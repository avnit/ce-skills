---
name: customer-meeting-prep
description: >-
  Orchestrates end-to-end preparation for Customer Engineering (CE) customer & partner meetings.
  Interactively prompts the user FIRST via ask_question for persona focus vs generalist preferences,
  executes broad Workspace communication audits (Gmail, Drive, Calendar, Chat via csa_cli.par),
  filters and synthesizes retrieved content locally against the active developer persona (.agents/rules/persona.md),
  validates architectural solutions & quotas via Moma Search and Google Developer Knowledge MCP, analyzes
  grounded Account Friction Temperature & Sentiment metrics, enforces deterministic Link Authenticity Verification,
  and tags source classification ([Public], [Internal Only], [Pre-GA / NDA]) in a repeatable One-Pager format.
---

# Skill: Customer Meeting Preparation & Solution Validation

This skill provides a standardized, repeatable procedure for Customer Engineers (CEs) to prepare for high-stakes customer and partner meetings. It begins with a **Pre-Flight Interactive Scoping Modal (`ask_question`)** to establish persona preference, executes a **broad Workspace context retrieval (`csa_cli.par`)**, performs **local agent synthesis & domain filtering** aligned with `.agents/rules/persona.md`, executes multi-source solution validation, calculates grounded sentiment & friction temperature metrics, enforces deterministic link authenticity verification, and outputs a consolidated Document & Reference Directory.

---

## Workflow Overview

```
Phase 0: Pre-Flight Interactive Scoping Modal (ask_question FIRST)
   │  ├── Prompt User: Persona-Based Specialization vs Generalist Overview
   │  └── Prompt User: Required Technical Depth Level (L300/400 vs L200)
   ▼
Phase 1: Broad Workspace Context Retrieval (csa_cli.par SECOND)
   │  └── Broad, unconstrained search across Gmail, Drive, Calendar, & Chat (20k tokens)
   ▼
Phase 2A: Local Agent Synthesis & Persona Domain Filtering
   │  ├── Read Active Persona Parameters from .agents/rules/persona.md
   │  └── Parse retrieved CSA payload locally to isolate persona-specific blockers
   ▼
Phase 2B: Technical & Architectural Solution Validation & Edge-Case Audit
   │  ├── Moma Search (Internal docs, Buganizer, SFDC ERs, go/ links)
   │  └── Google Developer Knowledge MCP (Public GCP docs, quotas, limits)
   ▼
Phase 2C: Grounded Sentiment & Friction Temperature Analysis
   │  ├── Friction Temperature Score (Low 🟢, Moderate 🟡, High 🟠, Critical 🔥)
   │  └── Sentiment Signals & Root Causes (Grounded in exact message links)
   ▼
Phase 3A: Source Classification & Attribution
   │  ├── [Public]: Official public GCP docs & release notes
   │  ├── [Internal Only]: Internal go/ links, Buganizer tickets, Moma results
   │  └── [Pre-GA / NDA]: Pre-GA features, internal roadmap, gated flags
   ▼
Phase 3B: Deterministic Link Authenticity Verification Protocol
   │  ├── Execute scripts/verify_links.py on generated One-Pager
   │  └── Confirm zero broken or fabricated links before presentation
   ▼
Phase 4: One-Pager Artifact Synthesis & Reference Directory
   └── Populate assets/one_pager_template.md & present to user
```

---

## Phase 0: Pre-Flight Interactive Scoping Modal (FIRST STEP)

**BEFORE running `csa_cli.par` or invoking any search tools**, read [.agents/rules/persona.md](../../rules/persona.md) and present an interactive **`ask_question`** modal to prompt the user for their preferred briefing scope and persona focus:

```json
{
  "questions": [
    {
      "question": "How would you like to scope this meeting preparation?",
      "options": [
        "(Recommended) Persona-Based Briefing (Tailored to active persona in .agents/rules/persona.md)",
        "Generalist Executive Overview (Balanced overview across all business goals, timeline risks, and teams)"
      ],
      "is_multi_select": false
    },
    {
      "question": "What technical depth level should be applied?",
      "options": [
        "(Recommended) Level 300/400 Deep Technical & Architecture Briefing (CLI flags, topology, workarounds)",
        "Level 200 High-Level Briefing (Business goals, launch timeline risks, key contacts)"
      ],
      "is_multi_select": false
    }
  ]
}
```

---

## Phase 1: Broad Workspace Context Retrieval (SECOND STEP)

Execute `${CSA_CLI:-/google/bin/releases/csa-cli/csa_cli.par}` with a **broad, unconstrained customer prompt** to bring back 100% of available Workspace context across Gmail, Drive, Calendar, and Chat:

```bash
${CSA_CLI:-/google/bin/releases/csa-cli/csa_cli.par} \
  --user_prompt="Find all communications, email discussions, docs, calendar events, and chat messages regarding {Customer Name} in the last 14 days." \
  --allowed_corpora="GMAIL,DRIVE,CALENDAR,CHAT" \
  --latency_budget_seconds=60 \
  --max_output_tokens=20000
```

