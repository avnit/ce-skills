---
description: Orchestrate the automated generation of Month-To-Date (MTD) Google Cloud billing reports and cost reviews using BigQuery.
---

# Workflow: Review GCP Month-To-Date Billing Report

This workflow guides you through compiling and reviewing your Month-to-Date (MTD) GCP Sandbox spend report to identify high-cost resources, detect leakages, and execute sandbox cleanup steps.

## Operational Workflow

### Phase 1: Identity & Credentials Verification
1.  **Active Account**: BigQuery billing export queries require access to the `billing-350700` billing project. Verify your active identity:
    ```bash
    python3 .agents/skills/gcloud-auth-verification/scripts/verify_auth.py
    ```
2.  The active account should be one with BigQuery read access over Argolis resources (e.g. your primary sandbox admin or corporate employee account).

### Phase 2: Run Billing Report
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

### Phase 3: Cost Control Cleanup Actions
1.  Scan the generated Project MTD Cost table for any unused or high-cost sandbox projects (e.g. projects costing $10+ that are no longer active).
2.  If any are identified, ask the user if they would like to execute the **`codelab-cleanup`** workflow to delete the project and immediately halt further billing:
    ```bash
    python3 .agents/skills/codelab-cleanup/scripts/cleanup_projects.py --delete <PROJECT_ID> --force
    ```

### Phase 4: Email Report Delivery (Interactive)
1.  Invoke the `ask_question` tool to prompt the user if they would like to email the compiled billing report to themselves or colleagues:
    - **Question**: "Would you like to email this beautifully compiled MTD Billing Report as an HTML card?"
    - **Options**:
      - "Yes, send to my corporate email (shacharb@google.com)"
      - "Yes, send to custom email addresses..."
      - "No, skip email delivery"
2.  If the user selects "Yes, send to my corporate email" (or custom emails):
    - Connect to the `gcloud-auth-verification` skill to verify/switch the active account to their corporate `shacharb@google.com` identity (required for using internal `gmail` CLI).
    - Execute the email delivery script:
      ```bash
      python3 .agents/skills/send-email/scripts/send_email.py --to "<user-email>" --subject "Month-To-Date GCP Spend Review" --body "<report_artifact_path>" --html
      ```
    - Present a confirmation message with the target recipient details.
