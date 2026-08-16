---
description: Orchestrate the automated generation of Month-To-Date (MTD) Google Cloud billing reports and cost reviews using BigQuery.
---

# Workflow: Review GCP Month-To-Date Billing Report

This workflow guides you through compiling and reviewing your Month-to-Date (MTD) GCP Sandbox spend report to identify high-cost resources, detect leakages, and execute sandbox cleanup steps.

## Operational Workflow

### Phase 0: Pre-Flight Authentication Verification

1. Consult and enforce the global auth validation standard: [gcloud_auth.md](../rules/gcloud_auth.md).
2. Execute the **gcloud-auth-verification** skill (`python3 .agents/skills/gcloud-auth-verification/scripts/verify_auth.py`).
3. If active account matches target environment (with BigQuery read access over Argolis resources, e.g. primary sandbox admin or corporate employee account), log active identity and proceed automatically.
4. If an account switch or user decision is required, invoke the `ask_question` tool modal to let the user select or confirm the active account.

### Phase 1: Run Billing Report

1.  Prompt the user to select the type of billing report they wish to compile:
    - **`project` (Default)**: Shows MTD spend broken down by GCP Project. (Most useful for spotting resource leakage).
    - **`service`**: Shows MTD spend broken down by GCP Service (Compute Engine, Cloud SQL, etc.).
    - **`sku`**: Shows MTD spend broken down by specific resource SKU.
    - **`trend`**: Shows spend trends over time.
    - **`all`**: Compiles all breakdown reports in sequence.
2.  Execute the billing reports script, passing their chosen parameters and saving the compiled report to the active Jetski conversation artifacts directory:
    ```bash
    python3 .agents/skills/gcp-billing-reports/scripts/get_billing_reports.py --report <REPORT_TYPE> --save-artifact <appDataDir>/brain/<conversation-id>/billing_report.md
    ```
3.  Display the rendered Markdown tables from the report cleanly in the chat to present the cost review.

### Phase 2: Cost Control Cleanup Actions

1.  Scan the generated Project MTD Cost table for any unused or high-cost sandbox projects (e.g. projects costing $10+ that are no longer active).
2.  If any are identified, ask the user if they would like to execute the **`codelab-cleanup`** workflow to delete the project and immediately halt further billing:
    ```bash
    python3 .agents/skills/codelab-cleanup/scripts/cleanup_projects.py --delete <PROJECT_ID> --force
    ```

### Phase 3: Email Report Delivery (Interactive)

1.  Invoke the `ask_question` tool to prompt the user if they would like to email the compiled billing report to themselves or colleagues:
    - **Question**: "Would you like to email this beautifully compiled MTD Billing Report as an HTML card?"
    - **Options**:
      - "Yes, send to my corporate email (<user-corporate-email>)"
      - "Yes, send to custom email addresses..."
      - "No, skip email delivery"
2.  If the user selects "Yes, send to my corporate email" (or custom emails):
    - Connect to the `gcloud-auth-verification` skill to verify/switch the active account to their corporate `<user-corporate-email>` identity (required for using internal `gmail` CLI).
    - Execute the email delivery script:
      ```bash
      python3 .agents/skills/send-email/scripts/send_email.py --to "<user-email>" --subject "Month-To-Date GCP Spend Review" --body "<report_artifact_path>" --html
      ```
    - Present a confirmation message with the target recipient details.
