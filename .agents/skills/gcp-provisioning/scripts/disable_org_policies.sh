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
    gcloud org-policies set-policy current_boolean.yaml --project="$PROJECT_ID" || echo "Warning: Failed to disable $policy"
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
    gcloud org-policies set-policy current_list.yaml --project="$PROJECT_ID" || echo "Warning: Failed to set policy for $policy"
done

rm -f boolean_policy.yaml list_policy.yaml current_boolean.yaml current_list.yaml

echo "Waiting 60 seconds for policy propagation..."
sleep 60

echo "Org Policies disabled successfully."
