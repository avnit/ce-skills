# Source Classification, Link Verification & Targeted Persona Steering Guide

This reference defines the mandatory source classification rules, sentiment signals, Account Friction Temperature metrics, **Link Authenticity Verification Protocol**, and **Targeted Persona Search Prompt Construction** for Customer Engineering (CE) meeting preparation.

---

## 1. Targeted Persona Search Prompt Construction

To maximize search precision and relevance, `csa_cli.par` does not run generic un-targeted queries. Instead, the `--user_prompt` parameter is dynamically constructed by fusing:

1. **Target Account Name**: `{Customer Name}`
2. **Phase 0 User Selection**: Answers from the interactive `ask_question` modal (e.g. `Practice CE for Networking` vs `Generalist Executive Overview`).
3. **Active Persona Context**: Parameters from [.agents/rules/persona.md](file:///.agents/rules/persona.md).

### Persona Prompt Injection Formula:

```bash
/google/bin/releases/csa-cli/csa_cli.par \
  --user_prompt="Find all communications, email discussions, docs, calendar events, and chat messages regarding {Customer Name} in the last 14 days. Prioritize topics, architectural decisions, tickets, open blockers, and discussions specifically relevant to {Selected Persona Focus / Specialization, e.g. Networking, Infrastructure, PSC, Load Balancing, Security, Data/AI} at {Selected Depth Level, e.g. Level 300/400 Deep Architecture}." \
  --allowed_corpora="GMAIL,DRIVE,CALENDAR,CHAT" \
  --latency_budget_seconds=60 \
  --max_output_tokens=20000
```

---

## 2. Link Authenticity Verification Protocol (Zero Fabrication)

To ensure that every link in the One-Pager is 100% real, active, and clickable, follow these verification rules:

| Link Type                  | Verification Source                            | Allowed Link Pattern                                           | Fall-Through Rule (If URL Not Found)                                                              |
| :------------------------- | :--------------------------------------------- | :------------------------------------------------------------- | :------------------------------------------------------------------------------------------------ |
| **Buganizer Ticket**       | `moma.search` / `buganizer` MCP                | `https://b.corp.google.com/issues/<NUMERICAL_ID>`              | Refer by ticket title without URL (e.g. `[Valkey Custom SAN Ticket]`). Never guess numerical IDs. |
| **Google Drive / Doc**     | `csa_cli.par` / `moma.internal_content_lookup` | Exact `docs.google.com/...` or `drive.google.com/...` link     | Use bold document title (e.g. **Workday IP Draining Guide** `[Unindexed]`).                       |
| **Public GCP Doc**         | `google-developer-knowledge.search_documents`  | Exact `cloud.google.com/...` canonical URL                     | Search via MCP to locate canonical URL; do not construct path.                                    |
| **Workspace Email / Chat** | `csa_cli.par`                                  | Exact `mail.google.com/mail/...` or `chat.google.com/room/...` | Reference email subject line & date without URL.                                                  |

---

## 3. Classification Badges & Sharing Rules

| Classification Badge  | Description & Scope                                                                            | Examples                                                                                                           | Customer Sharing Guidance                                                                                                                                    |
| :-------------------- | :--------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`[Public]`**        | Officially published Google Cloud information available on `cloud.google.com`.                 | GCP Documentation, Public Release Notes, standard IAM roles, public quota defaults, public pricing.                | **Safe for external sharing.** Can be shared in presentation decks, emails, or docs sent directly to customer.                                               |
| **`[Internal Only]`** | Internal Google corporate data, tickets, tools, or design docs.                                | Buganizer issues (b/xxx), Horizon demand records (CDR/RDR), SFDC ERs, internal go/ links, internal design reviews. | **INTERNAL USE ONLY.** Do NOT share direct links, Buganizer IDs, or unredacted internal text with customer. Translate into customer-friendly status updates. |
| **`[Pre-GA / NDA]`**  | Pre-General Availability features (Alpha, Preview, Private Beta) or unannounced roadmap items. | Features under NDA, Private Preview feature flags, internal launch tracker dates.                                  | **REQUIRES NDA & APPROVAL.** Must only be discussed under executed NDA and after confirming customer is whitelisted.                                         |

---

## 4. Account Friction Temperature & Sentiment Taxonomy

Account Friction Temperature measures the level of operational friction, technical frustration, and launch risk present in customer communications:

| Friction Level | Badge         | Trigger Criteria                                                                                                                       | Action Required                                                                             |
| :------------- | :------------ | :------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------ |
| **Low**        | `Low 🟢`      | Smooth execution, active progress, positive collaboration, no open blockers.                                                           | Standard account maintenance & milestone tracking.                                          |
| **Moderate**   | `Moderate 🟡` | Minor capacity or feature request delays; valid workarounds exist; non-blocking for launch.                                            | Assign owner, monitor quota tickets, provide weekly status updates.                         |
| **High**       | `High 🟠`     | Impending go-live (<7 days) with ungranted capacity/quota; trial-and-error deployment friction in key region; unassigned support case. | Escalate to Capacity/Product Leads, schedule technical sync, provide daily updates.         |
| **Critical**   | `Critical 🔥` | Unresolved P1/P2 outage ticket; hard launch blocker; missed milestone attributable to GCP infrastructure.                              | Immediate executive escalation; daily war-room sync; direct engagement with Eng/Product VP. |
