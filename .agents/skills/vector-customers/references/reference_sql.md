# Reference SQL Queries for `vector_customers`

Production-grade GoogleSQL queries for PLX `ExecuteSql` targeting `gcc.vector_customers`.

---

## Query 1: Full Customer Account, Vector Link & Territory Summary

Lookup account details, direct Salesforce Vector link, segment, region, sub-region, NAL ID, NAL Name, and NAL Cluster for a given customer name:

```sql
SELECT
  reporting_id,
  CONCAT('https://vector.lightning.force.com/lightning/r/Account/', reporting_id, '/view') AS vector_url,
  core.account_name AS account_name,
  core.segment AS segment,
  core.nal_id AS nal_id,
  core.nal_name AS nal_name,
  core.nal_cluster AS nal_cluster,
  core.region AS region,
  core.sub_region AS sub_region,
  core.industry AS industry,
  core.is_digital_native AS is_digital_native
FROM gcc.vector_customers
WHERE LOWER(core.account_name) LIKE '%workday%'
ORDER BY core.account_name;
```

---

## Query 2: Unnested Account Team (FSR & Customer Engineer)

Extract the assigned Field Sales Representative (FSR) and Customer Engineer (CE) LDAPs for an account:

```sql
SELECT DISTINCT
  reporting_id,
  CONCAT('https://vector.lightning.force.com/lightning/r/Account/', reporting_id, '/view') AS vector_url,
  core.account_name AS account_name,
  core.nal_id AS nal_id,
  core.nal_name AS nal_name,
  core.nal_cluster AS nal_cluster,
  acc.primary_field_rep AS fsr_ldaps,
  acc.customer_engineer AS ce_ldaps
FROM gcc.vector_customers,
UNNEST(account_details) AS acc
WHERE LOWER(core.account_name) LIKE '%workday%';
```

---

## Query 3: Account Roster by NAL ID (with Cluster)

List all accounts assigned to a specific NAL ID with Vector links and NAL Cluster:

```sql
SELECT
  reporting_id,
  CONCAT('https://vector.lightning.force.com/lightning/r/Account/', reporting_id, '/view') AS vector_url,
  core.account_name AS account_name,
  core.segment AS segment,
  core.nal_name AS nal_name,
  core.nal_cluster AS nal_cluster,
  core.region AS region,
  core.sub_region AS sub_region,
  core.industry AS industry
FROM gcc.vector_customers
WHERE core.nal_id = 2507192445
ORDER BY core.account_name;
```

---

## Query 4: Account Roster by Cluster

List all accounts sharing the same NAL Cluster as a target reporting ID (e.g. `0014M00001h3l17QAA` / `West 4 (CL)`):

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

## Query 5: Digital Native Accounts in a Region

List all Digital Native accounts in a specific region with assigned NALs and Clusters:

```sql
SELECT
  reporting_id,
  CONCAT('https://vector.lightning.force.com/lightning/r/Account/', reporting_id, '/view') AS vector_url,
  core.account_name AS account_name,
  core.nal_id AS nal_id,
  core.nal_name AS nal_name,
  core.nal_cluster AS nal_cluster,
  core.sub_region AS sub_region
FROM gcc.vector_customers
WHERE core.is_digital_native = TRUE
  AND core.region = 'NORTHAM'
ORDER BY core.account_name
LIMIT 50;
```
