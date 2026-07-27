---
description: Provision a dedicated GCP test project for codelab validations
---

Consult the **gcp-provisioning** skill to orchestrate the end-to-end creation and preparation of a test project.

Required parameters from the user:

1. Lab Name (e.g., `multi-vpc-dns` or `secure-aws-exchange`)

Steering Workflow:

1. **Phase 0: Pre-Flight Authentication & ADC Verification**
   - Consult and enforce the global auth validation standard: [gcloud_auth.md](../rules/gcloud_auth.md).
   - Execute the **gcloud-auth-verification** skill (`python3 .agents/skills/gcloud-auth-verification/scripts/verify_auth.py`).
   - If active account matches target Sandbox environment (`admin@*.altostrat.com`), log the active identity and proceed automatically.
   - If an account switch or user decision is required, invoke the `ask_question` tool modal to let the user select or confirm the active account.
2. Instruct the agent to read the full execution instructions documented in the **gcp-provisioning** skill manifest.
3. Execute the project provisioning and organization policy removal tasks exactly as defined by the skill's operational guidelines.
4. Return the fully configured `PROJECT_ID` along with linked billing summaries cleanly to the user.

