---
name: system-validation
description: Workspace-level skill to validate onboarding readiness, credentials, persona binding, CitC workspaces, sidecars, and MCP server connectivity before starting any deployments or tests.
---

# Skill: System Validation & Environmental Verification

This skill provides standard procedures and scripts to verify that the workspace is fully onboarded and configured per `.agents/skills/onboarding/SKILL.md`, ensuring all necessary MCP servers, persona rules, and tools are operational.

## Operational Workflow

### 1. Run the System Verification Script

To run the full validation suite, execute the Python helper script from your terminal, passing the dynamic active JetSki conversation artifact directory to avoid polluting the user's workspace:

```bash
python3 .agents/skills/system-validation/scripts/verify_system.py <appDataDir>/brain/<conversation-id>/system_validation_report.md
```

This script performs six key categories of checks:

1. **GCP Config Check**: Validates that `./gcp_config.txt` exists in the repository root and contains non-empty parameters for required keys (`folder_id`, `billing_account`), as well as optional tracking for `piper_workspace` and `cloudtop_host`.
2. **Systems Engineering Persona Check**: Validates that `./.agents/rules/persona.md` exists and binds an active Customer Engineering role (`Practice CE`, `Platform CE`, or `Outcome CE`).
3. **CitC CompanyDoc Readiness Check**: Verifies that `/google/src/cloud/$USER/$piper_workspace/company` is initialized and accessible for internal g3doc/CompanyDoc publishing.
4. **Background Sidecar Daemons Check**: Scans `./.agents/sidecars` to ensure background automated cost and sweep daemons (e.g., `codelab-cleanup`) are valid JSON and synced.
5. **Python Dependencies Check**: Verifies essential authentication and API libraries (`googleapiclient`, `google.auth`) are installed in the host python environment.
6. **MCP Servers Connectivity Check**: Parses `./.gemini/mcp_config.json` and verifies local command-based servers (like `workspace`) and tests HTTP JSON-RPC POST connectivity for documentation servers.

### 2. Remediation Guidelines

If any check fails:

1. **Analyze the Script Output**: Check which components failed (e.g., `gcp_config.txt` keys missing, or specific MCP servers returning connectivity/authentication errors).
2. **Consult Setup Steps**: Point the user to the configuration guide for instructions on how to align environment parameters and enable APIs:
   - [CE-Scale JetSki Configuration](https://docs.google.com/document/d/1KKsh2394jSC_GX5zAsu-JiABjWM6x2SWR5FIa5TrvIY/edit?resourcekey=0-I92ALWXlSgB4_PxS9kbTLw&tab=t.3wn5ohhiptk4)
3. **Instruct the User**: Provide the precise gcloud service enablement or auth login command necessary to fix the problem, then prompt the user to run it.
4. **Re-Verify**: Re-run the validation script after the user confirms the remediation steps have been completed.
