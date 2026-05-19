---
name: system-validation
description: Workspace-level skill to validate gcp_config.txt and MCP server connectivity before starting any deployments or tests.
---

# Skill: System Validation & Environmental Verification

This skill provides standard procedures and scripts to verify that the workspace is fully configured and all necessary MCP servers are reachable.

## Operational Workflow

### 1. Run the System Verification Script
To run the full validation suite, execute the Python helper script from your terminal, passing the dynamic active JetSki conversation artifact directory to avoid polluting the user's workspace:
```bash
python3 .agents/skills/system-validation/scripts/verify_system.py <appDataDir>/brain/<conversation-id>/system_validation_report.md
```

This script performs two key categories of checks:
1. **GCP Config Check**: Validates that `./gcp_config.txt` exists in the repository root and contains non-empty parameters for `folder_id`, `billing_account`, and `cloudtop_host`.
2. **MCP Servers Check**: Parses `./.gemini/mcp_config.json` in the repository root and tests connection to each configured HTTP MCP server using a POST JSON-RPC payload.

### 2. Remediation Guidelines
If any check fails:
1. **Analyze the Script Output**: Check which components failed (e.g., `gcp_config.txt` keys missing, or specific MCP servers returning connectivity/authentication errors).
2. **Consult Setup Steps**: Point the user to the configuration guide for instructions on how to align environment parameters and enable APIs:
   * [CE-Scale JetSki Configuration](https://docs.google.com/document/d/1RLhTRPgfZnXssXog-pKbBnMExulxZyaKMWWTbtw0mF0/edit?usp=sharing&resourcekey=0-ETB7RzJbpqeYH2syDTMF4g)
3. **Instruct the User**: Provide the precise gcloud service enablement or auth login command necessary to fix the problem, then prompt the user to run it.
4. **Re-Verify**: Re-run the validation script after the user confirms the remediation steps have been completed.
