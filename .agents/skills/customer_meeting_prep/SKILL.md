---
name: customer-meeting-prep
description: >-
  Orchestrates end-to-end preparation for Customer Engineering (CE) customer & partner meetings.
  Interactively prompts the user FIRST via ask_question for persona focus vs generalist preferences,
  dynamically passes persona & user preferences into targeted csa_cli.par search prompts across Gmail, Drive, Calendar, & Chat,
  validates architectural solutions & quotas via Moma Search and Google Developer Knowledge MCP, analyzes
  grounded Account Friction Temperature & Sentiment metrics, enforces deterministic Link Authenticity Verification,
  and tags source classification ([Public], [Internal Only], [Pre-GA / NDA]) in a repeatable One-Pager format.
---

# Skill: Customer Meeting Preparation & Solution Validation

This skill provides a standardized, repeatable procedure for Customer Engineers (CEs) to prepare for high-stakes customer and partner meetings. It starts with a **Pre-Flight Interactive Scoping Modal (`ask_question`)** to establish persona preference, dynamically injects user choices into targeted workspace communication audits, executes multi-source solution validation, calculates grounded sentiment & friction temperature metrics, enforces deterministic link authenticity verification, and outputs a consolidated Document & Reference Directory.

---

## Workflow Overview

```
Phase 0: Pre-Flight Interactive Scoping Modal (ask_question FIRST)
   │  ├── Prompt User: Persona-Based Specialization vs Generalist Overview
   │  └── Prompt User: Required Technical Depth Level (L300/400 vs L200)
   ▼
Phase 1: Targeted & Persona-Steered Workspace Audit (csa_cli.par SECOND)
   │  └── Inject Phase 0 Persona Answers & persona.md Rules into --user_prompt
   ▼
Phase 2A: Technical & Architectural Solution Validation & Edge-Case Audit
   │  ├── Moma Search (Internal docs, Buganizer, SFDC ERs, go/ links)
   │  ├── Google Developer Knowledge MCP (Public GCP docs, quotas, limits)
   │  └── Persona-Aligned Technical Sweep
   ▼
Phase 2B: Grounded Sentiment & Friction Temperature Analysis
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

**BEFORE running `csa_cli.par` or invoking any search tools**, read [.agents/rules/persona.md](file:///.agents/rules/persona.md) and present an interactive **`ask_question`** modal to prompt the user for their preferred briefing scope and persona focus:

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

## Phase 1: Targeted & Persona-Steered Workspace Audit (SECOND STEP)

Once the user completes the `ask_question` modal, **dynamically construct the `--user_prompt` parameter** of `csa_cli.par` by injecting:

1. `{Customer Name}`
2. User's selected persona choice from Phase 0 (e.g. `Practice CE for Networking`, `Practice CE for Security`, `Practice CE for Data/AI`, or `Generalist Executive Overview`).
3. Active role objectives & technical depth parameters from [.agents/rules/persona.md](file:///.agents/rules/persona.md).

### Persona-Targeted Command Execution Template:

```bash
/google/bin/releases/csa-cli/csa_cli.par \
  --user_prompt="Find all communications, email discussions, docs, calendar events, and chat messages regarding {Customer Name} in the last 14 days. Filter and prioritize topics, architectural decisions, tickets, open blockers, and discussions EXCLUSIVELY relevant to {Selected Persona Domain ONLY, e.g. Practice CE for Networking: Private Service Connect, Load Balancers, Cloud Armor, Interconnect, IP Draining, ILB Latency} at {Selected Depth Level}." \
  --allowed_corpora="GMAIL,DRIVE,CALENDAR,CHAT" \
  --latency_budget_seconds=60 \
  --max_output_tokens=20000
