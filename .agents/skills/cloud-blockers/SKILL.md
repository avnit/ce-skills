---
name: cloud-blockers
description: >-
  Queries, filters, and reports on Google Cloud Blockers (CB) and Customer Requests (CR)
  in BigQuery/PLX. Use when looking up Cloud Blockers by account, CR issue ID, CB issue ID,
  severity, product area (including Networking), triage status (CR Triaged vs Pending Triage), or region/cluster.
---

# Skill: Cloud Blockers & Customer Requests (CR) Analytics

Cheatsheet and recipes for interacting with Google Cloud Blockers (CB) and Customer Requests (CR) datasets in PLX (`cloud_blockers_data.prod.cloud_blockers_stack_ranking_report_view`, `buganizer.issuestatsfresh.latest`, `ceops.gcc_opportunities`, `ceops.gcc_workloads`, `gcp_insights.cb_spr_rsr_gtm_data`, `rel360_platform.pst.v1.entities`).

## Core Mandatory Workflow

### Step 1: Pre-flight Resolution & `ask_question` Gate

#### A. Account Name Resolution

When a user requests Cloud Blockers for a customer account (e.g. "Anthropic", "Walmart", "24 7.ai"):

1. Run pre-flight PLX query against `gcc.vector_customers` using `core.account_name`, `core.region`, and `core.sub_region` fields:
   ```sql
   SELECT DISTINCT reporting_id, core.account_name, core.region, core.sub_region
   FROM gcc.vector_customers
   WHERE LOWER(core.account_name) LIKE '%<account_keyword>%'
   ORDER BY core.account_name
   LIMIT 10;
   ```
2. If multiple accounts match, invoke the `ask_question` tool modal to present choices BEFORE proceeding.

#### B. Product Area & Feature Resolution (Multi-Select Gate)

When a user requests Cloud Blockers for a product area or feature (e.g. "Cloud Armor", "PCS Interface", "Cloud CDN"):

1. Run a quick pre-flight PLX query to fetch matching PST product/feature display names:
   ```sql
   SELECT DISTINCT display_name, owning_product_group
   FROM rel360_platform.pst.v1.entities
   WHERE LOWER(display_name) LIKE '%<keyword>%'
   ORDER BY display_name
   LIMIT 10;
   ```
2. Invoke the **`ask_question`** tool modal with `is_multi_select: true` so the user can select one or more specific PST features (e.g. `[x] Cloud Armor for Cloud CDN`, `[x] Google Cloud Armor`).

### Step 2: Execute Cloud Blocker PLX Query

Generate the GoogleSQL query via `scripts/cloud_blocker_lookup.py` using the selected account or PST display names (`--pst-name "Cloud Armor for Cloud CDN, Google Cloud Armor"`) and execute it via PLX `ExecuteSql`.

### Step 3: Render Deterministic Markdown Report Artifact

Pass the raw PLX query output directly to `scripts/render_report.py` to generate the complete 33-column Markdown report artifact without LLM hallucination:

```bash
python3 .agents/skills/cloud-blockers/scripts/render_report.py \
  --input-file <plx_output_file> \
  --output-file <appDataDir>/brain/<conversation-id>/cloud_blocker_report_<slug>.md \
  --account-name "Cloud Armor for Cloud CDN"
```

### Step 4: Render Responsive HTML Email Artifact (For `/send-email`)

To email Cloud Blocker reports without horizontal layout breakage or unrendered markdown links in Gmail, run `scripts/render_email.py` to generate a responsive HTML email card:

```bash
python3 .agents/skills/cloud-blockers/scripts/render_email.py \
  --input-file <plx_output_file_or_markdown_artifact> \
  --output-file <appDataDir>/brain/<conversation-id>/cloud_blocker_email.html \
  --account-name "Cloud Armor for Cloud CDN"

# Send via send-email skill
python3 .agents/skills/send-email/scripts/send_email.py \
  --to "user@google.com" \
  --subject "Cloud Blockers Report: Cloud Armor for Cloud CDN" \
  --body "<appDataDir>/brain/<conversation-id>/cloud_blocker_email.html" \
  --html
```

---

## Quick Start Recipes

### 1. Provide Customer Requests (CRs) for Customer X

```bash
python3 .agents/skills/cloud-blockers/scripts/cloud_blocker_lookup.py --account "Anthropic" --limit 25
```

---

### 2. Lookup Network-Related Customer Requests

Find all Customer Requests targeting Networking, VPC, Interconnect, Cloud DNS, or NetSec PST product areas:

```bash
python3 .agents/skills/cloud-blockers/scripts/cloud_blocker_lookup.py --product-area "Networking" --limit 25
```

---

### 3. Lookup Customer Requests for a Territory Cluster

Find all Customer Requests linked to accounts within a specific territory cluster (e.g., `West 4 (CL)`):

```bash
python3 .agents/skills/cloud-blockers/scripts/cloud_blocker_lookup.py --cluster "West 4" --limit 25
```

---

### 4. Lookup by CR or CB Buganizer Issue ID

Lookup complete details for a specific Customer Request Buganizer ID (e.g. `537381675`):

