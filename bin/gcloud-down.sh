#!/usr/bin/env bash
#
# install_gcloud.sh - Robust installation of Google Cloud CLI (gcloud) on RHEL.
# Supports both System-wide (DNF/YUM) and User-level (tarball) installations.
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

# --- Help Usage ---
show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --system     Install system-wide via dnf/yum (requires sudo/root) [Default]"
    echo "  --user       Install for current user only in \$HOME/google-cloud-sdk (no sudo needed)"
    echo "  --help       Show this help message"
    echo ""
}

# --- System Detection ---
detect_arch() {
    local arch
    arch=$(uname -m)
    case "$arch" in
        x86_64)  echo "x86_64" ;;
        aarch64|arm64) echo "aarch64" ;;
        *)
            log_error "Unsupported architecture: $arch"
            exit 1
            ;;
    esac
}

detect_rhel_version() {
    local major_ver=""
    if [ -f /etc/os-release ]; then
        # Shell-source os-release to get VERSION_ID
        # shellcheck disable=SC1091
        . /etc/os-release
        major_ver=$(echo "${VERSION_ID:-}" | cut -d. -f1)
    elif [ -f /etc/redhat-release ]; then
        major_ver=$(sed -rn 's/.*release ([0-9]+).*/\1/p' /etc/redhat-release)
    fi
    
    if [ -z "$major_ver" ]; then
        log_warn "Could not determine RHEL major version. Defaulting repository setup to RHEL 9 compatible."
        echo "9"
    else
        echo "$major_ver"
    fi
}

# --- Installation Methods ---

install_system_wide() {
    log_info "Starting system-wide installation via package manager..."
    
    # Ensure user has root privileges
    if [ "$EUID" -ne 0 ]; then
        log_error "System-wide installation requires root or sudo. Please run as root or use sudo."
        log_info "Tip: You can use './install_gcloud.sh --user' to install without root privileges."
        exit 1
    fi

    local arch rhel_ver base_url gpg_key pkg_mgr
    arch=$(detect_arch)
    rhel_ver=$(detect_rhel_version)
    
    # 1. Determine Repository Base URL and GPG Key based on RHEL version
    # RHEL 10 uses distinct GPG keys and el10 paths; RHEL 7, 8, 9 use el9 compatible repositories
    if [ "$rhel_ver" -ge 10 ]; then
        base_url="https://packages.cloud.google.com/yum/repos/cloud-sdk-el10-${arch}"
        gpg_key="https://packages.cloud.google.com/yum/doc/rpm-package-key-v10.gpg"
    else
        base_url="https://packages.cloud.google.com/yum/repos/cloud-sdk-el9-${arch}"
        gpg_key="https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg"
    fi

    # 2. Add Google Cloud CLI repository configuration
    log_info "Configuring gcloud DNF/YUM repository..."
    tee /etc/yum.repos.d/google-cloud-sdk.repo << EOM
[google-cloud-cli]
name=Google Cloud CLI
baseurl=${base_url}
enabled=1
gpgcheck=1
repo_gpgcheck=0
gpgkey=${gpg_key}
EOM

    # 3. Detect Package Manager (dnf vs yum)
    if command -v dnf &>/dev/null; then
        pkg_mgr="dnf"
    elif command -v yum &>/dev/null; then
        pkg_mgr="yum"
    else
        log_error "No supported package manager (dnf/yum) found!"
        exit 1
    fi

    # 4. Install pre-requisites and CLI
    log_info "Installing dependencies and google-cloud-cli..."
    if [ "$rhel_ver" -ge 8 ]; then
        # Newer RHEL distributions require libxcrypt-compat for compatibility
        $pkg_mgr install -y libxcrypt-compat.x86_64 || log_warn "libxcrypt-compat package not found or already satisfied."
    fi

    $pkg_mgr install -y google-cloud-cli

    log_success "Google Cloud CLI system-wide installation completed successfully!"
}

install_user_level() {
    log_info "Starting user-level installation via official archive..."
    
    local arch tarball_arch download_url target_dir tmp_dir
    arch=$(detect_arch)
    target_dir="$HOME/google-cloud-sdk"
    
    # Handle the architecture naming difference in standalone archives
    if [ "$arch" = "aarch64" ]; then
        tarball_arch="arm"
    else
        tarball_arch="x86_64"
    fi

    download_url="https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-${tarball_arch}.tar.gz"
    
    if [ -d "$target_dir" ]; then
        log_warn "Destination directory '$target_dir' already exists."
        read -rp "Do you want to overwrite it? (y/N): " confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            log_info "Installation cancelled."
            exit 0
        fi
        log_info "Removing existing installation directory..."
        rm -rf "$target_dir"
    fi

    # 1. Download and extract
    tmp_dir=$(mktemp -d)
    trap 'rm -rf "$tmp_dir"' EXIT

    log_info "Downloading gcloud CLI archive..."
    curl -L "$download_url" -o "$tmp_dir/gcloud.tar.gz"

    log_info "Extracting archive to your home directory..."
    tar -xzf "$tmp_dir/gcloud.tar.gz" -C "$HOME"

    # 2. Run official interactive installation script silently
    # --quiet: run non-interactively
    # --path-update=true: append shell rc files to add gcloud to $PATH
    # --command-completion=true: enable tab-completion
    log_info "Running the installation script..."
    "$target_dir/install.sh" --quiet --path-update=true --command-completion=true

    log_success "Google Cloud CLI user-level installation completed successfully!"
    log_info "Please restart your terminal session or run: source ~/.bashrc (or your shell profile) to update your path."
}

# --- Main Entry Point ---
main() {
    local mode="system"

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --system)
                mode="system"
                shift
                ;;
            --user)
                mode="user"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Run selected installation
    if [ "$mode" = "system" ]; then
        # Default to system if root, else warning/prompt
        install_system_wide
    else
        install_user_level
    fi

    # Post-install verification helper
    echo ""
    log_info "Verifying gcloud CLI installation..."
    export PATH="$PATH:/usr/bin:/usr/local/bin:$HOME/google-cloud-sdk/bin"
    if command -v gcloud &>/dev/null; then
        log_success "gcloud version info:"
        gcloud --version
        echo ""
        log_success "Setup complete! Run 'gcloud init' to authenticate your account and configure defaults."
        gcloud auth application-default login --login-config=auth.json --project tf-ai-host-project-tf-state --output=$HOME/.config/g
cloud/application_default_credentials.json
    else
        log_warn "Installation succeeded, but 'gcloud' is not immediately accessible in this shell's PATH."
        log_warn "Please open a new terminal session or manually run: source ~/.bashrc"
    fi
}

main "$@"
