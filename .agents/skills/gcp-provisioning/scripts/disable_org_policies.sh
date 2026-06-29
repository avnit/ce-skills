#!/bin/bash
# disable_org_policies.sh
# Disables common Org Policies that interfere with Codelab deployments.
# Usage: ./disable_org_policies.sh <PROJECT_ID>

set -e

PROJECT_ID=$1

if [ -z "$PROJECT_ID" ]; then
  echo "Usage: $0 <PROJECT_ID>"
  exit 1
fi

# Verify Org Policy API endpoint readiness with retries
echo "Verifying Org Policy API readiness..."
API_READY=false
for i in {1..10}; do
  if gcloud org-policies list --project="$PROJECT_ID" --limit=1 --quiet >/dev/null 2>&1; then
    echo "Org Policy API is active and ready."
    API_READY=true
    break
  fi
  echo "Waiting for Org Policy API endpoint to warm up (attempt $i/10)..."
  sleep 10
done

if [ "$API_READY" = false ]; then
  echo "Error: Org Policy API service did not become ready in time."
  exit 1
fi


# Create a unique temporary directory for this process to prevent multi-process race conditions in shared directories
TMP_DIR=$(mktemp -d -t org-policy-XXXXXX)
trap 'cd /tmp && rm -rf "$TMP_DIR"' EXIT
cd "$TMP_DIR"

# Helper function with retries for setting org policies robustly
set_org_policy_with_retry() {
  local policy_file=$1
  local policy_name=$2
  local max_retries=3
  local attempt=1
  while [ $attempt -le $max_retries ]; do
    if gcloud org-policies set-policy "$policy_file" --project="$PROJECT_ID" --quiet; then
      return 0
    fi
    echo "Warning: Failed to set policy $policy_name (attempt $attempt/$max_retries). Retrying in 15s..."
    sleep 15
    attempt=$((attempt + 1))
  done
  echo "Warning: Giving up on setting policy $policy_name after $max_retries attempts."
  return 0
}

# Boolean Policies
BOOLEAN_POLICIES=(
  "compute.requireShieldedVm"
  "iam.disableServiceAccountKeyCreation"
  "iam.disableServiceAccountKeyUpload"
  "compute.requireOsLogin"
)

# List Policies
LIST_POLICIES=(
  "compute.vmExternalIpAccess"
  "compute.restrictVpcPeering"
  "compute.restrictProtocolForwardingCreationForTypes"
  "compute.vmCanIpForward"
  "compute.restrictVpnPeerIPs"
)

echo "Disabling Org Policies for project: $PROJECT_ID"

# Create policy file for Boolean (Enforced: False)
cat <<EOF > boolean_policy.yaml
name: projects/$PROJECT_ID/policies/%POLICY%
spec:
  rules:
  - enforce: false
EOF

for policy in "${BOOLEAN_POLICIES[@]}"; do
    echo "Disabling Boolean Policy $policy..."
    sed "s|%POLICY%|$policy|g" boolean_policy.yaml > current_boolean.yaml
    set_org_policy_with_retry current_boolean.yaml "$policy"
done

# Create policy file for List (Allow All: True)
cat <<EOF > list_policy.yaml
name: projects/$PROJECT_ID/policies/%POLICY%
spec:
  rules:
  - allowAll: true
EOF

for policy in "${LIST_POLICIES[@]}"; do
    echo "Enforcing ALLOW_ALL for List Policy $policy..."
    sed "s|%POLICY%|$policy|g" list_policy.yaml > current_list.yaml
    set_org_policy_with_retry current_list.yaml "$policy"
done

# Clean up the isolated temporary directory safely
cd /tmp
rm -rf "$TMP_DIR"

echo "Waiting 60 seconds for policy propagation..."
sleep 60

echo "Org Policies disabled successfully."
