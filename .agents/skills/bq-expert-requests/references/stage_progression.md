# Opportunity Stage Progression & Deduplication Logic

This guide details advanced analytical techniques for Expert Request (ER) queries, including tracking deal progression post-engagement and avoiding metric inflation on one-to-many joins.

---

## 1. Opportunity Stage Progression Tracking

A key metric for sales and CE leadership is **ER-Driven Stage Progression** (measuring deals that advanced to Stage 3 Proposal/Negotiation or Stage 4 Implementation after an Expert Request was initiated).

### Logic Requirements:

1. Capture the opportunity stage **at the exact time the ER was created**.
2. Compare it to the **current opportunity stage**.
3. Require that `current_stage >= '03 - Proposal/Negotiation'` AND `stage_at_er_creation < '03 - Proposal/Negotiation'`.

### SQL Implementation Snippet:

```sql
WITH er_with_stage_at_creation AS (
  SELECT
    er.expert_request_id,
    er.opportunity_id,
    er.created_date AS er_created_date,
    o.stage_name AS current_stage_name,
    o.usd_acv,

    -- Extract exact completion date from field history
    (SELECT DATE(MIN(start_time))
     FROM UNNEST(er.expert_request_field_history.status_field_history)
     WHERE value = 'Completed') AS er_completed_date

  FROM `concord-prod.service_cloudbi.expert_requests` AS er
  LEFT JOIN `concord-prod.service_cloudbi.opportunities_streaming` AS o
         ON er.opportunity_id = o.opportunity_id
  WHERE er.created_date >= DATE_TRUNC(CURRENT_DATE('UTC'), YEAR)
    AND er.opportunity_id IS NOT NULL
)

SELECT
  expert_request_id,
  opportunity_id,
  current_stage_name,
  -- Identify if the deal is currently in Stage 3 or higher
  CASE WHEN current_stage_name IN ('03 - Proposal/Negotiation', '04 - Migration/Implementation', 'Closed Won')
       THEN 1 ELSE 0
  END AS is_progressed_to_stage3
FROM er_with_stage_at_creation;
```

---

## 2. Cryptographic MD5 Deduplication for ER ACV/ARR

Because a single opportunity or workload can have multiple Expert Requests attached to it, joining `expert_requests` to `opportunities_streaming` creates a **one-to-many relationship**.

- **The Problem:**
  - `SUM(o.usd_acv)` double-counts the opportunity value for every attached ER.
  - `SUM(DISTINCT o.usd_acv)` breaks if two distinct deals happen to have the exact same ACV (e.g., both are $\$50,000$).
- **The Solution:**
  Apply the cryptographic MD5 hash-offset deduplication formula to uniquely scale each ACV/ARR value by adding a deterministic pseudo-random offset derived from `opportunity_id` or `expert_request_id`:

```sql
ROUND(
  COALESCE(
    CAST(
      (
        -- 1. SUM DISTINCT of (ACV value scaled + unique MD5 offset)
        SUM(DISTINCT
          (CAST(ROUND(COALESCE(opportunities.usd_acv, 0) * 0.001, 9) AS NUMERIC) +
          (CAST(CAST(CONCAT('0x', SUBSTR(TO_HEX(MD5(CAST(opportunities.opportunity_id AS STRING))), 1, 15)) AS INT64) AS NUMERIC) * 4294967296 +
           CAST(CAST(CONCAT('0x', SUBSTR(TO_HEX(MD5(CAST(opportunities.opportunity_id AS STRING))), 16, 8)) AS INT64) AS NUMERIC)) * 0.000000001)
        )
        -- 2. Subtract SUM DISTINCT of the unique MD5 offsets alone
        - SUM(DISTINCT
          (CAST(CAST(CONCAT('0x', SUBSTR(TO_HEX(MD5(CAST(opportunities.opportunity_id AS STRING))), 1, 15)) AS INT64) AS NUMERIC) * 4294967296 +
           CAST(CAST(CONCAT('0x', SUBSTR(TO_HEX(MD5(CAST(opportunities.opportunity_id AS STRING))), 16, 8)) AS INT64) AS NUMERIC)) * 0.000000001
      ) / 0.001 AS NUMERIC
    ), 0
  ), 6
) AS total_deduplicated_acv
```
