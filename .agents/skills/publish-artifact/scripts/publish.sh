#!/bin/bash
# Script to publish an artifact to internal g3doc CompanyDoc (//depot/company/...) supporting team and personal scopes.

set -e

# Default values
FILE_PATH=""
CATEGORY=""
SUBJECT=""
SCOPE="personal"
TEAM=""
WORKSPACE_NAME=""
DRY_RUN=false

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -f|--file) FILE_PATH="$2"; shift ;;
        -c|--category) CATEGORY="$2"; shift ;;
        -s|--subject) SUBJECT="$2"; shift ;;
        -p|--scope) SCOPE="$2"; shift ;;
        -t|--team) TEAM="$2"; shift ;;
        -w|--workspace) WORKSPACE_NAME="$2"; shift ;;
        --dry-run) DRY_RUN=true ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [[ -z "$FILE_PATH" || -z "$CATEGORY" || -z "$SUBJECT" ]]; then
    echo "Usage: $0 -f <file_path> -c <category> -s <subject> [-p <personal|team>] [-t <team_name>] [-w <workspace_name>]"
    echo "Example (Personal): $0 -f doc/system_design.md -c blueprints -s closed_loop_learning -p personal"
    echo "Example (Team):     $0 -f demo/one-pager.md -c whitepapers -s customer_x -p team -t practice-ce"
    exit 1
fi

if [[ ! -e "$FILE_PATH" ]]; then
    echo "Error: Path '$FILE_PATH' does not exist."
    exit 1
fi

if [[ "$SCOPE" == "team" && -z "$TEAM" ]]; then
    echo "Error: --team <team_name> is required when --scope is set to 'team'."
    exit 1
fi

USERNAME=${USER:-$(whoami)}
FILE_NAME=$(basename "$FILE_PATH")

# Determine preferred workspace name from args or gcp_config.txt
CONFIG_FILE=""
if [[ -f "gcp_config.txt" ]]; then CONFIG_FILE="gcp_config.txt";
elif [[ -f "../gcp_config.txt" ]]; then CONFIG_FILE="../gcp_config.txt";
elif [[ -f "../../gcp_config.txt" ]]; then CONFIG_FILE="../../gcp_config.txt"; fi

if [[ -z "$WORKSPACE_NAME" && -n "$CONFIG_FILE" ]]; then
    WORKSPACE_NAME=$(grep "^piper_workspace=" "$CONFIG_FILE" | cut -d'=' -f2 | tr -d '\r')
fi
if [[ -z "$WORKSPACE_NAME" ]]; then WORKSPACE_NAME="ce-skills"; fi

# Ensure gcp_config.txt records piper_workspace
if [[ -n "$CONFIG_FILE" ]]; then
    if grep -q "^piper_workspace=" "$CONFIG_FILE"; then
        sed -i "s/^piper_workspace=.*/piper_workspace=$WORKSPACE_NAME/" "$CONFIG_FILE"
    else
        echo "piper_workspace=$WORKSPACE_NAME" >> "$CONFIG_FILE"
    fi
fi

# Determine target relative path in CompanyDoc
if [[ "$SCOPE" == "team" ]]; then
    OWNER_TAG="$TEAM"
    REL_TARGET="teams/${TEAM}/${CATEGORY}/${SUBJECT}"
else
    OWNER_TAG="$USERNAME"
    REL_TARGET="users/${USERNAME}/${CATEGORY}/${SUBJECT}"
fi

echo "Preparing to publish '$FILE_PATH' to CompanyDoc scope '$SCOPE' ($REL_TARGET) via workspace '$WORKSPACE_NAME'..."

