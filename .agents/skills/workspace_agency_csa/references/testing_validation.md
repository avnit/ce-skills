# Testing and Validation Guide

To verify the stability, credentials binding, and data retrieval of your `ContextServiceAgent` integration, utilize the following validation checklist:

---

## 1. Manual Presubmit Smoke Test
Before deploying or committing changes, execute the official Context Service manual presubmit notebook in your workspace:
*   **Notebook Path**: `google3/apps/intelligence/context/g3doc/context_service/developer_guide/context_service_manual_presubmit.ipynb`

Verify that:
- The notebook successfully initiates RPC connections.
- Local LOAS tokens (`gcert`) possess adequate permissions.
- Queries return valid, structured citations.

---

## 2. Regression & Mocking Suite (TEST.md)
When developing your custom CE agent, create a companion test spec `TEST.md` inside your agent's folder. 

Structure a mock trajectory testing the integration E2E:
1.  **Simulate RPC Calls**: Map out mock GMR response payloads.
2.  **Assert Citation Grounding**: Ensure that the agent successfully parses the simulated `guri` citations without hallucinating extra data.
