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

for POLICY in "${BOOLEAN_POLICIES[@]}"; do
  echo "Disabling Boolean Policy $POLICY..."
  gcloud resource-manager org-policies disable-enforce "constraints/$POLICY" --project="$PROJECT_ID" || echo "Warning: Failed to disable $POLICY"
done

for POLICY in "${LIST_POLICIES[@]}"; do
  echo "Enforcing ALLOW_ALL for List Policy $POLICY..."
  cat <<EOF > policy.yaml
constraint: constraints/$POLICY
listPolicy:
  allValues: ALLOW
EOF
  gcloud resource-manager org-policies set-policy policy.yaml --project="$PROJECT_ID" || echo "Warning: Failed to set policy for $POLICY"
  rm policy.yaml
done

echo "Waiting 60 seconds for policy propagation..."
sleep 60

echo "Org Policies disabled successfully."
