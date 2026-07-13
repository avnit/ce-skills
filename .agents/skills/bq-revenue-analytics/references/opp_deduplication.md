# Cryptographic Hash-Based SUM(DISTINCT) Deduplication Pattern

When joining opportunities to repeating child arrays (such as product-level revenue components or sales plays), the query creates a **one-to-many relationship**, causing the main opportunity metrics (like `incremental_acv` or `watermark`) to duplicate across rows.

## The Problem

- Standard `SUM(value)` will duplicate the metric for every child row, inflating the total.
- Standard `SUM(DISTINCT value)` is broken because if two different opportunities have the same contract value (e.g. both are exactly $\$100,000$), it will collapse them and only count $\$100,000$ once.

## The Solution

We add a unique, deterministic pseudo-random offset (derived from the opportunity's primary key `opportunity_id`) to the contract value.

1.  This makes the value unique to that opportunity ID.
2.  We perform the distinct sum of this composite value.
3.  We then subtract the sum of the distinct offsets to yield the exact true total.

## SQL Implementation

```sql
ROUND(
  COALESCE(
    CAST(
      (
        -- 1. SUM DISTINCT of (ACV value scaled + unique MD5 offset)
        SUM(DISTINCT
          (CAST(ROUND(COALESCE(opportunities.usd_gcp_incremental_acv, 0) * 0.001, 9) AS NUMERIC) +
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
) AS opportunities_total_gcp_incremental_acv
```

### Key Parameters:

- **Scale Factor (`0.001`):** Multiplied during addition, divided back at the end. This shifts the decimal place of the target currency value to keep it distinct from the integer-level offset values.
- **Hash Function (`MD5`):** Cryptographically generates a pseudo-random 128-bit hex string from the ID.
- **Offset calculation:** Substrings are extracted from the MD5 hex string, converted to integers (`INT64`), cast to `NUMERIC` values, and combined.
