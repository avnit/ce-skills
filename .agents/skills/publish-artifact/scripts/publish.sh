#!/bin/bash
# Script to publish an artifact to internal g3doc CompanyDoc (//depot/company/...) supporting team and personal scopes.

set -e

# Default values
FILE_PATH=""
CATEGORY=""
SUBJECT=""
SCOPE="personal"
TEAM=""
DRY_RUN=false

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -f|--file) FILE_PATH="$2"; shift ;;
        -c|--category) CATEGORY="$2"; shift ;;
        -s|--subject) SUBJECT="$2"; shift ;;
        -p|--scope) SCOPE="$2"; shift ;;
        -t|--team) TEAM="$2"; shift ;;
        --dry-run) DRY_RUN=true ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [[ -z "$FILE_PATH" || -z "$CATEGORY" || -z "$SUBJECT" ]]; then
    echo "Usage: $0 -f <file_path> -c <category> -s <subject> [-p <personal|team>] [-t <team_name>]"
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

# Determine target relative path in CompanyDoc
if [[ "$SCOPE" == "team" ]]; then
    OWNER_TAG="$TEAM"
    REL_TARGET="teams/${TEAM}/${CATEGORY}/${SUBJECT}"
else
    OWNER_TAG="$USERNAME"
    REL_TARGET="users/${USERNAME}/${CATEGORY}/${SUBJECT}"
fi

echo "Preparing to publish '$FILE_PATH' to CompanyDoc scope '$SCOPE' ($REL_TARGET)..."

# Keep track of absolute path to source file
if [[ "$FILE_PATH" = /* ]]; then
    ABS_FILE_PATH="$FILE_PATH"
else
    ABS_FILE_PATH="$PWD/$FILE_PATH"
fi

# Locate CitC workspace containing /company mount
CITC_WORKSPACE=""
for client_dir in /google/src/cloud/"$USERNAME"/*; do
    if [[ -d "$client_dir/company" ]]; then
        CITC_WORKSPACE="$client_dir"
        break
    fi
done

# If running dry-run or no CitC workspace found, use local mock directory for verification
if [[ "$DRY_RUN" == "true" || -z "$CITC_WORKSPACE" ]]; then
    echo "Notice: Using local staging directory for dry-run / offline test verification."
    TARGET_DIR="/tmp/g3doc_publish_mock/company/${REL_TARGET}"
    CL_NUMBER="999999999"
    IS_MOCK=true
else
    TARGET_DIR="${CITC_WORKSPACE}/company/${REL_TARGET}"
    IS_MOCK=false
fi

mkdir -p "$TARGET_DIR"

# Copy files
if [[ -d "$ABS_FILE_PATH" ]]; then
    cp -r "$ABS_FILE_PATH/"* "$TARGET_DIR/"
else
    cp "$ABS_FILE_PATH" "$TARGET_DIR/"
fi
find "$TARGET_DIR" -type f \( -name "*.env" -o -name "*.state" -o -name ".env" -o -name ".state" \) -delete

# Inject g3doc metadata headers into markdown files if missing
TODAY=$(date +%Y-%m-%d)
find "$TARGET_DIR" -type f -name "*.md" | while read -r md_file; do
    if ! grep -q "<!--\* freshness:" "$md_file"; then
        echo "Injecting g3doc freshness tag into $(basename "$md_file")..."
        TEMP_MD=$(mktemp)
        # Extract title or default to filename
        FIRST_LINE=$(head -n 1 "$md_file")
        if [[ "$FIRST_LINE" == \#* ]]; then
            echo "$FIRST_LINE" > "$TEMP_MD"
            echo "" >> "$TEMP_MD"
            tail -n +2 "$md_file" > "${TEMP_MD}.body"
        else
            echo "# ${SUBJECT} (${FILE_NAME})" > "$TEMP_MD"
            echo "" >> "$TEMP_MD"
            cat "$md_file" > "${TEMP_MD}.body"
        fi
        
        cat <<EOF >> "$TEMP_MD"
<!--* freshness: { owner: '$OWNER_TAG' reviewed: '$TODAY' } *-->

[TOC]

EOF
        cat "${TEMP_MD}.body" >> "$TEMP_MD"
        mv "$TEMP_MD" "$md_file"
        rm -f "${TEMP_MD}.body"
    fi
done

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
