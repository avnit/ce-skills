# Test Plan: GCP Pricing Estimator

This test plan outlines validation guidelines to verify the E2E execution flow of the pre-sales pricing estimator.

---

## Mock Trajectory Test Suite

### Test Scenario: Terraform Ingestion E2E
1.  **Ingestion Intake**: Provide a GKE and AlloyDB terraform setup in `/infra`.
2.  **Mock BNS Response**: Mocks the `CWP.PricingService` BNS Stubby response to return standard regional costs and enterprise contract discounts.
3.  **Assert Sheets CLI**: Verify the agent executes the `gsheets create` and `gsheets import-csv` CLI commands in the correct sequence.
4.  **Assert Docs Summary**: Verify the agent writes a styled markdown summary and links it in the proposal Google Doc using `gdocs edit`.

---

## Diagnostic Commands

To run a quick dry-run on your Cloudtop environment:
```bash
python3 .agents/skills/gcp_pricing_estimator/scripts/pricing_client.py \
  --payload_path=".agents/skills/gcp_pricing_estimator/examples/sample_topology.json" \
  --output_path="/tmp/agent_artifacts/test_estimate.json"
```
Verify the output JSON is populated with valid pricing entries.
