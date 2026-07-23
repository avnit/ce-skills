---
name: plx-vector-customers
description: >-
  Provides exact SQL recipes, schema definitions, gotchas, and CLI scripts for
  querying concord-prod.service_cloudbi.vector_customers via PLX (gcc.vector_customers).
  Use when looking up SFDC Vector reporting IDs from account names, generating NAL
  (Named Account List) customer rosters, or identifying assigned Field Sales
  Representatives (FSR) and Customer Engineers (CE). Constructs direct Salesforce Vector
  URLs and formats results as numbered lists (1..N).
---

# Skill: PLX Vector Customers & NAL Territory Analytics

Cheatsheet and recipes for interacting with Google Cloud's `vector_customers` dataset in BigQuery/PLX (`concord-prod.service_cloudbi.vector_customers` via PLX table `gcc.vector_customers`).

## Quick Start Recipes

### 1. Lookup Reporting ID & Vector Link from Account Name
Find SFDC Vector `reporting_id`, direct Vector URL, NAL ID, and Sales Region for a customer:

```sql
SELECT
  reporting_id,
  CONCAT('https://vector.lightning.force.com/lightning/r/Account/', reporting_id, '/view') AS vector_url,
  core.account_name AS account_name,
  core.nal_id AS nal_id,
  core.nal_name AS nal_name,
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
  acc.primary_field_rep AS primary_field_rep_fsr,
  acc.customer_engineer AS customer_engineer_ce
FROM gcc.vector_customers,
UNNEST(account_details) AS acc
WHERE UPPER(core.account_name) LIKE '%WORKDAY%'
LIMIT 5;
```

### 3. Accounts List per NAL / Territory Cluster
List all accounts assigned to a specific NAL ID or NAL Name:

```sql
SELECT
  reporting_id,
  CONCAT('https://vector.lightning.force.com/lightning/r/Account/', reporting_id, '/view') AS vector_url,
  core.account_name AS account_name,
  core.segment AS segment,
  core.region AS region,
  core.sub_region AS sub_region
FROM gcc.vector_customers
WHERE core.nal_id = 2507192445
ORDER BY core.account_name;
```

---

## Gotchas & Pitfalls

1. **Vector Salesforce Links:**
   - Always construct the direct link `https://vector.lightning.force.com/lightning/r/Account/<reporting_id>/view` using `CONCAT(...)`.
2. **Numbered Indexing for User Interaction:**
   - When returning multiple accounts, format them with 1-based index numbers (`1.`, `2.`, `3.`) so the user can easily ask for "more details on #1".
3. **Table Access Route:**
   - Prefer using `gcc.vector_customers` over `google.vector_customers` or `concord-prod.service_cloudbi.vector_customers` in PLX `ExecuteSql` calls to avoid restricted Datahub ACL permissions.
4. **Repeated Proto Fields:**
   - `primary_field_rep` and `customer_engineer` live inside the array `account_details`. Always use `UNNEST(account_details)` when retrieving account team members.

---

## Execution Guide

Run the standalone CLI helper script directly inside your terminal or from custom scripts:

```bash
# Lookup customer by name (includes Vector URLs & 1..N indexing)
python3 .agents/skills/plx-vector-customers/scripts/vector_lookup.py --account "Workday"

# List accounts for a NAL ID
python3 .agents/skills/plx-vector-customers/scripts/vector_lookup.py --nal 2507192445

# Lookup assigned FSR / CE account team
python3 .agents/skills/plx-vector-customers/scripts/vector_lookup.py --team "Workday"
```

---

## Supplementary References

*   **Schema Details:** See [references/schema.md](references/schema.md) for full `CoreDetails` and `AccountDetails` proto schemas.
*   **Production SQL Queries:** See [references/reference_sql.md](references/reference_sql.md) for advanced GoogleSQL queries.
*   **Sample Reports:** See [references/sample_reports.md](references/sample_reports.md) for example report output formats with Vector links and numbered indexing.
