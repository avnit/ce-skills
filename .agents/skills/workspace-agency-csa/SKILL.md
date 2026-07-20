---
name: workspace-agency-csa
description: >-
  Use when instantiating, configuring, or executing the Google Workspace Context Service CLI (csa_cli.par) natively inside custom Python agents or bash scripts to perform cross-corpus semantic search across Gmail, Calendar, Drive, and Chat.
---

# Skill: Google Workspace Context Service CLI (csa_cli)

This skill guides you through invoking the pre-compiled **`csa_cli.par`** binary natively on a Google Cloudtop workstation. It enables direct semantic search over corporate Workspace data (`GMAIL, DRIVE, CALENDAR, CHAT`) without causing `gcloud` auth scope conflicts, as it relies entirely on your local **LOAS** (`gcert`) credentials natively.

---

## Core Workflow

To execute a semantic search, run the binary in your terminal or wrap it inside a Python subprocess execution context.

### 1. Execution CLI Recipe

Run the binary directly in your bash shell:

```bash
/google/bin/releases/csa-cli/csa_cli.par \
  --user_prompt="{your_detailed_search_prompt}" \
  --allowed_corpora=GMAIL,DRIVE,CALENDAR,CHAT \
  --latency_budget_seconds=45 \
  --max_output_tokens=20000
```

- _Parameters_:
  - `--user_prompt`: (String, Required) The semantic search query/prompt.
  - `--allowed_corpora`: (String, Required) Comma-separated list of target corpora (`GMAIL,DRIVE,CALENDAR,CHAT`).
  - `--latency_budget_seconds`: (Int, default `45`) Time allocation for the search.
  - `--max_output_tokens`: (Int, default `20000`) Token output limits.

---

## 📅 Recipe: "Last 30 Days Account Review"

To generate a consolidated account review of all customer interactions in the last 30 days, run the following parameterized query:

```bash
/google/bin/releases/csa-cli/csa_cli.par \
  --user_prompt="Find all emails, calendar invites, chat escalations, and shared architectural blueprints regarding the customer '{account_name}' in the last 30 days." \
  --allowed_corpora=GMAIL,DRIVE,CALENDAR,CHAT \
  --latency_budget_seconds=45
```

- _Processing Output_: Parse the standard output to extract:
  - **Timeline Interactions**: Collate timestamps and subject lines.
  - **Citations & Links**: Capture `guri` files and email URLs (`https://mail.google.com/...`) to present exact grounding source links.

---

## 🛠️ Reference Materials & Programmatic Wrappers

- **Python Subprocess Wrapper**: See [subprocess_execution.py](references/subprocess_execution.py) for a clean, reusable Python interface to execute `csa_cli.par` and capture/parse output dynamically in your scripts.

---

## Gotchas & Pitfalls

- **LOAS / gcert Expiry**: GMR queries will fail silently or throw authentication errors if your local `gcert` session has expired. Always run `gcert` to refresh your corporate session before execution.
- **Output Redirect Folder Check**: If piping/teeing output to a directory (e.g. `tee /tmp/agent_artifacts/output.txt`), **always** verify that the parent directory exists or create it first (`mkdir -p /tmp/agent_artifacts/`) to prevent shell output redirect errors.
- **Data Governance & PII**: To comply with `go/code-ai-policy`, **never** cache raw customer PII or confidential Drive chunks in persistent, world-readable directories outside of the ephemeral session context.
