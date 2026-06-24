#!/bin/bash
# Script to publish an artifact to the ce-skills-artifacts repository via Pull Request.

set -e

# Default values
FILE_PATH=""
CATEGORY=""
SUBJECT=""

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -f|--file) FILE_PATH="$2"; shift ;;
        -c|--category) CATEGORY="$2"; shift ;;
        -s|--subject) SUBJECT="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [[ -z "$FILE_PATH" || -z "$CATEGORY" || -z "$SUBJECT" ]]; then
    echo "Usage: $0 -f <file_path> -c <category> -s <subject>"
    echo "Example: $0 -f demo/one-pager.md -c customers -s customer_x"
    exit 1
fi

if [[ ! -e "$FILE_PATH" ]]; then
    echo "Error: Path '$FILE_PATH' does not exist."
    exit 1
fi

# Configuration
ORG_REPO=${CE_ARTIFACTS_REPO_URL:-"cloud-gtm/ce-skills-artifacts"}
TEMP_DIR=$(mktemp -d)
USERNAME=${USER:-$(whoami)}
FILE_NAME=$(basename "$FILE_PATH")
TARGET_DIR="${USERNAME}/${CATEGORY}/${SUBJECT}"
BRANCH_NAME="add-artifact-${SUBJECT}-${USERNAME}-$(date +%s)"

echo "Preparing to publish '$FILE_PATH' to '$ORG_REPO' via Pull Request..."

# Keep track of absolute path to source file since we will change directory
if [[ "$FILE_PATH" = /* ]]; then
    ABS_FILE_PATH="$FILE_PATH"
else
    ABS_FILE_PATH="$PWD/$FILE_PATH"
fi

# --- LOCAL MOCK TEST MODE ---
# If running the automated TEST.md test script, we bypass GitHub CLI
if [[ "$ORG_REPO" == file://* ]]; then
    git clone "$ORG_REPO" "$TEMP_DIR"
    cd "$TEMP_DIR"
    mkdir -p "$TARGET_DIR"
    if [[ -d "$ABS_FILE_PATH" ]]; then
        cp -r "$ABS_FILE_PATH/"* "$TARGET_DIR/"
    else
        cp "$ABS_FILE_PATH" "$TARGET_DIR/"
    fi
    git add "$TARGET_DIR"
    git commit -m "Test commit"
    git push origin HEAD:main
    cd "$OLDPWD"
    rm -rf "$TEMP_DIR"
    echo "✅ Artifact successfully published to local mock remote!"
    exit 0
fi
# --- END TEST MODE ---

# Ensure GitHub CLI is installed and authenticated for production mode
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is required but not installed."
    echo "Please install it and run 'gh auth login' before using this skill."
    exit 1
fi

# Clone the main repository
gh repo clone "$ORG_REPO" "$TEMP_DIR"
cd "$TEMP_DIR"

# Create a new branch for this artifact
git checkout -b "$BRANCH_NAME"

# Create the target directory structure
mkdir -p "$TARGET_DIR"

# Copy the artifact
if [[ -d "$ABS_FILE_PATH" ]]; then
    cp -r "$ABS_FILE_PATH/"* "$TARGET_DIR/"
else
    cp "$ABS_FILE_PATH" "$TARGET_DIR/"
fi

# Git operations
git add "$TARGET_DIR"
git commit -m "Add artifacts for $SUBJECT in $CATEGORY"

# Push the branch directly to origin
echo "Pushing branch to origin..."
git push -u origin "$BRANCH_NAME"

# Create the Pull Request and capture the URL
echo "Creating Pull Request..."
PR_URL=$(gh pr create --title "Publish artifact: $FILE_NAME for $SUBJECT" \
             --body "Automated PR to publish artifact(s) for $SUBJECT in category $CATEGORY by $USERNAME." | tail -n 1)

# Cleanup
cd "$OLDPWD"
rm -rf "$TEMP_DIR"

echo "=========================================================="
echo "✅ Artifact successfully published! "
echo "🔗 PR Link: $PR_URL"
echo "=========================================================="
