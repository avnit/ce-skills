# Google Cloud Sales BI Table Portfolio Catalog

This document lists the primary tables and views available in the `concord-prod` sales database, their business descriptions, and common join patterns.

---

## Core Transaction & Metric Tables

### 1. `concord-prod.service_cloudbi_reporting.revenue_daily`

- **Description:** High-volume daily recognized and sales revenue metrics. Partitioned by date.
- **Best For:** Short-term Daily Run Rate (DRR) calculations, week-over-week or month-to-date spending analysis.
- **Partition Key:** `partition_date` (Must be filtered in `WHERE` clauses to prevent full table scans).

### 2. `concord-prod.service_cloudbi_reporting.revenue_monthly`

- **Description:** Monthly rolled-up recognized revenue (RVP), quota allocations, and billing totals.
- **Best For:** Monthly run rate trends, multi-year comparisons, and quarterly financial reviews.
- **Partition Key:** `partition_date` (Typically truncated to the first day of each month).

### 3. `concord-prod.service_cloudbi.pipeline_based_outlook_streaming`

- **Description:** Real-time streaming predictions of customer consumption. Combines historical usage with forward-looking committed/uncommitted pipeline estimates.
- **Best For:** Future quarters outlook (PBO) and quota gap tracking.
- **Key Fields:** `pbo_metrics.pipeline_based_outlook`, `pbo_metrics.components.committed_pipeline`.

### 4. `concord-prod.service_cloudbi.opportunities_streaming`

- **Description:** Real-time SFDC opportunities feed. Tracks deal progress, close dates, and contract sizes.
- **Best For:** Closed-won ARR analysis, active pipeline stage reporting, and reseller vs. direct deal splits.
- **Key Fields:** `stage_name` (e.g. `'Closed Won'`), `usd_gcp_incremental_acv` (iACV), `usd_tcv`.

### 5. `concord-prod.service_cloudbi.gcp_watermark_reporting`

- **Description:** A consolidated view comparing committed booking targets (watermarks) against actual billing.
- **Best For:** Tracking contract commitment pacing and identifying spend-pacing opportunities.

---

## Dimension & Mapping Tables

### 6. `concord-prod.service_cloudbi.vector_customers`

- **Description:** The master profile table for customer accounts.
- **Best For:** Retrieving account segmentations, account tiers, and mapping SFDC accounts to billing lists.
- **Key Nested Fields:** `account_details` (needs to be unnested to query fields like rep name, CE owner, and Anaplan categories).

### 7. `concord-prod.service_cloudbi.nals`

- **Description:** Named Account List (NAL) mapping hierarchy.
- **Best For:** Segmenting sales metrics by geographic boundaries, territory clusters, or account namespaces.

### 8. `concord-prod.service_cloudbi.persons`

- **Description:** Corporate personnel hierarchy directory.
- **Best For:** Translating owner IDs to rep names, mapping rep-to-manager reporting chains, and identifying CE owners.

### 9. `concord-prod.service_cloudbi_adhoc.gtml5_sales_play_mapping`

- **Description:** Ad-hoc SKU-to-campaign mapping reference.
- **Best For:** Grouping raw GCP product SKUs into targeted marketing play buckets (e.g., _Migrate Modernize Databases_).

### 10. `concord-prod.service_cloudbi.gcc_workloads_streaming`

- **Description:** Technical workload tracking details (specific cloud migration projects).
- **Best For:** Monitoring workload progress stages (e.g. `0-2: Tech Eval/Solution Dev`, `4.3: Migrated/Implemented`) and assigning technical owner credits.

---

## Common Join Patterns Reference

Use this table to find the correct join criteria between our core tables:

| Source Table              | Join Target Table         | Join Columns                     | Purpose                                         |
| :------------------------ | :------------------------ | :------------------------------- | :---------------------------------------------- |
| `revenue_daily`           | `vector_customers`        | `reporting_id`                   | Extract customer segments/tiers for spend.      |
| `revenue_daily`           | `nals`                    | `customer.nal_id = nals.nal_id`  | Segment spend by sales territories.             |
| `opportunities_streaming` | `persons`                 | `owner_id = person_id`           | Map opportunity owners to sales rep names.      |
| `gcc_workloads_streaming` | `opportunities_streaming` | `opportunity_id`                 | Link technical workloads to pipeline deals.     |
| `opportunities_streaming` | `vector_customers`        | `sfdc_account_id = reporting_id` | Join pipeline opportunities to profile details. |
