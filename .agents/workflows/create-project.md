---
description: Provision a dedicated GCP test project for codelab validations
---

Consult the **gcp-provisioning** skill to orchestrate the end-to-end creation and preparation of a test project.

Required parameters from the user:
1. Lab Name (e.g., `multi-vpc-dns` or `secure-aws-exchange`)

Steering Workflow:
1. Instruct the agent to read the full execution instructions documented in the **gcp-provisioning** skill manifest.
2. Execute the project provisioning and organization policy removal tasks exactly as defined by the skill's operational guidelines.
3. Return the fully configured `PROJECT_ID` along with linked billing summaries cleanly to the user.