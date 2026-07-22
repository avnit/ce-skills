# Expert Requests (ER) SQL Reference Templates & Output Formats

This document provides ready-to-use production SQL query templates with **Salesforce Vector Deep Links** (Account, ER, Opportunity, Workload) and sample Markdown/HTML report output formats.

---

## Template 1: CE Rep Productivity & Activity Leaderboard (with Vector Links)

Consolidates completed vs. in-flight Expert Requests, attached ACV/ARR, and engaged account counts by Customer Engineer (rep LDAP).

### SQL Query:

```sql
WITH ce_assignments AS (
  SELECT
    rep_ldap,
    rep_role,
    manager_user_name,
    pod_sub_region,
    specialization,
    primary_practice
  FROM `concord-prod.service_cloudbi.ce_rep_details`
),

expert_requests_owned AS (
  SELECT
    er.expert_request_id,
    er.name AS er_name,
    er.owner_user_name AS rep_ldap,
    er.status,
    er.created_date,
    er.opportunity_id,
    er.workload_id,
    er.reporting_id,
    er.customer.account_name,
    w.metrics.annual_gross_revenue AS workload_arr,
    o.usd_acv AS opportunity_acv,

    -- Salesforce Vector Links
    CONCAT('https://vector.lightning.force.com/lightning/r/Expert_Request__c/', er.expert_request_id, '/view') AS er_vector_url,
    CONCAT('https://vector.lightning.force.com/lightning/r/Account/', er.reporting_id, '/view') AS account_vector_url
  FROM `concord-prod.service_cloudbi.expert_requests` AS er
  LEFT JOIN `concord-prod.service_cloudbi.opportunities_streaming` AS o
         ON er.opportunity_id = o.opportunity_id
  LEFT JOIN `concord-prod.service_cloudbi.gcc_workloads_streaming` AS w
         ON er.workload_id = w.workload_id
  WHERE er.created_date >= DATE_TRUNC(CURRENT_DATE('UTC'), YEAR)
    AND er.status IN ('New', 'Accepted', 'Assigned', 'Completed')
)

SELECT
  c.rep_ldap,
  c.rep_role,
  c.manager_user_name,
  c.pod_sub_region,
  c.specialization,

  -- Completed ER metrics
  COUNT(DISTINCT CASE WHEN er.status = 'Completed' THEN er.expert_request_id END) AS completed_ers_count,
  COALESCE(SUM(CASE WHEN er.status = 'Completed' THEN er.workload_arr ELSE 0 END), 0) AS completed_er_arr,

  -- In-Flight ER metrics
  COUNT(DISTINCT CASE WHEN er.status IN ('New', 'Accepted', 'Assigned') THEN er.expert_request_id END) AS in_flight_ers_count,

  -- Account Engagement
  COUNT(DISTINCT er.reporting_id) AS total_engaged_accounts

FROM ce_assignments c
LEFT JOIN expert_requests_owned er ON c.rep_ldap = er.rep_ldap
GROUP BY 1, 2, 3, 4, 5
ORDER BY completed_ers_count DESC;
```

### Sample Output (Markdown Format):

```markdown
| Rep LDAP | Role          | Manager     | Completed ERs | In-Flight ERs | Engaged Accounts | Completed ARR |
| :------- | :------------ | :---------- | :-----------: | :-----------: | :--------------: | :-----------: |
| `jdoe`   | CE Specialist | `mcolumbus` |      14       |       3       |        12        |  $4,250,000   |
| `asmith` | Field CE      | `alanpoole` |      11       |       5       |        9         |  $2,800,000   |
```

---

## Template 2: Opportunity Stage Progression Tracker (with Vector Deep Links)

Tracks active deals engaged by Expert Requests that progressed to Stage 3 Proposal/Negotiation or Stage 4, generating direct links to the Opportunity, Workload, and ER in Salesforce Vector.

### SQL Query:

