---
name: onboarding
description: Automates developer environment setup including gcp_config.txt generation, persona binding, MCP JSON injection, CitC verification, and sidecar daemon synchronization.
---

# Developer Environment Onboarding Skill

This skill provides deterministic automation for onboarding developer workstations and cloudtop instances.

## When to use this skill

Use this skill during the `/onboarding` workflow or whenever a user needs to configure their local `gcp_config.txt` credentials, bind their engineering persona (`.agents/rules/persona.md`), configure local MCP servers (`.gemini/mcp_config.json`), or synchronize background sidecar scripts.

## Usage Instructions

After collecting onboarding parameters interactively from the user via `ask_question`, execute the Python automation script using the `run_command` tool:

```bash
python3 .agents/skills/onboarding/scripts/onboard.py \
  --persona "<Practice CE | Platform CE | Outcome CE>" \
  --folder-id "<folder_id>" \
  --billing-account "<billing_account_id>" \
  --billing-project "<billing_project_id>" \
  [--billing-table "<billing_table_id>"] \
  [--cloudtop-host "<cloudtop_hostname>"] \
  [--knowledge-project "<knowledge_project_id>"] \
  [--piper-workspace "<piper_workspace_name>"]
```

### Script Arguments:

- `--persona`: (Required) The selected Systems Engineering Persona. Must be one of `Practice CE`, `Platform CE`, or `Outcome CE`.
- `--folder-id`: (Required) Target Google Cloud Folder ID for sandbox project provisioning.
- `--billing-account`: (Required) Target Google Cloud Billing Account ID (e.g., `01C4AF-4A2D30-073483`).
- `--billing-project`: (Required) Target BigQuery project ID containing billing export datasets. Can be set via the `CE_BILLING_PROJECT` environment variable.
- `--billing-table`: (Optional) Target BigQuery table ID for detailed resource billing exports.
- `--cloudtop-host`: (Optional) Hostname of the developer's dedicated Cloudtop VM.
- `--knowledge-project`: (Optional) Quota project ID for Developer Knowledge MCP server requests. Can be set via the `CE_KNOWLEDGE_PROJECT` environment variable.
- `--piper-workspace`: (Optional, defaults to `ce-skills`) Preferred CitC/Fig workspace name for staging and publishing live CompanyDocs. Automatically forced/created if missing and recorded in `gcp_config.txt`.

## Automated Operations Performed

The script executes the following deterministic operations:

1. **Persona Rule Binding**: Creates `.agents/rules/persona.md` configured with the exact architectural depth and tooling mappings for the chosen role.
2. **Credential Configuration**: Writes `gcp_config.txt` containing clean `key=value` pairs.
3. **MCP Configuration Injection**: Updates `.gemini/mcp_config.json` to inject `X-goog-user-project` headers for `google-developer-documentation-mcp` and ensures the `workspace` MCP server binary is registered.
4. **Piper CompanyDoc Readiness Check**: Verifies if an active CitC/Fig workspace under `${CITC_WORKSPACE_ROOT:-/google/src/cloud/$USER/<your-client>}` includes the `/company` view.
5. **Sidecar & Cache Sync**: Pre-warms Mermaid CLI caching and triggers `sync_sidecars.sh`.
6. **Community Group Membership**: Prompts and verifies membership in `ce-skills-users@google.com` via self-service web link or CLI `membership_tool` using tickets under Buganizer Component ID `2150801`.
