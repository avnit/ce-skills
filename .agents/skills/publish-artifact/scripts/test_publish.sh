#!/bin/bash
# Deterministic test script for publish-artifact skill.

set -e

echo "Running deterministic test for publish-artifact skill..."

# 1. Setup mock remote
TEST_DIR=$(mktemp -d)
MOCK_REMOTE="$TEST_DIR/mock_remote.git"
mkdir -p "$MOCK_REMOTE"
git init --bare "$MOCK_REMOTE" > /dev/null

# 2. Setup initial commit in mock remote
CLONE_DIR="$TEST_DIR/initial_clone"
git clone "$MOCK_REMOTE" "$CLONE_DIR" 2>/dev/null
cd "$CLONE_DIR"
echo "# Initial" > README.md
git add README.md
git commit -m "Initial commit" > /dev/null
git branch -M main
git push origin main > /dev/null
cd - > /dev/null

# 3. Create a dummy artifact
DUMMY_FILE="$TEST_DIR/dummy_artifact.md"
echo "# Test Artifact" > "$DUMMY_FILE"

# 4. Override URL and run publish script
export CE_ARTIFACTS_REPO_URL="file://$MOCK_REMOTE"
export USER="test_user"

SCRIPT_PATH=".agents/skills/publish-artifact/scripts/publish.sh"
# Allow running from anywhere inside the workspace
if [[ ! -f "$SCRIPT_PATH" ]]; then
    echo "Please run this script from the workspace root."
    rm -rf "$TEST_DIR"
    exit 1
fi

bash "$SCRIPT_PATH" -f "$DUMMY_FILE" -c "test_category" -s "test_subject"

# 5. Verify the push reached the mock remote
echo "Verifying published structure..."
VERIFY_DIR="$TEST_DIR/verify_clone"
git clone "$MOCK_REMOTE" "$VERIFY_DIR" 2>/dev/null
cd "$VERIFY_DIR"

EXPECTED_PATH="test_user/test_category/test_subject/dummy_artifact.md"
if [[ -f "$EXPECTED_PATH" ]]; then
    echo "✅ Test Passed: Artifact successfully published to the correct deterministic path: $EXPECTED_PATH"
    EXIT_CODE=0
else
    echo "❌ Test Failed: Artifact not found at expected path: $EXPECTED_PATH"
    echo "Files found:"
    find . -type f | grep -v ".git"
    EXIT_CODE=1
fi

# Cleanup
rm -rf "$TEST_DIR"
exit $EXIT_CODE
