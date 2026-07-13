# Google Cloud Revenue & Sales BI Schema Reference

This reference documents the database locations, field types, and filter guidelines for Google Cloud sales reporting.

---

## 1. Revenue Metrics Taxonomy

Do not confuse different revenue classifications. Choose the correct metric field based on the reporting target:

| Metric Type                  | Description                                                | Key Column Path                                                  |
| :--------------------------- | :--------------------------------------------------------- | :--------------------------------------------------------------- |
| **Recognized Revenue (RVP)** | Recognized revenue according to financial ledger bookings. | `usd_revenue_metrics.rvp_revenue.rvp_revenue` (or `revenue_rvp`) |
| **Invoice / Sales Revenue**  | Invoiced consumption before ledger alignments.             | `usd_revenue_metrics.invoice_revenue.components.list_revenue`    |
| **Forecast Outlook (PBO)**   | Pipeline-Based Outlook (future incremental revenue).       | `pbo_metrics.net_incremental_revenue`                            |
| **Looker Special Quota**     | Quota targets set specifically for Looker.                 | `revenue_metrics.special_products_quota.looker_quota`            |
| **Apigee Special Quota**     | Quota targets set specifically for Apigee.                 | `revenue_metrics.special_products_quota.apigee_quota`            |
| **Sales Revenue**            | Quota-aligned booking metrics.                             | `usd_revenue_metrics.sales_revenue.sales_revenue`                |

---

## 2. Product & SKU Hierarchy Navigation

We track products using two distinct trees: **GTM Product Hierarchy** (sales-focused) and **Finance Product Hierarchy** (ledger-focused).

### GTM Product Hierarchy (Level 1 to 7)

Use this when segmenting by sales divisions or products (e.g. Workspace, Cloud AI, Analytics, AI):

- **L1 (GTM Division):** `product_details.gtm_product_hierarchy.gtm_product_level_1` (e.g., `'CLOUD'`, `'GEO'`)
- **L5 (Product Group):** `product_details.gtm_product_hierarchy.gtm_product_level_5` (e.g., `'Analytics'`, `'Build with AI'`, `'Security'`, `'Workspace'`)
- **L7 (Product Segment):** `product_details.gtm_product_hierarchy.gtm_product_level_7`

### Standard Exclusions (Gotchas)

Production dashboards apply these strict exclusions to keep reports clean:

1.  **Excluding Security & Workspace from GCP Infra:**
    Workspace and Security have independent pipelines and are usually excluded from core GCP infra dashboards:
    ```sql
    WHERE gtm_product_level_5 NOT IN ('Security', 'Workspace')
    ```
2.  **Excluding Third-Party Marketplace Spend:**
    Third-party marketplace transactions represent pass-through billing and are excluded to avoid gross-margin skew:
    ```sql
    WHERE gtm_product_level_7 NOT IN ('Marketplace Anthropic', 'Marketplace Oracle', 'Marketplace Other')
    ```

---

## 3. Customer, Segment & Territory Dimensions

To filter by geographies, sales divisions, or customer size:

- **Regions:** `customer_details.region` or `customer.region` (e.g., `'NORTHAM'`, `'EMEA'`, `'APAC'`, `'JAPAN'`, `'LATAM'`)
- **Sub-regions:** `customer_details.sub_region` or `nal_details.sub_region` (e.g., `'US Retail'`, `'UK & Ireland'`)
- **Sales Segments:** `customer_details.segment` or `segment` (e.g., `'Enterprise'`, `'Select'`, `'Corporate'`, `'Startup'`)
  - _Note:_ Exclude self-service or micro-accounts in enterprise reports using: `WHERE segment <> 'Scaled'`
- **Channels:** `channel_details.channel` (exclude resellers via: `WHERE channel <> 'Reseller'`)

---

## 4. Integration Join Rules (Table Mappings)

When joining transaction records (revenue or bookings) to sales territories, opportunities, or reps, use these standard join paths:

- **Named Account List (NAL):** Maps billing accounts to sales territories.
  ```sql
  FROM `concord-prod.service_cloudbi_reporting.revenue_daily` AS r
  LEFT JOIN `concord-prod.service_cloudbi.nals` AS n ON r.customer.nal_id = n.nal_details.nal_id
  ```
- **Sales Rep mapping:**
  ```sql
  FROM `concord-prod.service_cloudbi.opportunities_streaming` AS o
  LEFT JOIN `concord-prod.service_cloudbi.persons` AS p ON o.owner_id = p.person_id
  ```