```

> [!CAUTION]
> **CRITICAL DOMAIN ISOLATION RULE**:
> Do NOT combine multiple unrelated domains (e.g., mixing Networking with Data/AI/Dataproc/Oracle) in the `csa_cli.par` prompt. If the active persona is **Networking**, restrict search keywords strictly to Networking & Infrastructure (PSC, ALB, Interconnect, BGP, IP draining, Latency) to prevent data science or database threads from crowding out networking blockers.

---

### Mandatory Customer Participant LinkedIn Profile Retrieval Protocol

For **EVERY** participant identified in the Customer Team list:

1. **Workspace Extraction**: Check calendar invites, meeting notes, email signatures, and pre-read slides retrieved by `csa_cli.par` for existing `https://www.linkedin.com/in/*` URLs.
2. **Mandatory Web Search (`search_web`)**: If a participant's LinkedIn profile link is missing, you **MUST** run the `search_web` tool for that participant:
   ```bash
   search_web query="{Participant Name} {Customer Company Name} LinkedIn profile"
   ```
3. **Verification & Attribution**: Validate the profile URL structure with `verify_links.py` and format as `[Customer Participant](https://www.linkedin.com/in/username) — Title/Role [Public]`.

---

## Link Authenticity Verification Protocol (Zero Fabrication)

To guarantee that 100% of links in the One-Pager are real and clickable, agents MUST execute the verification script gate:

```bash
python3 .agents/skills/customer_meeting_prep/scripts/verify_links.py \
  <path_to_one_pager.md>
```

---

## Step-by-Step Execution Guide

### Step 1: Trigger `ask_question` Modal FIRST

Present the Phase 0 pre-flight modal to capture the user's persona preference and depth requirements before executing any commands.

---

### Step 2: Execute Persona-Targeted Workspace Search

Dynamically inject the user's Phase 0 answers into the `csa_cli.par` `--user_prompt` parameter and run search across Gmail, Drive, Calendar, and Chat.

---

### Step 3: Solution Validation & Multi-Source Verification

Validate technical claims, error messages, capacity asks, or architectural recommendations:

1. **Internal Validation (`moma` MCP)**: Buganizer tickets, Horizon requests, SFDC ERs, internal go/ links.
2. **Public Validation (`google-developer-knowledge` MCP)**: Supported machine shapes, quotas, limits, and published documentation.

---

### Step 4: Grounded Sentiment & Account Friction Temperature Analysis

Evaluate account sentiment and calculate an **Account Friction Temperature** score based _strictly_ on verified evidence from communication threads and support cases:

#### Friction Temperature Scale:

- **`Low 🟢`**: Smooth execution, active progress, positive collaboration, no open blockers.
- **`Moderate 🟡`**: Minor capacity or feature request delays; workaround exists; customer timeline not compromised.
- **`High 🟠`**: Impending go-live deadline (<7 days) with unresolved capacity/quota blocks; trial-and-error deployment friction.
- **`Critical 🔥`**: Unresolved P1/P2 outage ticket; unassigned support escalation; missed launch deadline attributable to GCP.

---

### Step 5: Source Classification & Link Verification Audit

1. Apply classification badges (`[Public]`, `[Internal Only]`, `[Pre-GA / NDA]`).
2. Run `scripts/verify_links.py` to confirm zero 404s or broken URLs.

---

### Step 6: Author One-Pager Artifact & Key Reference Directory

1. Copy template from `assets/one_pager_template.md`.
2. Populate all sections incorporating persona specialization priorities.
3. Save as `<appDataDir>/brain/<conversation-id>/<customer_name>_meeting_prep.md`.

---

## Success Criteria & Quality Bar

- [ ] **Interactive Pre-Flight Gate (FIRST)**: `ask_question` modal executed FIRST before invoking `csa_cli.par` or any discovery tools.
- [ ] **Targeted & Persona-Steered Prompting**: `csa_cli.par --user_prompt` dynamically incorporates Phase 0 answers and `.agents/rules/persona.md` parameters to steer vector search toward persona-specific technical topics.
- [ ] **100% Real Verified Links**: Passed `scripts/verify_links.py` execution with 0 broken or fabricated URLs.
- [ ] **Anonymized & Community Safe**: All committed skill examples must use anonymized, generic placeholders (`Acme Corp`, `b/123456789`).
- [ ] **Consolidated Reference Directory**: Includes a dedicated section at the bottom linking all verified Docs, Trix sheets, Bugs, and Chat threads.
- [ ] **Strict Classification**: Every single Q&A entry carries an explicit `[Public]`, `[Internal Only]`, or `[Pre-GA / NDA]` tag.
