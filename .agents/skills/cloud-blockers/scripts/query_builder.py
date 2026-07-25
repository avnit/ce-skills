#!/usr/bin/env python3
"""Query builder class for constructing filtered Cloud Blocker & Customer Request GoogleSQL queries.
"""

from sql_template import (
  BASE_QUERY_TEMPLATE,
  COMPONENT_CLOUD_BLOCKERS_INTAKE,
  COMPONENT_CUSTOMER_ESCALATIONS,
  COMPONENT_PRODUCT_FEATURE_GAPS,
  CUSTOM_FIELD_PST_ID_1,
  CUSTOM_FIELD_PST_ID_2,
  CUSTOM_FIELD_SFDC_OPP_1,
  CUSTOM_FIELD_SFDC_OPP_2,
  CUSTOM_FIELD_SFDC_OPP_3,
  CUSTOM_FIELD_SFDC_OPP_4,
)


class CloudBlockerQueryBuilder:
  """Builds filtered GoogleSQL queries for PLX F1 execution."""

  def __init__(self, limit=500):
    self.limit = limit

  def build_where_clause(self, args):
    conditions = []

    if getattr(args, "account", None):
      account_clean = args.account.replace("'", "\\'").strip("'\"")
      conditions.append(
          f"(LOWER(account_name) LIKE '%{account_clean.lower()}%' OR"
          f" LOWER(cr_title) LIKE '%{account_clean.lower()}%')"
      )

    if getattr(args, "title_keyword", None):
      kw_clean = args.title_keyword.replace("'", "\\'").strip()
      # Scope strictly to issue titles (CR + CB) — not PST hierarchy fields.
      conditions.append(
          f"(LOWER(cr_title) LIKE '%{kw_clean.lower()}%' OR"
          f" LOWER(cb_title) LIKE '%{kw_clean.lower()}%')"
      )

    if getattr(args, "cr_id", None):
      clean_cr_id = args.cr_id.strip()
      if not clean_cr_id.isdigit():
        raise ValueError(
            f"Invalid --cr-id '{args.cr_id}'. Must be numeric (e.g. 537381675)."
        )
      conditions.append(f"cr_issue_id = {clean_cr_id}")

    if getattr(args, "cb_id", None):
      clean_cb_id = args.cb_id.strip()
      if not clean_cb_id.isdigit():
        raise ValueError(
            f"Invalid --cb-id '{args.cb_id}'. Must be numeric (e.g. 519126417)."
        )
      conditions.append(f"cb_issue_id = {clean_cb_id}")

    if getattr(args, "severity", None):
      sev_clean = args.severity.upper().strip()
      if "," in sev_clean:
        sevs = [f"'{s.strip()}'" for s in sev_clean.split(",") if s.strip()]
        conditions.append(f"cr_severity IN ({', '.join(sevs)})")
      else:
        conditions.append(f"cr_severity = '{sev_clean}'")

    if getattr(args, "status", None):
      status_clean = args.status.strip()
      conditions.append(f"triaged = '{status_clean}'")

    if getattr(args, "resolution_status", None):
      res_clean = args.resolution_status.replace("'", "\\'").strip()
      if "%" in res_clean or " " in res_clean:
        conditions.append(
            f"LOWER(cb_pm_resolution_status) LIKE '%{res_clean.lower()}%'"
        )
      else:
        conditions.append(f"cb_pm_resolution_status = '{res_clean}'")

    if getattr(args, "pst_name", None):
      pst_clean = args.pst_name.replace("'", "\\'").strip()
      if "," in pst_clean:
        parts = [f"'{p.strip()}'" for p in pst_clean.split(",") if p.strip()]
        conditions.append(f"pst_display_name IN ({', '.join(parts)})")
      elif "%" in pst_clean or " " in pst_clean:
        conditions.append(
            f"LOWER(pst_display_name) LIKE '%{pst_clean.lower()}%'"
        )
      else:
        conditions.append(f"pst_display_name = '{pst_clean}'")

    if getattr(args, "pst_group", None):
      group_clean = args.pst_group.replace("'", "\\'").strip()
      if "," in group_clean:
        parts = [f"'{p.strip()}'" for p in group_clean.split(",") if p.strip()]
        conditions.append(f"pst_owning_product_group IN ({', '.join(parts)})")
      elif "%" in group_clean or " " in group_clean:
        conditions.append(
            f"LOWER(pst_owning_product_group) LIKE '%{group_clean.lower()}%'"
        )
      else:
        conditions.append(f"pst_owning_product_group = '{group_clean}'")

    if getattr(args, "pst_area", None):
      area_clean = args.pst_area.replace("'", "\\'").strip()
      # Strict PST hierarchy scoping — must NOT leak into cr_title/cb_title
      # (that's what --title-keyword is for).
      conditions.append(
          f"(LOWER(pst_owning_product_group) LIKE '%{area_clean.lower()}%' OR"
          f" LOWER(pst_display_name) LIKE '%{area_clean.lower()}%' OR"
          f" LOWER(owning_super_product_area) LIKE '%{area_clean.lower()}%' OR"
          f" LOWER(pst_owning_execution_area) LIKE '%{area_clean.lower()}%')"
      )

    if getattr(args, "pst_execution", None):
      exec_clean = args.pst_execution.replace("'", "\\'").strip()
      conditions.append(
          f"LOWER(pst_owning_execution_area) LIKE '%{exec_clean.lower()}%'"
      )

    if getattr(args, "region", None):
      reg_clean = args.region.upper().strip()
      conditions.append(f"region = '{reg_clean}'")

    if getattr(args, "sub_region", None):
      sub_clean = args.sub_region.replace("'", "\\'").strip()
      conditions.append(f"LOWER(sub_region) LIKE '%{sub_clean.lower()}%'")

    if getattr(args, "request_type", None):
      req_clean = args.request_type.replace("'", "\\'").strip()
      conditions.append(f"LOWER(cb_request_type) LIKE '%{req_clean.lower()}%'")

    if getattr(args, "interlock", None):
      int_clean = args.interlock.strip()
      conditions.append(
          f"cb_if_submitted_during_GTM_interlock = '{int_clean}'"
      )

    if getattr(args, "launch_status", None):
      launch_clean = args.launch_status.replace("'", "\\'").strip()
      conditions.append(
          f"LOWER(launch_status) LIKE '%{launch_clean.lower()}%'"
      )

    if getattr(args, "cluster", None):
      cluster_clean = args.cluster.replace("'", "\\'").strip()
      conditions.append(
          f"(LOWER(sub_region) LIKE '%{cluster_clean.lower()}%' OR"
          f" LOWER(region) LIKE '%{cluster_clean.lower()}%')"
      )

    if not conditions:
      return ""

    return "WHERE " + " AND ".join(conditions)

  def generate_query(self, args):
    where_clause = self.build_where_clause(args)
    limit = getattr(args, "limit", self.limit)
    return BASE_QUERY_TEMPLATE.format(
        custom_field_opp_1=CUSTOM_FIELD_SFDC_OPP_1,
        custom_field_opp_2=CUSTOM_FIELD_SFDC_OPP_2,
        custom_field_opp_3=CUSTOM_FIELD_SFDC_OPP_3,
        custom_field_opp_4=CUSTOM_FIELD_SFDC_OPP_4,
        custom_field_pst_1=CUSTOM_FIELD_PST_ID_1,
        custom_field_pst_2=CUSTOM_FIELD_PST_ID_2,
        comp_gaps=COMPONENT_PRODUCT_FEATURE_GAPS,
        comp_blockers=COMPONENT_CLOUD_BLOCKERS_INTAKE,
        comp_escalations=COMPONENT_CUSTOMER_ESCALATIONS,
        where_clause=where_clause,
        limit=limit,
    )

  def generate_list_distinct_query(self, field_name):
    valid_fields = {
        "cb_pm_resolution_status": "cb_pm_resolution_status",
        "pst_display_name": "pst_display_name",
        "pst_owning_product_group": "pst_owning_product_group",
        "pst_owning_execution_area": "pst_owning_execution_area",
        "owning_super_product_area": "owning_super_product_area",
        "region": "region",
        "sub_region": "sub_region",
        "cb_request_type": "cb_request_type",
        "launch_status": "launch_status",
        "account_name": "account_name",
    }

    if field_name not in valid_fields:
      raise ValueError(
          f"Invalid field '{field_name}'. Allowed distinct fields:"
          f" {list(valid_fields.keys())}"
      )

    col = valid_fields[field_name]
    base_query = BASE_QUERY_TEMPLATE.format(
        custom_field_opp_1=CUSTOM_FIELD_SFDC_OPP_1,
        custom_field_opp_2=CUSTOM_FIELD_SFDC_OPP_2,
        custom_field_opp_3=CUSTOM_FIELD_SFDC_OPP_3,
        custom_field_opp_4=CUSTOM_FIELD_SFDC_OPP_4,
        custom_field_pst_1=CUSTOM_FIELD_PST_ID_1,
        custom_field_pst_2=CUSTOM_FIELD_PST_ID_2,
        comp_gaps=COMPONENT_PRODUCT_FEATURE_GAPS,
        comp_blockers=COMPONENT_CLOUD_BLOCKERS_INTAKE,
        comp_escalations=COMPONENT_CUSTOMER_ESCALATIONS,
        where_clause="",
        limit=30000,
    )

    return f"""{base_query}
SELECT DISTINCT {col} AS distinct_value
FROM _0
WHERE {col} IS NOT NULL AND {col} != ''
ORDER BY {col};"""
