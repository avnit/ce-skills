---
name: gcp-billing-reports
description: Connects to Google Cloud BigQuery detailed billing export to present dynamic, partitioned Month-To-Date cost breakdowns per Project, Service, and resource SKU.
---

# Skill: GCP Billing Export Reports

This skill allows you to query a GCP detailed billing export table in BigQuery, generate Month-to-Date (MTD) sandbox spend reviews, and connect them directly to Cost Control Deletion workflows.

## How to use

Use the provided script to search and retrieve billing reports:

```bash
python3 .agents/skills/gcp-billing-reports/scripts/get_billing_reports.py [options]
```

**What it does:**
*   **Workspace Configuration Parsing**: Automatically searches for `gcp_config.txt` in your workspace to extract the active `billing_account`.
*   **Dynamic Table Pointer**: Converts the billing account ID (e.g., `01C4AF-4A2D30-073483`) into the precise BigQuery billing resource table `billing-350700.billing.gcp_billing_export_resource_v1_01C4AF_4A2D30_073483` dynamically. (Can be overridden explicitly using a `billing_table=...` line in `gcp_config.txt`).
*   **Standard SQL Execution**: Queries BigQuery using subprocess arrays (`shell=False`) with fast partition-level filters.
*   **Neat Markdown Rendering**: Formats and outputs clean Markdown tables with `Project ID` as the primary column.
*   **Time-Travel Querying**: Supports querying historical prior months using a `--month YYYY-MM` parameter.

## CLI Parameters

*   `--report <project|service|sku|trend|all>`: (String, default `project`) The billing report type to compile. `all` aggregates all four reports in sequence.
*   `--month <YYYY-MM>`: (String, optional) Overrides current Month-To-Date to query a historical month.
*   `--output <table|json>`: (String, default `table`) Standard console layout.
*   `--save-artifact <file_path>`: (String) Saves the compiled Markdown report to a local file.

## ⚠️ Cost Control & Sandbox Deletion Workflows

One of the primary advantages of this billing skill is its close integration with the **`codelab-cleanup`** skill to immediately shut down leaked or expensive sandbox environments.

### Step 1: Spot Leaked Spend
Run the default billing report to audit MTD spend per project. Look at the **Project ID** (first column) to find forgotten projects incurring costs (e.g., projects costing $10+ that you are no longer using):

```text
### MTD Spend per GCP Project

| Project ID | Project Name | MTD Cost (USD) |
| :--- | :--- | :--- |
| pr4d2b55bbef594246 | Use of mongodb-atlas-self-serv | $16.000 |
| infra-host-project-464423 | infra-host-project | $4.407 |
```

### Step 2: Run Cleanup Skill
Copy the target `Project ID` directly from the Markdown table, and feed it straight to the **`codelab-cleanup`** tool to delete the project and halt further billing:

```bash
python3 .agents/skills/codelab-cleanup/scripts/cleanup_projects.py --delete infra-host-project-464423 --force
```

This simple 2-step operation guarantees active sandbox cost control and stops resource leakage in seconds!