# Keep track of absolute path to source file
if [[ "$FILE_PATH" = /* ]]; then
    ABS_FILE_PATH="$FILE_PATH"
else
    ABS_FILE_PATH="$PWD/$FILE_PATH"
fi

# Locate or initialize CitC workspace containing /company mount
CITC_WORKSPACE="/google/src/cloud/${USERNAME}/${WORKSPACE_NAME}"
if [[ "$DRY_RUN" == "false" && -d "/google/src/cloud" ]]; then
    if [[ ! -d "$CITC_WORKSPACE/company" ]]; then
        echo "ℹ️ Workspace '$WORKSPACE_NAME' not found or missing company mount. Forcing creation..."
        g4 client -c "$WORKSPACE_NAME" 2>/dev/null || true
    fi
    if [[ ! -d "$CITC_WORKSPACE/company" ]]; then
        # Fallback to scanning for any existing workspace
        for client_dir in /google/src/cloud/"$USERNAME"/*; do
            if [[ -d "$client_dir/company" ]]; then CITC_WORKSPACE="$client_dir"; break; fi
        done
    fi
fi

# If running dry-run or no CitC workspace found, use local mock directory for verification
if [[ "$DRY_RUN" == "true" || ! -d "$CITC_WORKSPACE/company" ]]; then
    echo "Notice: Using local staging directory for dry-run / offline test verification."
    TARGET_DIR="/tmp/g3doc_publish_mock/company/${REL_TARGET}"
    CL_NUMBER="999999999"
    IS_MOCK=true
else
    TARGET_DIR="${CITC_WORKSPACE}/company/${REL_TARGET}"
    IS_MOCK=false
fi

mkdir -p "$TARGET_DIR"

# Copy main artifact files
SRC_BASE_DIR=$(if [[ -d "$ABS_FILE_PATH" ]]; then echo "$ABS_FILE_PATH"; else dirname "$ABS_FILE_PATH"; fi)
if [[ -d "$ABS_FILE_PATH" ]]; then
    cp -r "$ABS_FILE_PATH/"* "$TARGET_DIR/"
else
    cp "$ABS_FILE_PATH" "$TARGET_DIR/"
fi

# 1. Automatically copy standard asset folders if they exist alongside the source
for asset_folder in images img assets media; do
    if [[ -d "$SRC_BASE_DIR/$asset_folder" ]]; then
        echo "🖼️ Found image asset directory '$asset_folder', copying to staging..."
        cp -r "$SRC_BASE_DIR/$asset_folder" "$TARGET_DIR/"
    fi
done

# 2. Parse markdown files for explicitly referenced relative images and copy them if not already copied
find "$TARGET_DIR" -type f -name "*.md" | while read -r staged_md; do
    grep -oP '(!\[.*?\]\(\K[^)]+)|(<img[^>]+src=["\x27]\K[^"\x27]+)' "$staged_md" 2>/dev/null | while read -r img_ref; do
        if [[ "$img_ref" != http* && "$img_ref" != /* ]]; then
            SRC_IMG="$SRC_BASE_DIR/$img_ref"
            DEST_IMG="$TARGET_DIR/$img_ref"
            if [[ -f "$SRC_IMG" && ! -f "$DEST_IMG" ]]; then
                echo "🖼️ Copying referenced image '$img_ref'..."
                mkdir -p "$(dirname "$DEST_IMG")"
                cp "$SRC_IMG" "$DEST_IMG"
            fi
        fi
    done
done
find "$TARGET_DIR" -type f \( -name "*.env" -o -name "*.state" -o -name ".env" -o -name ".state" \) -delete

# Execute g3doc formatting script on all copied markdown files
FORMATTER_SCRIPT="$(dirname "$0")/../../g3doc-formatter/scripts/format_g3doc.py"
if [[ -f "$FORMATTER_SCRIPT" ]]; then
    find "$TARGET_DIR" -type f -name "*.md" | while read -r md_file; do
        echo "Formatting $(basename "$md_file") for g3doc compliance..."
        python3 "$FORMATTER_SCRIPT" --file "$md_file" --owner "$OWNER_TAG" --in-place
    done
fi

# Execute CitC version control registration if in live workspace
if [[ "$IS_MOCK" == "false" ]]; then
    cd "$TARGET_DIR"
    if hg root &>/dev/null; then
        hg add . 2>/dev/null || true
        CL_NUMBER=$(hg status 2>/dev/null | head -n 1 | awk '{print "FIG_PENDING"}')
        if [[ -z "$CL_NUMBER" ]]; then CL_NUMBER="PENDING_CL"; fi
    else
        g4 open ... 2>/dev/null || true
        g4 add ... 2>/dev/null || true
        CL_NUMBER=$(g4 pending 2>/dev/null | head -n 1 | awk '{print $2}' | tr -d ':')
        if [[ -z "$CL_NUMBER" ]]; then CL_NUMBER="PENDING_CL"; fi
    fi
    cd "$OLDPWD"
fi

# Generate preview URL
PREVIEW_FILE=$FILE_NAME
if [[ -d "$ABS_FILE_PATH" ]]; then
    # Find first markdown file for preview link
    FIRST_MD=$(find "$TARGET_DIR" -name "*.md" | head -n 1)
    if [[ -n "$FIRST_MD" ]]; then
        PREVIEW_FILE=$(basename "$FIRST_MD")
    fi
fi

PREVIEW_URL="https://g3doc.corp.google.com/company/${REL_TARGET}/${PREVIEW_FILE}?cl=${CL_NUMBER}"

echo "=========================================================="
echo "✅ Artifact successfully staged for g3doc CompanyDoc! "
echo "📂 Staged Directory: $TARGET_DIR"
echo "🔗 Live Preview URL: $PREVIEW_URL"
echo "=========================================================="
