---
name: gcp-well-architected-reviewer
description: >-
  Use when performing an E2E Google Cloud Well-Architected or Cloud Security Posture Review (CSPR). Automates local Terraform HCL scanning and generates styled CISO-ready NIST CSF 2.0 compliance reports in Google Docs.
---

# Skill: GCP Well-Architected & CSPR Reviewer (100% Offline)

This skill guides you through executing an enterprise-grade cloud auditing, compliance review, and regulatory alignment review natively and offline on your Cloudtop workstation.

---

## Decoupled Operational Steps

Copy this checklist and track progress:
- [ ] Step 1: Execute `index_knowledge_bases.py` to index master knowledge bases locally
- [ ] Step 2: Execute `compliance_audit.py` against local Terraform files
- [ ] Step 3: Synthesize findings and publish the master Google Doc report

---

## Ingestion & Analysis Recipes

### 1. Ingest & Cache Master Knowledge Bases
Run the local indexing utility to build and index your regulatory lookup tables. If static CSV sheets (`assets/cspr_master.csv` and `assets/nist_csf_2_0.csv`) are provided inside the repository, the script will parse them from the disk. Otherwise, it runs in a 100% offline mode, loading pre-populated golden CSPR & NIST rationales automatically.

**Execution Command:**
```bash
python3 .agents/skills/gcp_well_architected_reviewer/scripts/index_knowledge_bases.py
```

### 2. Local HCL Terraform Scanner
Scan local HCL `.tf` files for standard GCP security vulnerabilities (GCS bucket uniform access, public project IAM permissions, missing KMS cryptographic key rotations) and merge discovered gaps with the local JSON lookups.

**Execution Command:**
```bash
python3 .agents/skills/gcp_well_architected_reviewer/scripts/compliance_audit.py \
  --tf_dir="./terraform" --output_json="/tmp/war_master_findings.json"
```

### 3. Master Report Publishing
Format the compiled findings JSON `/tmp/war_master_findings.json` into a structured Markdown report featuring CISO executive scorecard tables, warnings callouts `> [!WARNING]`, and copy-pasteable Terraform remediation blocks. Use the OneDoc `/create-google-doc` webhook or `gdocs` CLI to publish the document directly into Google Drive.

**Execution Command (gdocs CLI Fallback):**
```bash
GDOCS=/google/bin/releases/gemini-agents-gdocs/gdocs
$GDOCS create --title "GCP Well-Architected & CSPR Master Report"
$GDOCS import-md /tmp/war_master_report.md --title "GCP Well-Architected & CSPR Master Report"
```

---

## Gotchas & Pitfalls

*   **CSPR Confidentiality**: The raw CSPR spreadsheet contains internal-only Google review stubs. **Never** expose raw internal cells or BigQuery query structures in your final report. Only extract the approved public `Title(Y)` and `Rationale(Y)` mappings.
*   **Comment Stripping**: The compliance scanner strips all single-line (`#` and `//`) and multi-line (`/* ... */`) comments from the HCL file before scanning. This ensures that commented-out properties are correctly treated as *missing/disabled*, avoiding false positives.
