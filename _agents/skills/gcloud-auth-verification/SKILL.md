---
name: gcloud-auth-verification
description: Workspace-level skill to check active gcloud credentials and interactively switch active accounts or configure ADC using ask_question tool.
---

# Skill: Google Cloud Active Auth & ADC Verification

This skill provides instructions and scripts to inspect, present, and interactively switch active Google Cloud authenticated accounts and Application Default Credentials (ADC).

## Operational Workflow

Follow this step-by-step interactive protocol before starting any deployment or validation workflow:

### 1. Check Credentialed Accounts
Execute the helper script to retrieve a structured JSON of active and other accounts:
```bash
python3 _agents/skills/gcloud-auth-verification/scripts/verify_auth.py
```

Expected output:
```json
{
  "active_account": "active-user@domain.com",
  "other_accounts": [
    "other-user@domain.com"
  ]
}
```

### 2. Present Interactive Ask Question Modal
Invoke the `ask_question` tool to present a multiple-choice selection modal to the user. Dynamically populate the active account and other options from the JSON output:

*   `question`: "Confirm active Google Cloud credentialed account for this run:"
*   `options`:
    *   `"(Recommended) Keep currently active account: {active_account}"`
    *   For each account in `other_accounts` (if any): `"Switch to existing account: {account}"`
    *   `"Authenticate a new account (gcloud auth login)"`
    *   `"Configure Application Default Credentials (ADC) & Quota Project"`
*   `is_multi_select`: `false`

### 3. Process Selection and Take Corrective Action

Based on the user's response:

*   **Selection: Keep currently active account**
    - Proceed immediately with your scheduled workflow.
    
*   **Selection: Switch to existing account**
    - Extract the target account name from the option.
    - Run the command to set the active account:
      ```bash
      gcloud config set account <ACCOUNT>
      ```
    - Verify success by re-running the check script and proceed.

*   **Selection: Authenticate a new account**
    - Pause execution.
    - Instruct the user to execute these authentication commands in their terminal:
      ```bash
      gcloud auth login
      gcloud auth application-default login
      ```
    - Wait for user confirmation and then re-verify.

*   **Selection: Configure Application Default Credentials (ADC)**
    - Identify the active test or deployment `PROJECT_ID`.
    - Instruct the user to align their Application Default Credentials (ADC) and quota projects:
      ```bash
      gcloud auth application-default login
      gcloud auth application-default set-quota-project <PROJECT_ID>
      ```

---

## Example Implementation Plan Integration

When planning deployment works, list this authentication check as the primary gate in your plan:
1. **Phase 0 (Pre-Flight Auth Check)**: Run `_agents/skills/gcloud-auth-verification/scripts/verify_auth.py` and present interactive `ask_question` selection.
