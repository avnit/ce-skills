# Test Plan: GCP Well-Architected Reviewer

This test plan defines validation instructions to verify the E2E execution flow of the compliance reviewer.

---

## Mock Trajectory Test Suite

### Test Scenario: Local Terraform Security Scan E2E
1.  **Ingestion**: Scan the sample vulnerable Terraform files inside `assets/`.
2.  **Cache Load**: Cache the CSPR and NIST spreadsheets locally using `index_knowledge_bases.py`.
3.  **Execution**: Run `compliance_audit.py` to output `/tmp/war_master_findings.json`.
4.  **Assertions**:
    *   Verify that the GCS bucket lacks uniform access vulnerability.
    *   Verify that the KMS key lacks rotation period vulnerability.
    *   Verify that these findings map to correct NIST CSF 2.0 subcategories (`PR.DS-01` and `PR.DS-02`).

---

## Diagnostic Run Command
```bash
# Ingest and cache stubs
python3 .agents/skills/gcp_well_architected_reviewer/scripts/index_knowledge_bases.py

# Execute audit against assets directory
python3 .agents/skills/gcp_well_architected_reviewer/scripts/compliance_audit.py \
  --tf_dir=".agents/skills/gcp_well_architected_reviewer/assets" \
  --output_json="/tmp/agent_artifacts/test_compliance_master.json"
```
Verify the output JSON contains 100% correct mapping entries.
