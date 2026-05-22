---
name: gcp-pricing-estimator
description: >-
  Use when generating contract-accurate Google Cloud cost estimates directly from Terraform HCL configurations, architecture diagrams, or RFP documents. Invokes CWP.PricingService Stubby endpoints to calculate exact SKU math and automatically creates professional Google Sheets and Docs proposal summaries.
---

# Skill: GCP pre-Sales Pricing Estimator (v2)

This skill guides you through extracting infrastructure topologies, calculating real-time contract-specific GCP pricing natively via Stubby BNS channels, and generating professional pricing sheets and proposal summaries for customers.

---

## Core Workflow Steps

Copy this checklist and track progress:
- [ ] Step 1: Ingest source material (Terraform `.tf` files or RFP document)
- [ ] Step 2: Extract infrastructure topology (vCPUs, RAM, Storage tiers, Region)
- [ ] Step 3: Execute local `pricing_client.py` Stubby call to `CWP.PricingService`
- [ ] Step 4: Generate dynamic Google Sheet using `gsheets` CLI
- [ ] Step 5: Embed Executive Summary Table in Proposal Doc using `gdocs` CLI

---

## Operational Guide

### 📋 Step 1: Ingest Source Material & Extract Topology
Scan the active workspace directory for Terraform HCL files or read the customer RFP document. Identify key architectural components: Compute Engine instances (machine series, count, OS), GKE clusters, Cloud Run services, Spanner instances, Cloud Storage buckets (class, GBs), and BigQuery usage metrics. Save the JSON payload representing the extracted topology.

### 🧮 Step 2: Execute Pricing Calculation via Stubby
Invoke the local `pricing_client.py` script to connect to `CWP.PricingService` over BNS. Pass the extracted topology payload to calculate exact line-item SKU costs.

**Execution Command:**
```bash
python3 .agents/skills/gcp_pricing_estimator/scripts/pricing_client.py \
  --payload_path="/tmp/agent_artifacts/extracted_topology.json" \
  --output_path="/tmp/agent_artifacts/calculated_estimate.json"
```

*Note: Ensure your Cloudtop environment has active LOAS credentials (`prodaccess`) and has completed the Borg service account linkage (`{LDAP}@system.gserviceaccount.com`) to project `245831632024`.*

### 📊 Step 3: Generate Dynamic Google Sheet
Use the `gsheets` CLI (`/google/bin/releases/gemini-agents-gsheets/gsheets`) to create a professional pricing sheet. Inject structured SKU data, apply Google Gray 900 borders, Blue 600 headers, and insert dynamic `=SUM()` Excel formulas for 1-year vs 3-year CUD comparisons.

**Execution Command:**
```bash
GSHEETS=/google/bin/releases/gemini-agents-gsheets/gsheets
$GSHEETS create --title "Customer Architecture - GCP Cost Estimate"
$GSHEETS import-csv SPREADSHEET_ID /tmp/agent_artifacts/calculated_estimate.csv
```

### 📄 Step 4: Embed Proposal Summary
1. Use the `gdocs` CLI (`/google/bin/releases/gemini-agents-gdocs/gdocs`) to locate the pricing section anchor in the CE's active proposal document.
2. Insert a clean executive summary table and a direct hyperlinked URL to the generated Google Sheet.

---

## Gotchas & Pitfalls

*   **Borg Service Account Linkage**: If Stubby calls fail with `CloudGaia.GenerateAccessToken; Not found`, verify your Borg service account project linkage (`go/robot-accounts/service-accounts#borg-sa-project-linkage`).
*   **Formula Preservation**: When importing CSV data into Sheets, ensure formula strings (e.g., `=SUM(B2:B10)`) are passed cleanly without escaping leading equals signs.
*   **BNS Stability**: If the primary BNS `/bns/qd/borg/qd-prd/cwp-pricingservice/0` expresses latency, verify your `gcert` session is active.
