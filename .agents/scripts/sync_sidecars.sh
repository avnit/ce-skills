#!/bin/bash
# Sync sidecars wrapper executing sync_sidecars.py

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "${SCRIPT_DIR}/sync_sidecars.py"
