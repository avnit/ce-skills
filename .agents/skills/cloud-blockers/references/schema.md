# Cloud Blockers & Customer Requests (CR) Schema Reference

Overview of datasets, views, Buganizer components, and joined entities powering the `cloud-blockers` skill via PLX `ExecuteSql`.

## Core Datasets & Views

| Dataset / Table Name                                                | Source / Engine  | Description                                                                                                    |
| :------------------------------------------------------------------ | :--------------- | :------------------------------------------------------------------------------------------------------------- |
| `cloud_blockers_data.prod.cloud_blockers_stack_ranking_report_view` | BigQuery / PLX   | Production view for Cloud Blocker (CB) stack ranking, semester commitments, intake periods, and delivery dates |
| `buganizer.issuestatsfresh.latest`                                  | Buganizer / F1   | Real-time Buganizer issue metadata for Customer Requests (CR)                                                  |
| `ceops.gcc_opportunities`                                           | Salesforce / PLX | Google Cloud Sales Opportunities (linked via SFDC `006...` IDs)                                                |
| `ceops.gcc_workloads`                                               | Salesforce / PLX | Google Cloud Customer Workloads (linked via SFDC `aBJ...` IDs)                                                 |
| `gcp_insights.cb_spr_rsr_gtm_data`                                  | Insights / PLX   | Go-To-Market (GTM) interlock and Cloud Blocker correlation dataset                                             |
| `rel360_platform.pst.v1.entities`                                   | REL360 / PLX     | Product & Solutions Taxonomy (PST) mapping for Product Areas and Execution Areas                               |

## Buganizer Component IDs & Custom Fields

### CR Component IDs

- `841988` (Product & Feature Gaps)
- `882846` (Cloud Blockers Intake)
- `583217` (Customer Escalations / Blockers)

### Custom Field IDs

- `601949` / `646798` / `429004`: Linked Opportunity or Workload SFDC ID (`006...` or `aBJ...`)
- `1248137` / `1248157`: Product Solutions Taxonomy (PST) Entity ID

## Key Output Fields

| Output Field Name                          | Type                | Description                                                                                                   |
| :----------------------------------------- | :------------------ | :------------------------------------------------------------------------------------------------------------ |
| `__CR_Buganizer_Issue_ID__1`               | `STRING (Markdown)` | Hyperlinked CR Buganizer Issue (`https://issuetracker.google.com/<id>`)                                       |
| `__CR_Triage_Cloud_Connect_Admin_Link__1`  | `STRING (Markdown)` | Cloud Connect Admin Triage URL (`https://cloudconnect.corp.google.com/admin/cloud-blockers?cr_issue_id=<id>`) |
| `__cr_title__1`                            | `STRING`            | Customer Request Title                                                                                        |
| `__cr_severity__1`                         | `STRING`            | Issue Severity (`S0`, `S1`, `S2`, `S3`, `S4`)                                                                 |
| `__cr_created_date__1`                     | `DATE`              | Date CR was logged                                                                                            |
| `__cr_reporter_user__1`                    | `STRING`            | Reporter LDAP / Email                                                                                         |
| `__cr_days_old__1`                         | `INT64`             | Days elapsed since creation                                                                                   |
| `__triaged__2`                             | `STRING`            | Triage Status (`CR Triaged` vs `CR Pending Triage`)                                                           |
| `__opp_or_workload__1`                     | `STRING`            | Linked Entity Type (`Opportunity` vs `Workload`)                                                              |
| `__Vector_Opp_Workload_ID_linked_to_CR__1` | `STRING (Markdown)` | Hyperlinked SFDC Vector URL (`https://vector.lightning.force.com/<id>`)                                       |
| `__account_name__1`                        | `STRING`            | Customer Account Name                                                                                         |
| `__region__1` / `__sub_region__1`          | `STRING`            | Sales Region & Sub-region                                                                                     |
| `__cb_title__1`                            | `STRING`            | Linked Cloud Blocker Title                                                                                    |
| `__cb_pm_resolution_status__1`             | `STRING`            | PM Resolution Status                                                                                          |
| `__CB_Buganizer_Issue_ID__1`               | `STRING (Markdown)` | Hyperlinked Cloud Blocker Buganizer Issue                                                                     |
| `__pst_owning_product_group__1`            | `STRING`            | Owning Product Group (e.g. `TPUs`, `Gemini Enterprise`, `Cloud Run`)                                          |
| `__pst_owning_execution_area__1`           | `STRING`            | Owning Execution Area                                                                                         |
| `__cb_delivery_date__2`                    | `DATE`              | Committed Delivery Date                                                                                       |
