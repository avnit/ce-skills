#!/usr/bin/env bash
#
# agy.sh - Authenticate Antigravity (AGY) via gcloud Application Default Credentials (ADC)
#          backed by a Google Cloud Workforce Identity Pool login configuration (auth.json),
#          then launch the Antigravity CLI (agy).
#

set -euo pipefail

# --- Color Helpers for Logging ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# --- Configuration Defaults ---
LOGIN_CONFIG="${LOGIN_CONFIG:-auth.json}"
WORKFORCE_POOL_ID="${WORKFORCE_POOL_ID:-XXXXXX}"
WORKFORCE_PROVIDER_ID="${WORKFORCE_PROVIDER_ID:-YYYYYY}"
PROJECT_ID="${PROJECT_ID:-}"
TEMP_DIR="${TEMP_DIR:-}"
SKIP_LOGIN=false
AGY_ARGS=()

show_help() {
    cat <<EOF
Usage: $0 [options] [-- <agy_args>...]

Authenticates Antigravity through gcloud Application Default Credentials (ADC)
backed by a Workforce Identity Pool login configuration (auth.json) and launches agy.

Options:
  --pool-id <ID>         Workforce Pool ID (replaces XXXXXX in auth.json)
  --provider-id <ID>     Workforce Provider ID (replaces YYYYYY in auth.json)
  --project <PROJECT_ID> Target Google Cloud Project ID for ADC login
  --login-config <FILE>  Path to login config file (default: auth.json)
  --temp-dir <TEMP_DIR>  Optional <TEMP_DIR> name under /tmp/<TEMP_DIR> for Step 2c copy
  --skip-login           Skip gcloud login if ADC is already configured and launch agy
  -h, --help             Show this help message

Environment Variables:
  WORKFORCE_POOL_ID      Workforce Pool ID
  WORKFORCE_PROVIDER_ID  Workforce Provider ID
  PROJECT_ID             Google Cloud Project ID
  LOGIN_CONFIG           Path to auth.json (default: auth.json)
EOF
}

# --- Parse Command-Line Arguments ---
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --pool-id)
                WORKFORCE_POOL_ID="$2"
                shift 2
                ;;
            --provider-id)
                WORKFORCE_PROVIDER_ID="$2"
                shift 2
                ;;
            --project)
                PROJECT_ID="$2"
                shift 2
                ;;
            --login-config)
                LOGIN_CONFIG="$2"
                shift 2
                ;;
            --temp-dir)
                TEMP_DIR="$2"
                shift 2
                ;;
            --skip-login)
                SKIP_LOGIN=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            --)
                shift
                AGY_ARGS+=("$@")
                break
                ;;
            *)
                AGY_ARGS+=("$1")
                shift
                ;;
        esac
    done
}