```sql
WITH er_deals AS (
  SELECT
    er.expert_request_id,
    er.name AS er_name,
    er.owner_user_name AS er_owner_ldap,
    er.created_date AS er_created_date,
    er.reporting_id,
    er.customer.account_name,
    o.opportunity_id,
    o.opportunity_name,
    o.stage_name AS current_stage_name,
    o.usd_acv AS opportunity_acv,
    w.workload_id,
    w.workload_name,

    -- Salesforce Vector Links
    CONCAT('https://vector.lightning.force.com/lightning/r/Expert_Request__c/', er.expert_request_id, '/view') AS er_url,
    CONCAT('https://vector.lightning.force.com/lightning/r/Account/', er.reporting_id, '/view') AS account_url,
    CONCAT('https://vector.lightning.force.com/lightning/r/Opportunity/', o.opportunity_id, '/view') AS opp_url,
    CONCAT('https://vector.lightning.force.com/lightning/r/Workload__c/', w.workload_id, '/view') AS workload_url

  FROM `concord-prod.service_cloudbi.expert_requests` AS er
  INNER JOIN `concord-prod.service_cloudbi.opportunities_streaming` AS o
          ON er.opportunity_id = o.opportunity_id
  LEFT JOIN `concord-prod.service_cloudbi.gcc_workloads_streaming` AS w
         ON er.workload_id = w.workload_id
  WHERE er.created_date >= DATE_TRUNC(CURRENT_DATE('UTC'), YEAR)
    AND o.customer_details.region = 'NORTHAM'
)

SELECT
  reporting_id,
  account_name,
  account_url,
  opportunity_id,
  opportunity_name,
  opp_url,
  expert_request_id,
  er_name,
  er_url,
  workload_id,
  workload_name,
  workload_url,
  current_stage_name,

  CASE WHEN current_stage_name IN ('03 - Proposal/Negotiation', '04 - Migration/Implementation', 'Closed Won')
       THEN 'Progressed (Stage 3+)'
       ELSE 'Early Stage (0-2)'
  END AS progression_status

FROM er_deals
ORDER BY er_created_date DESC;
```

### Sample Output (Markdown Report Format):

```markdown
## 🚀 Opportunity Stage Progression Report

| Customer Account                                                                                        | Opportunity                                                                                                      | Expert Request                                                                                                            | Workload                                                                                                        |             Stage             |      Progression Status      |
| :------------------------------------------------------------------------------------------------------ | :--------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------ | :-------------------------------------------------------------------------------------------------------------- | :---------------------------: | :--------------------------: |
| [PayPal Holdings, Inc.](https://vector.lightning.force.com/lightning/r/Account/001Kf000013etxQIAQ/view) | [PayPal Core Data Migration](https://vector.lightning.force.com/lightning/r/Opportunity/006Kf00000KOekfIAD/view) | [Dataproc Optimization Support](https://vector.lightning.force.com/lightning/r/Expert_Request__c/aAuKf0000004MMaKAM/view) | [BigQuery Modernization](https://vector.lightning.force.com/lightning/r/Workload__c/aBJKf000009eKriOAE/view)    |  `03 - Proposal/Negotiation`  | 🟢 **Progressed (Stage 3+)** |
| [Target Corporation](https://vector.lightning.force.com/lightning/r/Account/001Kf000013etxQIAQ/view)    | [Target Retail AI Search](https://vector.lightning.force.com/lightning/r/Opportunity/006Kf00000KOekfIAD/view)    | [Infra AI Capacity Assessment](https://vector.lightning.force.com/lightning/r/Expert_Request__c/aAuKf0000004MMaKAM/view)  | [Vertex AI Search Workload](https://vector.lightning.force.com/lightning/r/Workload__c/aBJKf000009eKriOAE/view) | `02 - Tech Eval/Solution Dev` |   🟡 **Early Stage (0-2)**   |
```

### Sample Output (HTML Report Format):

```html
<div
  class="report-card"
  style="padding: 16px; font-family: Roboto, sans-serif; background: #ffffff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.12);"
>
  <h3 style="margin-top:0; color: #202124;">
    🚀 Opportunity Stage Progression Summary
  </h3>
  <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
    <thead>
      <tr
        style="background: #f1f3f4; color: #3c4043; border-bottom: 2px solid #dadce0; text-align: left;"
      >
        <th style="padding: 10px;">Customer Account</th>
        <th style="padding: 10px;">Opportunity</th>
        <th style="padding: 10px;">Expert Request</th>
        <th style="padding: 10px;">Stage</th>
        <th style="padding: 10px;">Status</th>
      </tr>
    </thead>
    <tbody>
      <tr style="border-bottom: 1px solid #e8eaed;">
        <td style="padding: 10px;">
          <a
            href="https://vector.lightning.force.com/lightning/r/Account/001Kf000013etxQIAQ/view"
            target="_blank"
            style="color: #1a73e8; text-decoration: none; font-weight: 500;"
            >PayPal Holdings, Inc.</a
          >
        </td>
        <td style="padding: 10px;">
          <a
            href="https://vector.lightning.force.com/lightning/r/Opportunity/006Kf00000KOekfIAD/view"
            target="_blank"
            style="color: #1a73e8; text-decoration: none;"
            >PayPal Core Data Migration</a
          >
        </td>
        <td style="padding: 10px;">
          <a
            href="https://vector.lightning.force.com/lightning/r/Expert_Request__c/aAuKf0000004MMaKAM/view"
            target="_blank"
            style="color: #1a73e8; text-decoration: none;"
            >Dataproc Optimization Support</a
          >
        </td>
        <td style="padding: 10px;">Stage 3</td>
        <td style="padding: 10px;">
          <span
            style="background: #e6f4ea; color: #137333; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: 500;"
            >Progressed</span
          >
        </td>
      </tr>
    </tbody>
  </table>
</div>
```
