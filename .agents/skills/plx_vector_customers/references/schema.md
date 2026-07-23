# PLX Vector Customers Table & Proto Schemas

## Table Overview
* **Datahub / PLX Name:** `gcc.vector_customers`
* **Underlying Source:** `concord-prod.service_cloudbi.vector_customers`
* **Primary Key:** `reporting_id` (SFDC Vector Parent Account ID)

---

## High-Level Fields

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `reporting_id` | `STRING` | SFDC Vector Parent Account Reporting ID (e.g. `0014M00001hmLq3QAE`) |
| `core` | `PROTO<CoreDetails>` | Core territory, NAL, industry, and segment attributes |
| `account_details` | `ARRAY<PROTO<AccountDetails>>` | Detailed account assignments, FSRs, CEs, and child account info |
| `specialist_hierarchies` | `PROTO<SpecialistHierarchies>` | Workspace, Security, and Geo specialist assignments |
| `partner_core` | `PROTO<PartnerCoreDetails>` | Partner core details (if applicable) |
| `access_key_hierarchy` | `STRING` | Pipe-separated list of LDAP users with data access |

---

## Proto: `cloud.sales.bi.pipelines.entities.VectorParentCustomers.CoreDetails`

| Field | Type | Description |
| :--- | :--- | :--- |
| `account_name` | `STRING` | Name of parent Vector account |
| `segment` | `STRING` | Customer segment (`Enterprise`, `Corporate`, `Select`, `Scaled`) |
| `nal_id` | `INT64` | Prime NAL (Named Account List) ID |
| `nal_name` | `STRING` | Prime NAL Name |
| `nal_cluster` | `STRING` | NAL Cluster designation |
| `region` | `STRING` | Sales Region (`NORTHAM`, `EMEA`, `LATAM`, `APAC`, `JAPAN`, `PUBLIC SECTOR`) |
| `sub_region` | `STRING` | Sub-region |
| `super_region` | `STRING` | `Americas`, `International`, or `Other` |
| `micro_region` | `STRING` | Micro-region classification |
| `industry` | `STRING` | Industry sector (e.g. `Software & Internet`, `Retail & Consumer`) |
| `sub_industry` | `STRING` | Sub-industry classification |
| `is_digital_native` | `BOOL` | `TRUE` if account is a Digital Native customer |
| `is_lighthouse` | `BOOL` | `TRUE` if account is flagged as a lighthouse account |

---

## Proto: `cloud.sales.bi.pipelines.entities.VectorParentCustomers.AccountDetails`

| Field | Type | Description |
| :--- | :--- | :--- |
| `sfdc_account_id` | `STRING` | SFDC Account ID |
| `primary_field_rep` | `ARRAY<STRING>` | List of Field Sales Representative (FSR) LDAPs |
| `customer_engineer` | `ARRAY<STRING>` | List of Customer Engineer (CE / AI Specialist) LDAPs |
| `assignments` | `ARRAY<PROTO>` | Granular role assignment structures |
| `is_isv` | `BOOL` | `TRUE` if account is an Independent Software Vendor (ISV) |