# --- Step 1: Create or Validate Login Configuration File (auth.json) ---
setup_login_config() {
    log_info "Step 1: Preparing Workforce Identity Pool login configuration ($LOGIN_CONFIG)..."

    # Write auth.json if it doesn't exist or if pool/provider IDs were explicitly provided
    if [[ ! -f "$LOGIN_CONFIG" ]] || [[ "$WORKFORCE_POOL_ID" != "XXXXXX" ]] || [[ "$WORKFORCE_PROVIDER_ID" != "YYYYYY" ]]; then
        if [[ -f "$LOGIN_CONFIG" ]]; then
            # Preserve existing pool/provider if only one was overridden
            local existing_aud
            existing_aud=$(grep -o '"audience":[[:space:]]*"[^"]*"' "$LOGIN_CONFIG" || true)
            if [[ "$WORKFORCE_POOL_ID" == "XXXXXX" && "$existing_aud" =~ workforcePools/([^/]+)/providers/ ]]; then
                WORKFORCE_POOL_ID="${BASH_REMATCH[1]}"
            fi
            if [[ "$WORKFORCE_PROVIDER_ID" == "YYYYYY" && "$existing_aud" =~ providers/([^/\"]+) ]]; then
                WORKFORCE_PROVIDER_ID="${BASH_REMATCH[1]}"
            fi
        fi

        cat > "$LOGIN_CONFIG" <<EOF
{
  "universe_domain": "googleapis.com",
  "universe_cloud_web_domain": "cloud.google",
  "type": "external_account_authorized_user_login_config",
  "audience": "//iam.googleapis.com/locations/global/workforcePools/${WORKFORCE_POOL_ID}/providers/${WORKFORCE_PROVIDER_ID}",
  "auth_url": "https://auth.cloud.google/authorize",
  "token_url": "https://sts.googleapis.com/v1/oauthtoken",
  "token_info_url": "https://sts.googleapis.com/v1/introspect"
}
EOF
        log_info "Created login configuration file: $LOGIN_CONFIG"
    fi

    # Prompt interactively if placeholders XXXXXX or YYYYYY are still present
    if grep -q "XXXXXX" "$LOGIN_CONFIG" && [[ -t 0 ]]; then
        read -rp "Enter your Workforce Pool ID (replaces XXXXXX): " input_pool
        if [[ -n "$input_pool" ]]; then
            WORKFORCE_POOL_ID="$input_pool"
        fi
    fi

    if grep -q "YYYYYY" "$LOGIN_CONFIG" && [[ -t 0 ]]; then
        read -rp "Enter your Workforce Provider ID (replaces YYYYYY): " input_provider
        if [[ -n "$input_provider" ]]; then
            WORKFORCE_PROVIDER_ID="$input_provider"
        fi
    fi

    if [[ "$WORKFORCE_POOL_ID" != "XXXXXX" || "$WORKFORCE_PROVIDER_ID" != "YYYYYY" ]]; then
        cat > "$LOGIN_CONFIG" <<EOF
{
  "universe_domain": "googleapis.com",
  "universe_cloud_web_domain": "cloud.google",
  "type": "external_account_authorized_user_login_config",
  "audience": "//iam.googleapis.com/locations/global/workforcePools/${WORKFORCE_POOL_ID}/providers/${WORKFORCE_PROVIDER_ID}",
  "auth_url": "https://auth.cloud.google/authorize",
  "token_url": "https://sts.googleapis.com/v1/oauthtoken",
  "token_info_url": "https://sts.googleapis.com/v1/introspect"
}
EOF
    fi

    if grep -Eq "XXXXXX|YYYYYY" "$LOGIN_CONFIG"; then
        log_error "$LOGIN_CONFIG still contains placeholder values (XXXXXX or YYYYYY)."
        log_error "Pass --pool-id <POOL_ID> and --provider-id <PROVIDER_ID>, or edit $LOGIN_CONFIG directly."
        exit 1
    fi

    log_success "Login configuration ready at $LOGIN_CONFIG"
}

# --- Step 0: Network Preflight (STS reachability) ---
# gcloud (code exchange) and agy (token refresh) both call sts.googleapis.com.
# Fail fast with a clear layer-specific error instead of a urllib3 retry trace.
preflight_network() {
    local host="sts.googleapis.com"
    local code

    log_info "Step 0: Checking reachability of https://${host}..."

    if ! command -v curl &>/dev/null; then
        log_warn "curl not found; skipping network preflight."
        return 0
    fi

    if ! getent ahosts "$host" >/dev/null 2>&1; then
        log_error "DNS: cannot resolve ${host}."
        log_error "Check /etc/resolv.conf or your Private Google Access DNS zone (*.googleapis.com)."
        exit 1
    fi

    code=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 10 \
        "https://${host}/v1/introspect" || true)

    if [[ -z "$code" || "$code" == "000" ]]; then
        log_error "Cannot reach ${host}:443 (timeout / TLS / proxy)."
        log_error "HTTPS_PROXY='${HTTPS_PROXY:-${https_proxy:-<unset>}}'"
        log_error "Debug: curl -v https://${host}/v1/introspect"
        log_error "If behind a proxy: gcloud config set proxy/type http; proxy/address <host>; proxy/port <port>"
        log_error "If TLS inspection: gcloud config set core/custom_ca_certs_file <corp-ca.pem>"
        exit 1
    fi

    log_success "${host} reachable (HTTP ${code})"
}

# --- Step 2: Generate Application Default Credentials ---
generate_adc() {
    if [[ "$SKIP_LOGIN" == "true" ]]; then
        log_info "Skipping gcloud ADC login (--skip-login specified)."
        return 0
    fi

    if ! command -v gcloud &>/dev/null; then
        export PATH="$HOME/google-cloud-sdk/bin:$PATH:/usr/bin:/usr/local/bin"
    fi
    if ! command -v gcloud &>/dev/null; then
        log_error "'gcloud' CLI is not installed or not in PATH."
        exit 1
    fi

    # Resolve PROJECT_ID if not set
    if [[ -z "$PROJECT_ID" ]]; then
        PROJECT_ID=$(gcloud config get-value project 2>/dev/null || true)
        if [[ "$PROJECT_ID" == "(unset)" ]]; then
            PROJECT_ID=""
        fi
    fi

    if [[ -z "$PROJECT_ID" && -t 0 ]]; then
        read -rp "Enter your target Google Cloud Project ID (<PROJECT_ID>): " PROJECT_ID
    fi

    if [[ -z "$PROJECT_ID" ]]; then
        log_error "Target Google Cloud Project ID is required. Use --project <PROJECT_ID> or set PROJECT_ID."
        exit 1
    fi

    log_info "Step 2: Generating Application Default Credentials for project '$PROJECT_ID'..."
    echo ""
    log_info "Step 2a (Authenticate with Okta):"
    echo "  1. Open the sign-in URL printed below in your browser (Google Chrome recommended)."
    echo "  2. Sign in on your Okta sign-in page with your corporate credentials and complete MFA."
    log_info "Step 2b (Paste the Authorization Code into the CLI):"
    echo "  3. Copy the authorization code from the Google Cloud confirmation page,"
    echo "     paste it at the prompt below, and press Enter."
    echo ""

    gcloud auth application-default login --login-config="$LOGIN_CONFIG" --project="$PROJECT_ID"

    # --- Step 2c: Copy the Credentials to the Default ADC Location ---
    local default_adc_dir="$HOME/.config/gcloud"
    local default_adc_file="$default_adc_dir/application_default_credentials.json"
    mkdir -p "$default_adc_dir"

    local source_adc=""
    if [[ -n "$TEMP_DIR" && -f "/tmp/$TEMP_DIR/application_default_credentials.json" ]]; then
        source_adc="/tmp/$TEMP_DIR/application_default_credentials.json"
    elif [[ -n "${CLOUDSDK_CONFIG:-}" && -f "$CLOUDSDK_CONFIG/application_default_credentials.json" ]]; then
        source_adc="$CLOUDSDK_CONFIG/application_default_credentials.json"
    fi
    # NOTE: no blind `find /tmp` fallback. /tmp is world-writable; picking up the
    # first ADC file found could import another user's, a stale, or a planted
    # credential. Pass --temp-dir explicitly if gcloud wrote ADC under /tmp.

    # Refuse to import an ADC file not owned by the current user.
    if [[ -n "$source_adc" && ! -O "$source_adc" ]]; then
        log_error "Refusing to import $source_adc: not owned by $(id -un)."
        exit 1
    fi

    if [[ -n "$source_adc" && "$source_adc" != "$default_adc_file" ]]; then
        log_info "Step 2c: Copying credentials from $source_adc to $default_adc_file..."
        cp "$source_adc" "$default_adc_file"
        chmod 600 "$default_adc_file"
        log_success "Copied ADC credentials to $default_adc_file"
    elif [[ -f "$default_adc_file" ]]; then
        chmod 600 "$default_adc_file"
        log_success "Step 2c: ADC credentials verified at $default_adc_file"
    else
        log_warn "ADC file was not automatically found at $default_adc_file."
        if [[ -t 0 ]]; then
            read -rp "If gcloud saved credentials to /tmp/<TEMP_DIR>/application_default_credentials.json, enter <TEMP_DIR> (or full path): " user_temp
            if [[ -n "$user_temp" ]]; then
                if [[ -f "$user_temp" && -O "$user_temp" ]]; then
                    cp "$user_temp" "$default_adc_file"
                elif [[ -f "/tmp/$user_temp/application_default_credentials.json" && -O "/tmp/$user_temp/application_default_credentials.json" ]]; then
                    cp "/tmp/$user_temp/application_default_credentials.json" "$default_adc_file"
                else
                    log_error "Could not find credentials file at '$user_temp' or '/tmp/$user_temp/application_default_credentials.json'."
                    exit 1
                fi
                chmod 600 "$default_adc_file"
                log_success "Copied ADC credentials to $default_adc_file"
            fi
        fi
    fi
}

# --- Step 3 & Step 4: Enable ADC Auth and Launch Antigravity ---
launch_agy() {
    log_info "Step 3: Enabling ADC Authentication for Antigravity..."
    # Unset GOOGLE_APPLICATION_CREDENTIALS so ADC uses ~/.config/gcloud/application_default_credentials.json
    unset GOOGLE_APPLICATION_CREDENTIALS || true
    export AGY_ADC_AUTH=true
    log_success "Exported AGY_ADC_AUTH=true"

    # agy refreshes tokens against sts.googleapis.com itself and may not read
    # gcloud's proxy config. Propagate gcloud proxy settings to env if unset.
    if [[ -z "${HTTPS_PROXY:-${https_proxy:-}}" ]] && command -v gcloud &>/dev/null; then
        local p_addr p_port
        p_addr=$(gcloud config get-value proxy/address 2>/dev/null || true)
        p_port=$(gcloud config get-value proxy/port 2>/dev/null || true)
        if [[ -n "$p_addr" && "$p_addr" != "(unset)" && -n "$p_port" && "$p_port" != "(unset)" ]]; then
            export HTTPS_PROXY="http://${p_addr}:${p_port}"
            export NO_PROXY="${NO_PROXY:-localhost,127.0.0.1,metadata.google.internal}"
            log_info "Exported HTTPS_PROXY from gcloud config for agy."
        fi
    fi

    export PATH="$HOME/.local/bin:$PATH"
    if ! command -v agy &>/dev/null; then
        log_error "'agy' CLI not found in PATH. Please ensure Antigravity CLI is installed."
        exit 1
    fi

    log_info "Step 4: Launching Antigravity CLI (agy)..."
    if [[ ${#AGY_ARGS[@]} -gt 0 ]]; then
        exec agy "${AGY_ARGS[@]}"
    else
        exec agy
    fi
}

main() {
    parse_args "$@"
    setup_login_config
    preflight_network
    generate_adc
    launch_agy
}

main "$@"
