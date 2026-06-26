# Workflow: Google Workspace Semantic Search (/workspace-search)

This workflow orchestrates cross-corpus semantic search across your corporate Google Workspace (`GMAIL, DRIVE, CALENDAR, CHAT`) using the native Context Service CLI (`csa_cli.par`) without causing `gcloud` credential scope conflicts.

## Operational Workflow

### Phase 1: Interactive Query & Corpora Scoping

1. Use the `ask_question` tool to gather search parameters:
   - **Search Target / Query**: Prompt the user for the specific natural language question or topic (e.g., _"Find all design blueprints and email discussions regarding Customer X in the last 14 days"_).
   - **Target Corpora** (Multi-select or selection): Ask which corpora to search:
     - `GMAIL,DRIVE,CALENDAR,CHAT` (All corpora - Recommended)
     - `GMAIL,DRIVE` (Emails and Documents only)
     - `CHAT` (Chat threads and escalations)
   - **Time Horizon / Budget**: Confirm the latency budget (default `45` seconds).

### Phase 2: Pre-Flight LOAS Verification

1. Inform the user that `csa_cli.par` requires an active corporate session.
2. Execute a lightweight check or instruct the user:
   > _"Ensuring your local `gcert` corporate session is active before invoking CSA CLI..."_

### Phase 3: Execute csa_cli.par

1. Execute the search query natively via `run_command`:
   ```bash
   /google/bin/releases/csa-cli/csa_cli.par \
     --user_prompt="<user_query>" \
     --allowed_corpora="<selected_corpora>" \
     --latency_budget_seconds=45 \
     --max_output_tokens=20000
   ```

### Phase 4: Grounded Results & Citation Synthesis

1. Parse the JSON or text response returned by `csa_cli.par`.
2. Present a synthesized markdown report containing:
   - **Executive Summary**: Core findings across the workspace corpora.
   - **Chronological Timeline**: Key email discussions, meetings, and chat decisions.
   - **Grounding Citations**: Exact clickable links (`https://mail.google.com/...` or `guri` Drive links) verifying every source.
