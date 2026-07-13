# Salesforce Vector Deep Links & Report Formatting Guide

This guide details how to construct direct clickable **Salesforce Vector URLs** in BigQuery SQL queries and how to format report outputs as either Markdown or HTML.

---

## 1. Salesforce Vector URL Construction Patterns

In SQL queries, build deep-link URLs to Vector entities using `CONCAT()`:

| Entity Type             | URL Template                                                                 | BigQuery SQL Expression                                                                                      |
| :---------------------- | :--------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------- |
| **Expert Request (ER)** | `https://vector.lightning.force.com/lightning/r/Expert_Request__c/{id}/view` | `CONCAT('https://vector.lightning.force.com/lightning/r/Expert_Request__c/', er.expert_request_id, '/view')` |
| **Account**             | `https://vector.lightning.force.com/lightning/r/Account/{id}/view`           | `CONCAT('https://vector.lightning.force.com/lightning/r/Account/', er.reporting_id, '/view')`                |
| **Workload**            | `https://vector.lightning.force.com/lightning/r/Workload__c/{id}/view`       | `CONCAT('https://vector.lightning.force.com/lightning/r/Workload__c/', er.workload_id, '/view')`             |
| **Opportunity**         | `https://vector.lightning.force.com/lightning/r/Opportunity/{id}/view`       | `CONCAT('https://vector.lightning.force.com/lightning/r/Opportunity/', er.opportunity_id, '/view')`          |

---

## 2. SQL Helper Snippet for Hyperlinks

### Markdown Format Snippet (in SQL):

```sql
CONCAT('[', er.name, '](https://vector.lightning.force.com/lightning/r/Expert_Request__c/', er.expert_request_id, '/view)') AS er_markdown_link,
CONCAT('[', er.customer.account_name, '](https://vector.lightning.force.com/lightning/r/Account/', er.reporting_id, '/view)') AS account_markdown_link,
CONCAT('[', o.opportunity_name, '](https://vector.lightning.force.com/lightning/r/Opportunity/', o.opportunity_id, '/view)') AS opp_markdown_link,
CONCAT('[', w.workload_name, '](https://vector.lightning.force.com/lightning/r/Workload__c/', w.workload_id, '/view)') AS workload_markdown_link
```

### HTML Format Snippet (in SQL):

```sql
CONCAT('<a href="https://vector.lightning.force.com/lightning/r/Expert_Request__c/', er.expert_request_id, '/view" target="_blank">', er.name, '</a>') AS er_html_link,
CONCAT('<a href="https://vector.lightning.force.com/lightning/r/Account/', er.reporting_id, '/view" target="_blank">', er.customer.account_name, '</a>') AS account_html_link
```

---

## 3. Sample Markdown Report Output Format

```markdown
## 📋 Expert Requests Engagement Report

| Customer Account                                                                                        | ER Name                                                                                                                   | Opportunity                                                                                                      | Workload                                                                                                        |   Status    |
| :------------------------------------------------------------------------------------------------------ | :------------------------------------------------------------------------------------------------------------------------ | :--------------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------- | :---------: |
| [PayPal Holdings, Inc.](https://vector.lightning.force.com/lightning/r/Account/001Kf000013etxQIAQ/view) | [Dataproc Optimization Support](https://vector.lightning.force.com/lightning/r/Expert_Request__c/aAuKf0000004MMaKAM/view) | [PayPal Core Data Migration](https://vector.lightning.force.com/lightning/r/Opportunity/006Kf00000KOekfIAD/view) | [BigQuery Modernization](https://vector.lightning.force.com/lightning/r/Workload__c/aBJKf000009eKriOAE/view)    | `Completed` |
| [Target Corporation](https://vector.lightning.force.com/lightning/r/Account/001Kf000013etxQIAQ/view)    | [Infra AI Capacity Assessment](https://vector.lightning.force.com/lightning/r/Expert_Request__c/aAuKf0000004MMaKAM/view)  | [Target Retail AI Search](https://vector.lightning.force.com/lightning/r/Opportunity/006Kf00000KOekfIAD/view)    | [Vertex AI Search Workload](https://vector.lightning.force.com/lightning/r/Workload__c/aBJKf000009eKriOAE/view) | `Assigned`  |
```

---

## 4. Sample HTML Report Output Format

```html
<div class="report-container">
  <h3>📋 Expert Requests Engagement Executive Summary</h3>
  <table
    class="styled-table"
    style="width: 100%; border-collapse: collapse; font-family: sans-serif;"
  >
    <thead>
      <tr style="background-color: #1a73e8; color: white; text-align: left;">
        <th style="padding: 10px;">Customer Account</th>
        <th style="padding: 10px;">Expert Request</th>
        <th style="padding: 10px;">Opportunity</th>
        <th style="padding: 10px;">Workload</th>
        <th style="padding: 10px;">Status</th>
      </tr>
    </thead>
    <tbody>
      <tr style="border-bottom: 1px solid #dddddd;">
        <td style="padding: 10px;">
          <a
            href="https://vector.lightning.force.com/lightning/r/Account/001Kf000013etxQIAQ/view"
            target="_blank"
            style="color: #1a73e8; font-weight: bold;"
            >PayPal Holdings, Inc.</a
          >
        </td>
        <td style="padding: 10px;">
          <a
            href="https://vector.lightning.force.com/lightning/r/Expert_Request__c/aAuKf0000004MMaKAM/view"
            target="_blank"
            style="color: #1a73e8;"
            >Dataproc Optimization Support</a
          >
        </td>
        <td style="padding: 10px;">
          <a
            href="https://vector.lightning.force.com/lightning/r/Opportunity/006Kf00000KOekfIAD/view"
            target="_blank"
            style="color: #1a73e8;"
            >PayPal Core Data Migration</a
          >
        </td>
        <td style="padding: 10px;">
          <a
            href="https://vector.lightning.force.com/lightning/r/Workload__c/aBJKf000009eKriOAE/view"
            target="_blank"
            style="color: #1a73e8;"
            >BigQuery Modernization</a
          >
        </td>
        <td style="padding: 10px;">
          <span
            style="background-color: #e6f4ea; color: #137333; padding: 4px 8px; border-radius: 4px; font-weight: bold;"
            >Completed</span
          >
        </td>
      </tr>
    </tbody>
  </table>
</div>
```
