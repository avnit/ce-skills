#!/bin/bash
# ==============================================================================
# Google Cloud Codelab Factory: Sidecar Onboarding Sync Tool
# ==============================================================================
# Copies all version-controlled sidecar configurations and scripts from the
# workspace template folder (.agents/sidecars/) into the hidden local active
# Jetski runtime directory (~/.gemini/jetski/sidecars/) for instant execution.

set -euo pipefail

# Define Paths
WORKSPACE_DIR="${HOME}/skynet"
TEMPLATE_DIR="${WORKSPACE_DIR}/.agents/sidecars"
JETSKI_DIR="${HOME}/.gemini/jetski"
RUNTIME_DIR="${JETSKI_DIR}/sidecars"


echo "====================================================="
echo "🚀 Initializing Sidecar Config Template Sync..."
echo "====================================================="

# Verify template directory exists
if [ ! -d "${TEMPLATE_DIR}" ]; then
    echo "❌ Error: Template directory ${TEMPLATE_DIR} does not exist."
    exit 1
fi

# Create runtime directory if missing
if [ ! -d "${RUNTIME_DIR}" ]; then
    echo "📂 Creating hidden runtime sidecars folder: ${RUNTIME_DIR}..."
    mkdir -p "${RUNTIME_DIR}"
fi

# Copy templates recursively
echo "🔄 Syncing config templates..."
cp -r "${TEMPLATE_DIR}"/* "${RUNTIME_DIR}/"

echo "====================================================="
echo "✅ Sidecars synced and onboarded successfully!"
echo "====================================================="
echo "The following background daemons are active and running:"
for dir in "${TEMPLATE_DIR}"/*; do
    if [ -d "${dir}" ]; then
        name=$(basename "${dir}")
        echo "  • ${name} (Linked dynamically at: ${RUNTIME_DIR}/${name}/)"
    fi
done
echo "====================================================="
