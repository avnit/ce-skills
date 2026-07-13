# Google Cloud Revenue & Sales BI SQL Reference Templates

This document contains standard template queries for common revenue analysis tasks.

---

## 1. Symmetric Date Window Comparison Query (e.g. 7-Day Comparison)

This query performs a single-scan, partition-pruned comparison between two symmetric date windows.

```sql
DECLARE recent_start_date DATE;
DECLARE prior_start_date DATE;
SET recent_start_date = DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY);
SET prior_start_date = DATE_SUB(recent_start_date, INTERVAL 7 DAY);

WITH RawData AS (
  SELECT
    customer_id,
    usage_date,
    revenue,
    usage_date >= recent_start_date as is_recent,
    usage_date >= prior_start_date AND usage_date < recent_start_date as is_prior
  FROM
    `concord-prod.service_cloudbi_reporting.revenue_daily`
  WHERE
    -- CRITICAL: Prune partitions
    partition_date >= prior_start_date
    AND usage_date >= prior_start_date
    -- Exclude internal/fraud
    AND NOT is_internal
    AND NOT is_fraud
    -- Target filters
    AND region = 'NORTHAM'
    AND sub_region = 'US Retail'
),

AggregatedPeriods AS (
  SELECT
    customer_id,
    SUM(IF(is_recent, revenue, 0)) as sum_recent_revenue,
    SUM(IF(is_prior, revenue, 0)) as sum_prior_revenue
  FROM
    RawData
  GROUP BY
    1
),

SubRegionTotalPrior AS (
  SELECT
    SUM(sum_prior_revenue) / 7.0 as total_prior_drr
  FROM
    AggregatedPeriods
),

CalculatedDRR AS (
  SELECT
    customer_id,
    sum_prior_revenue / 7.0 as drr_prior,
    sum_recent_revenue / 7.0 as drr_recent
  FROM
    AggregatedPeriods
)

SELECT
  c.customer_id,
  c.drr_prior,
  c.drr_recent,
  (c.drr_recent - c.drr_prior) as absolute_change,
  SAFE_DIVIDE(c.drr_recent - c.drr_prior, ABS(c.drr_prior)) * 100 as pct_change,
  SAFE_DIVIDE(c.drr_recent - c.drr_prior, t.total_prior_drr) * 100 as sub_region_impact_pct
FROM
  CalculatedDRR c
CROSS JOIN
  SubRegionTotalPrior t
ORDER BY
  absolute_change DESC; -- Rank by absolute change
```

---

## 2. Multi-Level Opportunities & Sales Play Join with Cryptographic Deduplication

This query unnessts product-level components but prevents ACV duplication using the MD5 cryptographic offset trick.

```sql
SELECT
  opportunities.opportunity_id  AS opportunities_opportunity_id,
  opportunities.opportunity_name  AS opportunities_opportunity_name,
  gcp_watermark_reporting.opportunity_id  AS gcp_watermark_reporting_opportunity_id,
  gcp_watermark_reporting.watermark_source  AS gcp_watermark_reporting_watermark_source,

  -- Cryptographic SUM(DISTINCT) deduplication of watermark
  ROUND(
    COALESCE(
      CAST(
        (
          SUM(DISTINCT
            (CAST(ROUND(COALESCE(gcp_watermark_reporting.watermark, 0) * 0.001, 9) AS NUMERIC) +
            (CAST(CAST(CONCAT('0x', SUBSTR(TO_HEX(MD5(CAST(gcp_watermark_reporting.opportunity_id AS STRING))), 1, 15)) AS INT64) AS NUMERIC) * 4294967296 +
             CAST(CAST(CONCAT('0x', SUBSTR(TO_HEX(MD5(CAST(gcp_watermark_reporting.opportunity_id AS STRING))), 16, 8)) AS INT64) AS NUMERIC)) * 0.000000001)
          )
          - SUM(DISTINCT
            (CAST(CAST(CONCAT('0x', SUBSTR(TO_HEX(MD5(CAST(gcp_watermark_reporting.opportunity_id AS STRING))), 1, 15)) AS INT64) AS NUMERIC) * 4294967296 +
             CAST(CAST(CONCAT('0x', SUBSTR(TO_HEX(MD5(CAST(gcp_watermark_reporting.opportunity_id AS STRING))), 16, 8)) AS INT64) AS NUMERIC)) * 0.000000001
        ) / 0.001 AS NUMERIC
      ), 0
    ), 6
  ) AS gcp_watermark_reporting_watermark,

  -- Summing component-level metrics directly
  COALESCE(SUM(CASE WHEN (gcp_watermark_reporting__detail__revenue_watermark__details__product_level_revenue.product = 'LOOKER') THEN (IFNULL(gcp_watermark_reporting__detail__revenue_watermark__details__product_level_revenue.revenue_components.sales_revenue, 0)) * 4 ELSE NULL END), 0) AS annualized_sales_revenue_looker,
  COALESCE(SUM(CASE WHEN (gcp_watermark_reporting__detail__revenue_watermark__details__product_level_revenue.product = 'APIGEE') THEN (IFNULL(gcp_watermark_reporting__detail__revenue_watermark__details__product_level_revenue.revenue_components.sales_revenue, 0)) * 4 ELSE NULL END), 0) AS annualized_sales_revenue_apigee

FROM `concord-prod.service_cloudbi.gcp_watermark_reporting`  AS gcp_watermark_reporting
LEFT JOIN UNNEST(gcp_watermark_reporting.detail.revenue_watermark.details.product_level_revenue) as gcp_watermark_reporting__detail__revenue_watermark__details__product_level_revenue
LEFT JOIN `concord-prod.service_cloudbi.opportunities_streaming` AS opportunities ON gcp_watermark_reporting.opportunity_id = opportunities.opportunity_id

WHERE gcp_watermark_reporting.customer.region = 'NORTHAM'
GROUP BY 1, 2, 3, 4
ORDER BY gcp_watermark_reporting_watermark DESC
LIMIT 1000;
```