```bash
python3 .agents/skills/cloud-blockers/scripts/cloud_blocker_lookup.py --cr-id 537381675 --limit 1
```

---

## Dashboard Columns & Output Formatting Rules

Every output report must include the 17 official Cloud Blocker dashboard columns:

| Column Header                 | Source Field / Format                                                                                                      |
| :---------------------------- | :------------------------------------------------------------------------------------------------------------------------- |
| **#**                         | Numbered index (1..N)                                                                                                      |
| **CR Buganizer Issue ID**     | Hyperlinked CR Buganizer link (`[<id>](https://issuetracker.google.com/<id>)`)                                             |
| **CR Triage Admin Link**      | Hyperlinked Cloud Connect Admin URL (`[<id>](https://cloudconnect.corp.google.com/admin/cloud-blockers?cr_issue_id=<id>)`) |
| **CR Title**                  | `cr_title`                                                                                                                 |
| **CR Severity**               | `cr_severity` (`S0`..`S4`)                                                                                                 |
| **CR Created Date**           | `cr_created_date`                                                                                                          |
| **CR Requester**              | `cr_reporter_user` (LDAP)                                                                                                  |
| **CR Age (Days)**             | `cr_days_old`                                                                                                              |
| **CR Triaged/Linked to CB?**  | `triaged` (`CR Triaged` vs `CR Pending Triage`)                                                                            |
| **CR Linked to Opp/Workload** | `opp_or_workload` (`Opportunity` vs `Workload`)                                                                            |
| **Vector Opp/Workload ID**    | Hyperlinked SFDC Vector URL (`[<id>](https://vector.lightning.force.com/<id>)`)                                            |
| **Vector Account Name**       | `account_name`                                                                                                             |
| **Account Sales Region**      | `region`                                                                                                                   |
| **Sales Sub Region**          | `sub_region`                                                                                                               |
| **Cloud Blocker Title**       | `cb_title`                                                                                                                 |
| **go/CB-Resolution-Status**   | `cb_pm_resolution_status`                                                                                                  |
| **CB Buganizer Issue ID**     | Hyperlinked CB Buganizer link (`[<id>](https://issuetracker.google.com/<id>)`)                                             |

---

## Troubleshooting & MCP Resilience Protocol

### 1. Handling PLX MCP `bad local file header` or Binary Errors

If `call_mcp_tool` for `plx` server returns `bad local file header`, `connection reset`, or binary reload exceptions:

- **CRITICAL WARNING:** **NEVER** run `find /google/bin` or `which plx` to locate CLI binaries. Scanning Google's binfs FUSE filesystem takes over 15 minutes and will hang your session!
- **DO NOT** write custom JSON-RPC stdin/stdout scripts (`scratch/exec_plx.py`) or inspect `/google/bin/.../plx-mcp-server.par`.
- **DO NOT** attempt to execute internal FUSE binary paths directly via `run_command`.
- **DO** retry `call_mcp_tool` (`ExecuteSql`) once after a 3-second pause.
- If PLX MCP remains unavailable, generate the query via CLI and output the SQL directly to the user:
  ```bash
  python3 .agents/skills/cloud-blockers/scripts/cloud_blocker_lookup.py --account "PayPal" --pst-area "Networking"
  ```

### 2. Guard against Schema Misalignment in `gcc.vector_customers`

When joining or querying `gcc.vector_customers`:

- **CRITICAL:** `account_details` is an **`ARRAY<PROTO>`**, NOT a struct! Writing `account_details.account_name` directly throws `f1::SQL_ANALYSIS_ERROR: Cannot access field account_name on a value with type ARRAY<...>`.
- **Top-level Account Name:** Use top-level struct **`core.account_name`**, **`core.region`**, and **`core.sub_region`** (`WHERE LOWER(core.account_name) LIKE '%paypal%'`).
- **Unnesting Account Details:** If querying `account_details`, you MUST `UNNEST`: `FROM gcc.vector_customers, UNNEST(account_details) AS acc` and access `acc.account_name`.

### 3. Background Task Execution Protocol

- After launching any `run_command` or background query, **DO NOT** poll `manage_task` in a loop.
- Stop tool calls and let the reactive event system notify you automatically when the background task completes.

---

## Gotchas & Pitfalls

- **Pre-flight Account Check:** Always query `gcc.vector_customers` first before querying `cloud_blockers_data` to ensure exact account name matching and vector account URL alignment.
- **PLX Argument Key:** In PLX MCP `ExecuteSql`, the argument key is lowercase `sql`.
- **SET Statements:** The baseline query requires `SET RequestOptions.requested_enable_feature = 'MIN_COMPLETION_RATIO';` and `SET QueryRequest.return_query_info = true;`.

---

## Supplementary References

- **Schema Details:** See [references/schema.md](references/schema.md) for Buganizer component IDs, custom field mappings, and joined table schemas.
- **Production Baseline SQL:** See [references/reference_sql.md](references/reference_sql.md) for the full GoogleSQL query.
- **Sample Reports:** See [references/sample_reports.md](references/sample_reports.md) for example report output formats with links and brain artifacts.
