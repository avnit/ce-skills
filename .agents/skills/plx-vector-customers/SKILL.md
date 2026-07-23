---
name: plx-vector-customers
description: >-
  Provides exact SQL recipes, schema definitions, gotchas, and CLI scripts for
  querying concord-prod.service_cloudbi.vector_customers via PLX (gcc.vector_customers).
  Use when looking up SFDC Vector reporting IDs from account names, generating NAL
  (Named Account List) customer rosters, NAL Cluster account rosters, or identifying assigned Field Sales
  Representatives (FSR) and Customer Engineers (CE). Constructs direct Salesforce Vector
  URLs and formats results as numbered lists (1..N). Always writes persistent report
  artifacts to the brain directory (<appDataDir>/brain/<conversation-id>/...).
---

# Skill: PLX Vector Customers & NAL Territory Analytics

Cheatsheet and recipes for interacting with Google Cloud's `vector_customers` dataset in BigQuery/PLX (`concord-prod.service_cloudbi.vector_customers` via PLX table `gcc.vector_customers`).

## Quick Start Recipes

### 1. Lookup Reporting ID & Vector Link from Account Name
Find SFDC Vector `reporting_id`, direct Vector URL, NAL ID, NAL Cluster, and Sales Region for a customer:

```sql
SELECT
  reporting_id,
  CONCAT('https://vector.lightning.force.com/lightning/r/Account/', reporting_id, '/view') AS vector_url,
  core.account_name AS account_name,
  core.nal_id AS nal_id,
  core.nal_name AS nal_name,
  core.nal_cluster AS nal_cluster,
  core.region AS region,
  core.sub_region AS sub_region
FROM gcc.vector_customers
WHERE UPPER(core.account_name) LIKE '%WORKDAY%'
LIMIT 10;
```

> **User Output Rule:** Always format search results as a **numbered list (1..N)** including the clickable `[Vector Link](url)` so users can click directly to open Salesforce, or reply with `#1` or `#2` to request deeper account details.

### 2. Lookup Account Team (FSR & Customer Engineer)
Unnest `account_details` to retrieve assigned **Primary Field Reps (FSR)** and **Customer Engineers (CE)**:

```sql
SELECT
  reporting_id,
  CONCAT('https://vector.lightning.force.com/lightning/r/Account/', reporting_id, '/view') AS vector_url,
  core.account_name AS account_name,
  core.nal_id AS nal_id,
  core.nal_name AS nal_name,
  core.nal_cluster AS nal_cluster,
  acc.primary_field_rep AS primary_field_rep_fsr,
  acc.customer_engineer AS customer_engineer_ce
FROM gcc.vector_customers,
UNNEST(account_details) AS acc
WHERE UPPER(core.account_name) LIKE '%WORKDAY%'
LIMIT 5;
```

### 3. Accounts Roster by NAL / Territory Cluster
List all accounts assigned to a specific NAL ID or NAL Name, including `nal_cluster`:

```sql
SELECT
  reporting_id,
  CONCAT('https://vector.lightning.force.com/lightning/r/Account/', reporting_id, '/view') AS vector_url,
  core.account_name AS account_name,
  core.segment AS segment,
  core.nal_name AS nal_name,
  core.nal_cluster AS nal_cluster,
  core.region AS region,
  core.sub_region AS sub_region
FROM gcc.vector_customers
WHERE core.nal_id = 2507192445
ORDER BY core.account_name;
```

### 4. Accounts Roster by Cluster (or Target Account's Cluster)
List all accounts sharing the same NAL Cluster as a target reporting ID or cluster name (e.g. `West 4 (CL)`):

```sql
WITH target_cluster AS (
  SELECT core.nal_cluster AS cluster_name
  FROM gcc.vector_customers
  WHERE reporting_id = '0014M00001h3l17QAA'
  LIMIT 1
)
SELECT DISTINCT
  reporting_id,
  CONCAT('https://vector.lightning.force.com/lightning/r/Account/', reporting_id, '/view') AS vector_url,
  core.account_name AS account_name,
  core.segment AS segment,
  core.nal_id AS nal_id,
  core.nal_name AS nal_name,
  core.nal_cluster AS nal_cluster,
  core.region AS region,
  core.sub_region AS sub_region
FROM gcc.vector_customers, target_cluster
WHERE core.nal_cluster = target_cluster.cluster_name
ORDER BY account_name;
```

---

## Required Output Rules

1. **Vector Salesforce Links:**
   - Always construct the direct link `https://vector.lightning.force.com/lightning/r/Account/<reporting_id>/view` using `CONCAT(...)`.
2. **Include NAL & Cluster Details:**
   - Always include `core.nal_id`, `core.nal_name`, and `core.nal_cluster` in NAL & cluster report outputs.
3. **Numbered Indexing for User Interaction:**
   - Format search results with 1-based index numbers (`1.`, `2.`, `3.`) so the user can easily ask for "more details on #1".
4. **Brain Markdown Artifact Creation:**
   - Whenever executing an account search, NAL roster listing, cluster roster listing, or territory report, **always create a persistent Markdown artifact file** under `<appDataDir>/brain/<conversation-id>/vector_account_report.md` using `write_to_file` (`UserFacing: true`, `RequestFeedback: false`).
   - Include a direct clickable file link `[vector_account_report.md](file:///<appDataDir>/brain/<conversation-id>/vector_account_report.md)` in the chat response.

---

## Gotchas & Pitfalls

1. **Table Access Route:**
   - Prefer using `gcc.vector_customers` over `google.vector_customers` or `concord-prod.service_cloudbi.vector_customers` in PLX `ExecuteSql` calls to avoid restricted Datahub ACL permissions.
2. **Repeated Proto Fields:**
   - `primary_field_rep` and `customer_engineer` live inside the array `account_details`. Always use `UNNEST(account_details)` when retrieving account team members.

---

## Execution Guide

Run the standalone CLI helper script directly inside your terminal or from custom scripts:

```bash
# Lookup customer by name (includes Vector URLs & 1..N indexing)
python3 .agents/skills/plx-vector-customers/scripts/vector_lookup.py --account "Workday"

# List accounts for a NAL ID
python3 .agents/skills/plx-vector-customers/scripts/vector_lookup.py --nal 2507192445

# List accounts for a Cluster Name
python3 .agents/skills/plx-vector-customers/scripts/vector_lookup.py --cluster "West 4 (CL)"

# Lookup assigned FSR / CE account team
python3 .agents/skills/plx-vector-customers/scripts/vector_lookup.py --team "Workday"
```

---

## Supplementary References

*   **Schema Details:** See [references/schema.md](references/schema.md) for full `CoreDetails` and `AccountDetails` proto schemas.
*   **Production SQL Queries:** See [references/reference_sql.md](references/reference_sql.md) for advanced GoogleSQL queries.
*   **Sample Reports:** See [references/sample_reports.md](references/sample_reports.md) for example report output formats with Vector links, clusters, and brain artifacts.
