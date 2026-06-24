---
trigger: always_on
description: Enforces pre-flight Google Cloud active account identity and Application Default Credentials (ADC) verification before executing any GCP-facing commands or workflows.
---

# Google Cloud Active Identity & ADC Validation Standard

Before executing any workflow run, deploying workloads, provisioning resources, or running scripts that communicate with Google Cloud APIs, you **MUST** verify the active authentication environment to prevent credentials misalignment or permission blocks.

## Verification Requirements

1. **Interactive Authentication Verification (Pre-Flight Gate)**:
   - Prior to executing any GCP command, running a deployment script, or initiating a validation workflow, you **MUST** consult and execute the workspace-level skill: [.agents/skills/gcloud-auth-verification/SKILL.md](file:///.agents/skills/gcloud-auth-verification/SKILL.md).
   - Run `python3 .agents/skills/gcloud-auth-verification/scripts/verify_auth.py` to retrieve the active and credentialed accounts.

2. **Mandatory ask_question Modal**:
   - You **MUST** present the active credentialed account options to the user using the **`ask_question`** tool.
   - Populate the modal choices dynamically (Keep active, Switch to existing accounts, Authenticate new account, Configure ADC).
   - If the user selects a different existing account, you **MUST** proactively execute `gcloud config set account <ACCOUNT>` on their behalf before running the workflow.

3. **Application Default Credentials (ADC) Check**:
   - If executing Python libraries, terraform, or background runner scripts, ensure Application Default Credentials (ADC) are properly aligned.
   - If there are quota project or auth mismatches, instruct the user to run:
     ```bash
     gcloud auth application-default login
     gcloud auth application-default set-quota-project PROJECT_ID
     ```

4. **IAM Permission Verification**:
   - If a command fails with a `403 PERMISSION_DENIED` error, verify if the issue is related to missing IAM permissions for the active account on that specific project, rather than a complete authentication failure. Proceed with the `gcloud-auth-verification` skill instructions.
