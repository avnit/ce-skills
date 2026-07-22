---
description: Validate developer environment readiness, onboarding parameters (gcp_config.txt, persona binding, CitC workspaces, sidecars), and MCP server accessibility.
---

Consult the **system-validation** skill to orchestrate the end-to-end validation of your environment setup per the onboarding baseline.

Steering Workflow:

1. Instruct the agent to read the full operational instructions documented in the **system-validation** skill.
2. Verify that the workspace has been properly onboarded per `/onboarding`:
   - Check that `gcp_config.txt` contains valid `folder_id` and `billing_account`.
   - Check that `.agents/rules/persona.md` binds an active Systems Engineering Persona.
   - Check that all configured MCP servers are present in `.gemini/mcp_config.json`, including the local Google Workspace MCP server (`workspace` mapping to `${WORKSPACE_MCP_SERVER:-/google/bin/releases/codemind-mcp-servers/workspace_server.par}`).
3. Execute the Python system verification script, passing the dynamic active JetSki conversation artifact directory to avoid polluting the user's workspace:
   ```bash
   python3 .agents/skills/system-validation/scripts/verify_system.py <appDataDir>/brain/<conversation-id>/system_validation_report.md
   ```
4. Analyze the exit code and standard output across all six check categories (GCP config, Persona binding, CitC CompanyDoc view, Sidecar sync, Python packages, and MCP connectivity):
   - **If Exit Code is `0`**: Report a successful validation run cleanly to the user.
   - **If Exit Code is `1`**: Report the specific validation failures, recommend triggering `/onboarding` to re-run automated configuration or list precise manual remediation actions needed, and provide the user with the link to the setup guide:
     - [CE-Scale JetSki Configuration](https://docs.google.com/document/d/1KKsh2394jSC_GX5zAsu-JiABjWM6x2SWR5FIa5TrvIY/edit?resourcekey=0-I92ALWXlSgB4_PxS9kbTLw&tab=t.3wn5ohhiptk4)
5. Prompt the user to complete any failed setup requirements and re-run the validation once completed.
