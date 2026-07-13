---
name: bq-revenue-analytics
description: |
  Comprehensive guide for querying Google Cloud revenue, bookings, quotas, and opportunities in BigQuery.
  Provides mappings for RVP and invoice revenue, GTM product hierarchies, sales territory mappings (NALs),
  standard compliance filters, advanced SQL optimization patterns (partitioning, MD5 distinct hashing),
  and Daily Run Rate (DRR) calculations.
---

# Google Cloud Revenue & Sales BI Query Guide

This skill provides guidelines and performance optimization rules for writing BigQuery SQL queries to analyze Google Cloud revenue, bookings, quotas, and sales pipelines.

## Actionable Guidelines for the Agent

### 1. Identify the Correct Metrics & Fields

Before writing any SELECT or JOIN clauses, refer to the [Schema & Taxonomy Reference](references/schema_mapping.md) and the [Table Portfolio Reference](references/table_portfolio.md) to:

- Choose the correct revenue metric path (RVP, Invoice, Quotas, or Forecast).
- Correctly map GTM vs. Finance product hierarchies.
- Understand the structure, descriptions, and join parameters of our primary tables.
- Locate the correct geography, segment, and reseller channel filters.

### 2. Implement Partition Pruning (Mandatory Cost Control)

- You **must** include a filter on `partition_date` (mapped to `_PARTITIONDATE`) in the main `WHERE` clause.
- **Trap:** Do not filter solely on `usage_date` or `date` as this results in expensive full-table scans.
- See [Partitioning Examples](references/schema_mapping.md#5-performance--scale-optimizations-bigquery-rules) for the exact syntax.

### 3. Handle One-to-Many Joins without Metric Inflation

- When joining opportunity tables (`opportunities_streaming`) to repeating components (like sales plays or product lines), opportunity-level fields (like ACV or TCV) will duplicate.
- Do **not** use a simple `SUM(DISTINCT)` because it collapses different opportunities of matching value size.
- You **must** use the hash-offset deduplication pattern. Refer to the [Cryptographic Deduplication Math](references/opp_deduplication.md) guide for instructions and formulas.

### 4. Apply Compliance Exclusions

Always apply the standard enterprise exclusions to your queries unless explicitly told otherwise:

- Exclude internal test and fraud accounts: `AND NOT is_internal AND NOT is_fraud`
- Exclude Security and Workspace SaaS spend from GCP core metrics: `WHERE gtm_product_level_5 NOT IN ('Security', 'Workspace')`
- Exclude Marketplace pass-through spend from margins: `WHERE gtm_product_level_7 NOT IN ('Marketplace Anthropic', 'Marketplace Oracle', 'Marketplace Other')`

### 5. Deterministic Account Filtering (CRITICAL FOR ACCURACY)

- **Discovery vs. Execution:** Wildcard string searches (e.g., `LIKE '%PAYPAL%'`) are allowed during the initial search phase to discover candidate accounts and present them to the user. However, wildcards must **NEVER** be used in the final query executed to run specific revenue or usage reports.
- **Rule:** The final query must filter deterministically on unique account identifiers (`customer_details.reporting_id` or `sfdc_account_id`).
- **Resolution Flow:** If the exact ID is unknown:
  1. Query the master lookup view `concord-prod.service_cloudbi.vector_customers` using wildcards to discover matching SFDC IDs.
  2. Prompt the user to confirm the exact ID to execute against, or list the combined IDs in the final report header for clear accountability.

---

## SQL Reference & Code Templates

To quickly build and run queries, copy and modify the curated templates from the [SQL Query Templates](examples/template_queries.md) guide:

- [7-Day Symmetric Window Comparison Query](examples/template_queries.md#1-symmetric-date-window-comparison-query-e-g-7-day-comparison)
- [Multi-Level Opportunity Join with Cryptographic Deduplication](examples/template_queries.md#2-multi-level-opportunities-and-sales-play-join-with-cryptographic-deduplication)
