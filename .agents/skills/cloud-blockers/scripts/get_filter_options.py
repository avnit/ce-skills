#!/usr/bin/env python3
"""Utility for dynamically fetching and caching active filter options (helper maps) from PLX F1.

Queryable metadata types:
  --pst-groups         Fetch distinct PST Product Groups (e.g. Cloud Networking, Cloud Data Analytics)
  --pst-features       Fetch distinct PST Product/Variant/Feature names (e.g. PSC Interfaces, GKE)
  --statuses           Fetch distinct CB PM Resolution Statuses (e.g. Awaiting PM Status, GA Launched)
  --regions            Fetch distinct Account Sales Regions & Sub-Regions
  --request-types      Fetch distinct CB Request Types (e.g. Feature Request, RSR)
"""

import argparse
import sys

QUERY_MAP = {
    "pst_groups": """
    SELECT DISTINCT display_name AS pst_group_name
    FROM rel360_platform.pst.v1.entities
    WHERE entity_id.type = 3 -- Product Group
    ORDER BY pst_group_name
    LIMIT 200;
  """,
    "pst_features": """
    SELECT DISTINCT display_name AS pst_feature_name
    FROM rel360_platform.pst.v1.entities
    WHERE entity_id.type = 5 -- Product/Variant/Feature
    ORDER BY pst_feature_name
    LIMIT 300;
  """,
    "statuses": """
    SELECT DISTINCT cb_pm_resolution_status
    FROM cloud_blockers_data.prod.cloud_blockers_stack_ranking_report_view
    WHERE cb_pm_resolution_status IS NOT NULL AND cb_pm_resolution_status != ''
    ORDER BY cb_pm_resolution_status;
  """,
    "regions": """
    SELECT DISTINCT region, sub_region
    FROM ceops.gcc_opportunities
    WHERE region IS NOT NULL AND region != ''
    ORDER BY region, sub_region
    LIMIT 200;
  """,
    "request_types": """
    SELECT DISTINCT cb_request_type
    FROM cloud_blockers_data.prod.cloud_blockers_stack_ranking_report_view
    WHERE cb_request_type IS NOT NULL AND cb_request_type != ''
    ORDER BY cb_request_type;
  """,
}


def get_metadata_query(category):
  if category not in QUERY_MAP:
    raise ValueError(
        f"Unknown metadata category '{category}'. Valid options:"
        f" {list(QUERY_MAP.keys())}"
    )
  return QUERY_MAP[category].strip()


def main():
  parser = argparse.ArgumentParser(
      description=(
          "Fetch dynamic filter helper maps from PLX for Cloud Blocker"
          " Dashboard fields"
      )
  )
  parser.add_argument(
      "category",
      choices=list(QUERY_MAP.keys()),
      help="Metadata category to query from PLX",
  )

  args = parser.parse_args()

  try:
    sql = get_metadata_query(args.category)
    print(sql)
  except Exception as e:
    print(f"Error generating metadata query: {e}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
  main()
