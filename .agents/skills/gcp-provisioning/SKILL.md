---
name: gcp-provisioning
description: Provisioning GCP test projects, enabling APIs, and disabling org policies.
---

# Skill: GCP Provisioning

This skill provides instructions and scripts for provisioning Google Cloud projects, linking billing, enabling APIs, and disabling organization policies that might interfere with codelab testing.

## Prerequisites

You need a `gcp_config.txt` file sitting directly in the repository root directory (`./gcp_config.txt`).
Copy the template from `resources/gcp_config.txt.template` and fill in your details:

```text
folder_id=YOUR_FOLDER_ID
billing_account=YOUR_BILLING_ACCOUNT_ID
```

## Creating a Project

Use the provided Python script to create a project, link billing, and enable standard APIs:

```bash
python3 .agents/skills/gcp-provisioning/scripts/create_project.py <lab_name> [round_number]
```

**What it does:**
- Generates a unique project ID based on `lab_name` and `round_number` (or timestamp).
- Creates the project in the folder specified in `gcp_config.txt`.
- Links the project to the billing account specified in `gcp_config.txt` (with retries).
- Enables standard APIs: Compute, Network Connectivity, Logging, Artifact Registry, Pub/Sub.

## Disabling Org Policies

If your organization has strict policies that prevent deploying certain resources (like external IPs or unshielded VMs), use the provided shell script to disable them for your test project:

```bash
bash .agents/skills/gcp-provisioning/scripts/disable_org_policies.sh PROJECT_ID
```

**What it does:**
- Disables common boolean constraints (e.g., `requireShieldedVm`, `disableServiceAccountKeyCreation`).
- Sets list policies to `ALLOW` all values (e.g., `vmExternalIpAccess`).

## Manual Fallbacks

If the scripts fail or you don't have permission to use them, fall back to manual `gcloud` commands as described in the lighter version of this skill:

- `gcloud projects create ...`
- `gcloud services enable ...`
