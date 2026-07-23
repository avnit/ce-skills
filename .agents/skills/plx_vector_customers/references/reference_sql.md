# Reference SQL Queries for `vector_customers`

Production-grade GoogleSQL queries for PLX `ExecuteSql` targeting `gcc.vector_customers`.

---

## Query 1: Full Customer Account & Territory Summary
Lookup account details, segment, region, sub-region, and NAL for a given customer name:

```sql
SELECT
  reporting_id,
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
  core.account_name AS account_name,
  core.nal_id AS nal_id,
  core.nal_name AS nal_name,
  acc.primary_field_rep AS fsr_ldaps,
  acc.customer_engineer AS ce_ldaps
FROM gcc.vector_customers,
UNNEST(account_details) AS acc
WHERE LOWER(core.account_name) LIKE '%workday%';
```

---

## Query 3: Account Roster by NAL ID
List all accounts assigned to a specific NAL ID:

```sql
SELECT
  reporting_id,
  core.account_name AS account_name,
  core.segment AS segment,
  core.region AS region,
  core.sub_region AS sub_region,
  core.industry AS industry
FROM gcc.vector_customers
WHERE core.nal_id = 2507192445
ORDER BY core.account_name;
```

---

## Query 4: Digital Native Accounts in a Region
List all Digital Native accounts in a specific region with assigned NALs:

```sql
SELECT
  reporting_id,
  core.account_name AS account_name,
  core.nal_id AS nal_id,
  core.nal_name AS nal_name,
  core.sub_region AS sub_region
FROM gcc.vector_customers
WHERE core.is_digital_native = TRUE
  AND core.region = 'NORTHAM'
ORDER BY core.account_name
LIMIT 50;
```
