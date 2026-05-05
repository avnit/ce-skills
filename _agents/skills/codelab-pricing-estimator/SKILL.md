---
name: codelab-pricing-estimator
description: Audits and calculates the exact hourly cost of active provisioned resources in a deployed sandbox project using Cloud Asset Inventory.
---

# Skill: GCP Deployed Sandbox Pricing Auditor

This skill allows you to connect to a deployed Google Cloud sandbox project, discover all active provisioned resources in real time, and calculate a 100% deterministic hourly running cost based on the exact active configurations (machine types, GKE node pool sizes, persistent storage capacities, and database tiers).

## How to use

Use the provided script to audit a deployed sandbox project and extract structured resource data:

```bash
python3 _agents/skills/codelab-pricing-estimator/scripts/extract_and_estimate.py --project YOUR_PROJECT_ID [options]
```

**What it does:**
*   Discovers all active resources in the project by querying the **Google Cloud Asset Inventory API** (relying on `gcloud asset search-all-resources`).
*   Filters and isolates billable infrastructure categories (GCE VMs, persistent disks, GKE clusters, Cloud SQL instances).
*   Queries native GCP list APIs (Compute Engine, Container Engine, SQL Admin) to retrieve precise properties (active status, machine sizes, node counts, disk type, disk size).
*   Cross-references configurations with Google Cloud Catalog hourly metrics to calculate exact costs.
*   Outputs a beautiful, structured Markdown table of running costs.
*   Supports saving the audit report as a persistent local Markdown file.

## CLI Parameters

*   `--project <project_id>`: (String, Required) The target Google Cloud Project ID to audit.
*   `--save-report <file_path>`: (String) Saves the formatted Markdown pricing report to a local file (parent directories are auto-created).

## Output Format Example

Running `python3 extract_and_estimate.py --project "my-active-sandbox-99"` yields:

# Deployed Sandbox Pricing Audit Report

*   **Target GCP Project**: `my-active-sandbox-99`
*   **Deterministic Audit State**: Verified via Cloud Asset Inventory
*   **Hourly Running Cost**: $0.2345

## Active Billable Resources

| Resource Name | Resource Type | Status | Current Configuration | Hourly Cost |
| :--- | :--- | :--- | :--- | :--- |
| `sandbox-web-server` | Compute Instance | RUNNING | Machine: e2-standard-2 \| Zone: us-central1-a | $0.0670 |
| `sandbox-web-disk` | Persistent Disk | PROVISIONED | Size: 100 GB \| Type: pd-ssd | $0.0233 |
| `sandbox-db` | Cloud SQL Database | RUNNABLE | Tier: db-custom-2-7680 \| Region: us-central1 | $0.1226 |
| `gke-nodes` | GKE Cluster | STOPPED | Nodes: 3 x e2-medium \| Region: us-central1 | $0.0216 |

**Total Deployed Sandbox Cost**: $0.2345 / hour

## Audit Warnings & Disclaimers
> [!NOTE]
> This audit represents the exact hourly configuration charges currently running in your project. Volume-based usage (network egress, query scans) is excluded.
