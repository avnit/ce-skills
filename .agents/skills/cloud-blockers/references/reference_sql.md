# Reference SQL Queries for `cloud-blockers`

Production-grade GoogleSQL queries for PLX `ExecuteSql` targeting Cloud Blockers (CB), Customer Requests (CR), Buganizer, and Salesforce Opportunity/Workload entities.

## Baseline Cloud Blockers & Customer Requests Query

```sql
SET RequestOptions.requested_enable_feature = 'MIN_COMPLETION_RATIO';
SET QueryRequest.return_query_info = true;

WITH
  _0 AS (
    WITH
      cb AS (
        SELECT
          t.cb_issue_id,
          t.cb_title,
          t.cb_pm_resolution_status,
          t.pst_owning_product_group AS cb_pst_owning_product_group,
          t.pst_owning_execution_area AS cb_pst_owning_execution_area,
          t.pst_display_name AS cb_pst_display_name,
          a0_cr_detail_array.cr_issue_id,
        FROM
          cloud_blockers_data.prod.cloud_blockers_stack_ranking_report_view
            AS t,
          UNNEST(t.cr_detail_array) AS a0_cr_detail_array
      ),
      cr AS (
        SELECT
          cloud_blockers AS cb,
          cr_issues.issue_id AS cr_issue_id,
          custom_field_pst_id.value AS cr_pst_id,
          cr_issues.title AS cr_title,
          cr_issues.severity AS cr_severity,
          cr_issues.status AS cr_status,
          custom_fields.value AS cr_acct_opp_or_workload_id,
          CASE
            WHEN LEFT(custom_fields.value, 3) = 'aBJ' THEN 'Workload'
            WHEN LEFT(custom_fields.value, 3) = '006' THEN 'Opportunity'
            ELSE NULL
            END AS opp_or_workload,
          cr_issues.component_id AS cr_component_id,
          custom_fields.custom_field_id AS cr_custom_field_id,
          cr_issues.reporter_user.email AS reporter_user,
          DATE(TIMESTAMP_SECONDS(CAST(created_usecs / 1000000 AS INT64)))
            AS cr_created_date
        FROM buganizer.issuestatsfresh.latest AS cr_issues
        LEFT JOIN UNNEST(cr_issues.custom_field_values) AS custom_fields
          ON
            custom_fields.custom_field_id IN (
              601949,
              350603,
              429004,
              646798)
        LEFT JOIN
          UNNEST(cr_issues.parent_issue_id) AS parent_issue_id
        LEFT JOIN UNNEST(cr_issues.parent_issue_id) AS cloud_blockers
        LEFT JOIN
          UNNEST(cr_issues.custom_field_values) AS custom_field_pst_id
          ON
            custom_field_pst_id.custom_field_id IN (
              1248137,
              1248157)
        WHERE
          cr_issues.component_id IN (
            841988,
            882846,
            583217)
          AND custom_fields.custom_field_id
            = CASE
              WHEN cr_issues.component_id = 882846 THEN 646798
              WHEN cr_issues.component_id = 841988 THEN 601949
              WHEN cr_issues.component_id = 841988 THEN 429004
              ELSE 0
              END
      ),
      EMEA_Insights AS (
        SELECT DISTINCT
          cb.* EXCEPT (cr_issue_id),
          cr.* EXCEPT (cb, cr_component_id, cr_custom_field_id),
          DATE_DIFF(CURRENT_DATE(), cr.cr_created_date, DAY) AS cr_days_old,
          cr.reporter_user AS cr_reporter_user,
          COALESCE(o.stage_name, w.workload_details.workload_progress)
            AS opp_wl_stage,
          COALESCE(o.opportunity_name, w.workload_name) AS opp_wl_name,
          COALESCE(o.sfdc_account_id, w.sfdc_account_id) AS reporting_id,
          COALESCE(o.account_name, w.customer.account_name) AS account_name,
          COALESCE(o.sub_region, w.customer.sub_region) AS sub_region,
          COALESCE(o.region, w.customer.region) AS region,
        FROM cr
        LEFT JOIN cb
          ON cr.cr_issue_id = cb.cr_issue_id
        LEFT JOIN ceops.gcc_opportunities AS o
          ON o.opportunity_id = cr.cr_acct_opp_or_workload_id
        LEFT JOIN ceops.gcc_workloads AS w
          ON w.workload_id = cr.cr_acct_opp_or_workload_id
        ORDER BY 1 DESC
      ),
      gtm AS (
        SELECT *, REGEXP_EXTRACT(bug_link, r'\d+') AS cb_id
        FROM gcp_insights.cb_spr_rsr_gtm_data
      ),
      temp AS (
        SELECT *
        FROM
          gtm
        FULL OUTER JOIN EMEA_Insights
          ON (gtm.cb_id = CAST(EMEA_Insights.cb_issue_id AS STRING))
      ),
      stack_ranking_table AS (
        SELECT
          cb_issue_id AS cb_id_stack_ranking,
          cb_qualified_for_semester,
          cb_submission_intake_period,
          cb_committed_for_semester,
          cb_commitment_period,
          cb_request_type,
          cb_interlock_submission_period,
          cb_if_submitted_during_GTM_interlock,
          cb_delivery_date
        FROM cloud_blockers_data.prod.cloud_blockers_stack_ranking_report_view
      ),
      CR_DATA_DETAIL AS (
        SELECT
          entity_id.id AS entity_id,
          entity_id.type AS entity_type_id,
          display_name AS entity_display_name,
          description AS entity_description,
          gm_area,
          CASE
            WHEN
              (pnl_category_1 IS NULL OR pnl_category_1 = '')
              AND (pnl_category_2 IS NULL OR pnl_category_2 = '')
              AND (pnl_category_3 IS NULL OR pnl_category_3 = '')
              THEN []
            WHEN
              (pnl_category_1 IS NULL OR pnl_category_1 = '')
              AND (pnl_category_2 IS NULL OR pnl_category_2 = '')
              AND (pnl_category_3 IS NOT NULL AND pnl_category_3 != '')
              THEN [pnl_category_3]
            WHEN
              (pnl_category_1 IS NULL OR pnl_category_1 = '')
              AND (pnl_category_2 IS NOT NULL AND pnl_category_2 != '')
              AND (pnl_category_3 IS NULL OR pnl_category_3 = '')
              THEN [pnl_category_2]
            WHEN
              (pnl_category_1 IS NULL OR pnl_category_1 = '')
              AND (pnl_category_2 IS NOT NULL AND pnl_category_2 != '')
              AND (pnl_category_3 IS NOT NULL AND pnl_category_3 != '')
              THEN [pnl_category_2, pnl_category_3]
            WHEN
              (pnl_category_1 IS NOT NULL AND pnl_category_1 != '')
              AND (pnl_category_2 IS NULL OR pnl_category_2 = '')
              AND (pnl_category_3 IS NULL OR pnl_category_3 = '')
              THEN [pnl_category_1]
            WHEN
              (pnl_category_1 IS NOT NULL AND pnl_category_1 != '')
              AND (pnl_category_2 IS NULL OR pnl_category_2 = '')
              AND (pnl_category_3 IS NOT NULL AND pnl_category_3 != '')
              THEN [pnl_category_1, pnl_category_3]
            WHEN
              (pnl_category_1 IS NOT NULL AND pnl_category_1 != '')
              AND (pnl_category_2 IS NOT NULL AND pnl_category_2 != '')
              AND (pnl_category_3 IS NULL OR pnl_category_3 = '')
              THEN [pnl_category_1, pnl_category_2]
            ELSE [pnl_category_1, pnl_category_2, pnl_category_3]
            END AS pnl_categories_array,
          owning_super_product_area,
          owning_product_area,
          owning_product_group,
          owning_execution_area
        FROM rel360_platform.pst.v1.entities AS pst_entities
        WHERE entity_id.id IN (SELECT DISTINCT cr_pst_id FROM cr)
      ),
      pst_mapping AS (
        SELECT
          CR_DATA_DETAIL.entity_id AS pst_entity_id,
          CR_DATA_DETAIL.entity_display_name AS pst_display_name,
          CR_DATA_DETAIL.gm_area AS pst_gm_area,
          CR_DATA_DETAIL.pnl_categories_array,
          pst_entities_owning_super_product_area.display_name
            AS owning_super_product_area,
          pst_entities_owning_product_area.display_name
            AS pst_owning_product_area,
          pst_entities_owning_product_group.display_name
            AS pst_owning_product_group,
          pst_entities_owning_execution_area.display_name
            AS pst_owning_execution_area
        FROM CR_DATA_DETAIL
        LEFT JOIN
          rel360_platform.pst.v1.entities
            AS pst_entities_owning_super_product_area
          ON
            CR_DATA_DETAIL.owning_super_product_area
            = pst_entities_owning_super_product_area.entity_id.id
        LEFT JOIN
          rel360_platform.pst.v1.entities AS pst_entities_owning_product_area
          ON
            CR_DATA_DETAIL.owning_product_area
            = pst_entities_owning_product_area.entity_id.id
        LEFT JOIN
          rel360_platform.pst.v1.entities AS pst_entities_owning_product_group
          ON
            CR_DATA_DETAIL.owning_product_group
            = pst_entities_owning_product_group.entity_id.id
        LEFT JOIN
          rel360_platform.pst.v1.entities AS pst_entities_owning_execution_area
          ON
            CR_DATA_DETAIL.owning_execution_area
            = pst_entities_owning_execution_area.entity_id.id
      )
    SELECT
      *,
      IF(temp.cb_issue_id IS NULL, 'CR Pending Triage', 'CR Triaged') AS triaged
    FROM temp
    LEFT JOIN stack_ranking_table
      ON temp.cb_id = CAST(stack_ranking_table.cb_id_stack_ranking AS STRING)
    LEFT JOIN pst_mapping
      ON temp.cr_pst_id = pst_mapping.pst_entity_id
  ),
  _1 AS (
    SELECT
      concat(
        '[',
        CAST(cr_issue_id AS STRING),
        '](https://issuetracker.google.com/',
        CAST(cr_issue_id AS STRING),
        ')') AS __CR_Buganizer_Issue_ID__1,
      concat(
        '[',
        CAST(cr_issue_id AS STRING),
        '](https://cloudconnect.corp.google.com/admin/cloud-blockers?cr_issue_id=',
        CAST(cr_issue_id AS STRING),
        ')') AS __CR_Triage_Cloud_Connect_Admin_Link__1,
      cr_title AS __cr_title__1,
      CAST(cr_severity AS STRING) AS __cr_severity__1,
      cr_created_date AS __cr_created_date__1,
      cr_reporter_user AS __cr_reporter_user__1,
      cr_days_old AS __cr_days_old__1,
      triaged AS __triaged__2,
      opp_or_workload AS __opp_or_workload__1,
      concat(
        '[',
        CAST(cr_acct_opp_or_workload_id AS STRING),
        '](https://vector.lightning.force.com/',
        CAST(cr_acct_opp_or_workload_id AS STRING),
        ')') AS __Vector_Opp_Workload_ID_linked_to_CR__1,
      account_name AS __account_name__1,
      region AS __region__1,
      sub_region AS __sub_region__1,
      cb_title AS __cb_title__1,
      cb_pm_resolution_status AS __cb_pm_resolution_status__1,
      concat(
        '[',
        CAST(cb_issue_id AS STRING),
        '](https://issuetracker.google.com/',
        CAST(cb_issue_id AS STRING),
        ')') AS __CB_Buganizer_Issue_ID__1,
      cb_if_submitted_during_GTM_interlock
        AS __cb_if_submitted_during_GTM_interlock__1,
      cb_interlock_submission_period AS __cb_interlock_submission_period__1,
      cb_qualified_for_semester AS __cb_qualified_for_semester__1,
      cb_submission_intake_period AS __cb_submission_intake_period__1,
      cb_committed_for_semester AS __cb_committed_for_semester__1,
      cb_commitment_period AS __cb_commitment_period__1,
      cb_request_type AS __cb_request_type__1,
      region_name AS __region_name__1,
      owning_super_product_area AS __owning_super_product_area__1,
      pst_owning_product_group AS __pst_owning_product_group__1,
      pst_owning_execution_area AS __pst_owning_execution_area__1,
      pst_display_name AS __pst_display_name__1,
      assignee AS __assignee__1,
      cb_delivery_date AS __cb_delivery_date__2,
      launch_status AS __launch_status__1,
      actual_launch_date AS __actual_launch_date__1,
      status_summary AS __status_summary__1
    FROM _0 AS _t
    GROUP BY
      __CR_Buganizer_Issue_ID__1, __CR_Triage_Cloud_Connect_Admin_Link__1,
      __cr_title__1, __cr_severity__1, __cr_created_date__1,
      __cr_reporter_user__1, __cr_days_old__1, __triaged__2,
      __opp_or_workload__1, __Vector_Opp_Workload_ID_linked_to_CR__1,
      __account_name__1, __region__1, __sub_region__1, __cb_title__1,
      __cb_pm_resolution_status__1, __CB_Buganizer_Issue_ID__1,
      __cb_if_submitted_during_GTM_interlock__1,
      __cb_interlock_submission_period__1, __cb_qualified_for_semester__1,
      __cb_submission_intake_period__1, __cb_committed_for_semester__1,
      __cb_commitment_period__1, __cb_request_type__1, __region_name__1,
      __owning_super_product_area__1, __pst_owning_product_group__1,
      __pst_owning_execution_area__1, __pst_display_name__1, __assignee__1,
      __cb_delivery_date__2, __launch_status__1, __actual_launch_date__1,
      __status_summary__1
    ORDER BY __CR_Triage_Cloud_Connect_Admin_Link__1 DESC
    LIMIT 50
  )
SELECT * FROM _1
```
