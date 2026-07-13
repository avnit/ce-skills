---
name: bq-expert-requests
description: |
  Analyzes Customer Engineering (CE) Expert Requests (ER) in BigQuery.
  Provides schema mappings for expert_requests, joins to workloads and opportunities,
  tracking in-flight vs completed ER metrics, calculating attached ARR/ACV, measuring stage progression,
  and auditing CE rep productivity.
---

# Customer Engineering (CE) Expert Requests (ER) Query Guide

This skill provides guidelines, metric definitions, join patterns, and performance optimization rules for querying **Expert Requests (ER)** in BigQuery (`concord-prod.service_cloudbi.expert_requests`).

## Actionable Guidelines for the Agent

### 1. Identify the Correct ER Schemas & Metrics

Before writing any SELECT or JOIN clauses, refer to the [ER Schema & Metric Taxonomy Reference](references/er_schema.md) to:

- Understand primary columns, status categories (`In-Flight` vs. `Completed`), and metric formulas.
- Map table relationships when joining `expert_requests` to `opportunities_streaming`, `gcc_workloads_streaming`, or `ce_rep_details`.

### 2. Track Opportunity Stage Progression & Status History

- When measuring if an ER accelerated a deal to Stage 3 Proposal/Negotiation or Stage 4, unnest the status field history.
- Do not rely solely on current stage without checking the stage at ER creation date.
- Refer to the [Stage Progression & Deduplication Logic](references/stage_progression.md) guide for instructions.

### 3. Handle One-to-Many Joins without Metric Inflation

- When joining `expert_requests` to opportunities or workloads, an opportunity can have multiple ERs attached.
- Do **not** use `SUM(o.usd_acv)` directly (double-counts deal amounts) or `SUM(DISTINCT o.usd_acv)` (collapses matching deal sizes).
- Use the **Cryptographic MD5 Hash-Offset SUM(DISTINCT)** pattern documented in [Stage Progression & Deduplication Logic](references/stage_progression.md#2-cryptographic-md5-deduplication-for-er-acvarr).

### 4. Deterministic Account Filtering

- Never use wildcard matching (`LIKE '%PAYPAL%'`) in report execution queries.
- Always filter deterministically on unique account IDs (`er.reporting_id` or `o.opportunity_id`).
- Wildcard searches are only permitted during discovery to resolve matching IDs.

### 5. Construct Salesforce Vector Deep Links & Output Formats

- Construct direct clickable **Salesforce Vector URLs** in SQL queries for ERs, Accounts, Opportunities, and Workloads.
- Refer to the [Salesforce Vector Deep Links & Report Formatting Guide](references/vector_url_formatting.md) for exact URL patterns, Markdown table formats, and HTML report templates.

---

## SQL Reference & Code Templates

To quickly build and run queries, copy and adapt the curated templates from the [ER SQL Reference Templates](examples/template_queries.md) guide:

- [CE Rep Productivity & Activity Leaderboard Template](examples/template_queries.md#template-1-ce-rep-productivity--activity-leaderboard-with-vector-links)
- [Opportunity Stage Progression Tracker Template](examples/template_queries.md#template-2-opportunity-stage-progression-tracker-with-vector-deep-links)