> [!IMPORTANT]
> **Why Broad Ingestion + Local Filtering is Critical**:
> `csa_cli.par` vector search works best with simple, unconstrained prompt strings. Trying to hyper-filter inside the `csa_cli` prompt drops critical context. By returning the full 20,000 token payload, the **agent itself** locally parses and filters the retrieved communications in Phase 2A.

---

## Phase 2A: Local Agent Synthesis & Persona Steering

Once `csa_cli.par` returns the broad payload:

1. **Ingest Active Persona (.agents/rules/persona.md)**: Check active role (e.g. `Practice CE for Networking` vs `Security` vs `Data/AI`).
2. **Local Domain Filtering**: Filter the retrieved threads locally:
   - If persona is **Networking**: Prioritize threads, bugs, and docs related to Private Service Connect (PSC), Load Balancers, Cloud Armor, IP draining, Interconnect, BGP, VPC-SC, and cross-zone latency.
   - If persona is **Security**: Prioritize threads related to IAM, KMS, Org Policies, VPC-SC, and audit logging.
   - If persona is **Data / AI**: Prioritize threads related to Spanner, Valkey/Memorystore, AlloyDB, BigQuery, and Vertex AI.
   - If user selected **Generalist**: Balance topics across all engineering tracks and executive launch risks.

---

## Link Authenticity Verification Protocol (Zero Fabrication)

To guarantee that 100% of links in the One-Pager are real and clickable, agents MUST execute the verification script gate:

```bash
python3 .agents/skills/customer-meeting-prep/scripts/verify_links.py \
  <path_to_one_pager.md>
```

---

## Step-by-Step Execution Guide

### Step 1: Trigger `ask_question` Modal FIRST

Present the Phase 0 pre-flight modal to capture the user's persona preference and depth requirements before executing any commands.

---

### Step 2: Execute Broad Workspace Search

Run `csa_cli.par` with a broad prompt for `{Customer Name}` to retrieve all recent Workspace communications across Gmail, Drive, Calendar, and Chat.

---

### Step 3: Local Agent Synthesis & Domain Filtering

Filter and summarize the retrieved payload locally based on the active persona in `.agents/rules/persona.md` and user's Phase 0 modal choices.

---

### Step 4: Solution Validation & Multi-Source Verification

Validate technical claims, error messages, capacity asks, or architectural recommendations:

1. **Internal Validation (`moma` MCP)**: Buganizer tickets, Horizon requests, SFDC ERs, internal go/ links.
2. **Public Validation (`google-developer-knowledge` MCP)**: Supported machine shapes, quotas, limits, and published documentation.

---

### Step 5: Grounded Sentiment & Account Friction Temperature Analysis

Evaluate account sentiment and calculate an **Account Friction Temperature** score based _strictly_ on verified evidence from communication threads and support cases:

#### Friction Temperature Scale:

- **`Low 🟢`**: Smooth execution, active progress, positive collaboration, no open blockers.
- **`Moderate 🟡`**: Minor capacity or feature request delays; workaround exists; customer timeline not compromised.
- **`High 🟠`**: Impending go-live deadline (<7 days) with unresolved capacity/quota blocks; trial-and-error deployment friction.
- **`Critical 🔥`**: Unresolved P1/P2 outage ticket; unassigned support escalation; missed launch deadline attributable to GCP.

---

### Step 6: Source Classification & Link Verification Audit

1. Apply classification badges (`[Public]`, `[Internal Only]`, `[Pre-GA / NDA]`).
2. Run `scripts/verify_links.py` to confirm zero 404s or broken URLs.

---

### Step 7: Author One-Pager Artifact & Key Reference Directory

1. Copy template from `assets/one_pager_template.md`.
2. Populate all sections incorporating persona specialization priorities.
3. Save as `<appDataDir>/brain/<conversation-id>/<customer_name>_meeting_prep.md`.

---

## Success Criteria & Quality Bar

- [ ] **Interactive Pre-Flight Gate (FIRST)**: `ask_question` modal executed FIRST before invoking `csa_cli.par` or any discovery tools.
- [ ] **Broad Ingestion + Local Agent Filtering**: `csa_cli.par` prompt is broad and unconstrained. Content is filtered and prioritized locally by the agent against `.agents/rules/persona.md`.
- [ ] **100% Real Verified Links**: Passed `scripts/verify_links.py` execution with 0 broken or fabricated URLs.
- [ ] **Anonymized & Community Safe**: All committed skill examples must use anonymized, generic placeholders (`Acme Corp`, `b/123456789`).
- [ ] **Consolidated Reference Directory**: Includes a dedicated section at the bottom linking all verified Docs, Trix sheets, Bugs, and Chat threads.
- [ ] **Strict Classification**: Every single Q&A entry carries an explicit `[Public]`, `[Internal Only]`, or `[Pre-GA / NDA]` tag.
