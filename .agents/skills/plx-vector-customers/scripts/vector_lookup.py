#!/usr/bin/env python3
"""
vector_lookup.py - CLI tool & Python API for querying PLX gcc.vector_customers.

Examples:
    python3 vector_lookup.py --account "Workday"
    python3 vector_lookup.py --nal 2507192445
    python3 vector_lookup.py --team "Workday"
"""

import argparse
import sys

def build_account_lookup_sql(account_name: str) -> str:
    escaped_name = account_name.replace("'", "''")
    return f"""SELECT
  reporting_id,
  CONCAT('https://vector.lightning.force.com/lightning/r/Account/', reporting_id, '/view') AS vector_url,
  core.account_name AS account_name,
  core.nal_id AS nal_id,
  core.nal_name AS nal_name,
  core.region AS region,
  core.sub_region AS sub_region
FROM gcc.vector_customers
WHERE LOWER(core.account_name) LIKE '%{escaped_name.lower()}%'
LIMIT 10;"""

def build_team_lookup_sql(account_name: str) -> str:
    escaped_name = account_name.replace("'", "''")
    return f"""SELECT DISTINCT
  reporting_id,
  CONCAT('https://vector.lightning.force.com/lightning/r/Account/', reporting_id, '/view') AS vector_url,
  core.account_name AS account_name,
  core.nal_id AS nal_id,
  core.nal_name AS nal_name,
  acc.primary_field_rep AS fsr_ldaps,
  acc.customer_engineer AS ce_ldaps
FROM gcc.vector_customers,
UNNEST(account_details) AS acc
WHERE LOWER(core.account_name) LIKE '%{escaped_name.lower()}%'
LIMIT 10;"""

def build_nal_roster_sql(nal_id: int) -> str:
    return f"""SELECT
  reporting_id,
  CONCAT('https://vector.lightning.force.com/lightning/r/Account/', reporting_id, '/view') AS vector_url,
  core.account_name AS account_name,
  core.segment AS segment,
  core.region AS region,
  core.sub_region AS sub_region
FROM gcc.vector_customers
WHERE core.nal_id = {nal_id}
ORDER BY core.account_name
LIMIT 50;"""

def main():
    parser = argparse.ArgumentParser(
        description="Query PLX gcc.vector_customers for reporting IDs, Vector links, NAL rosters, or team assignments."
    )
    parser.add_argument("--account", help="Search customer name for reporting ID, Vector URL, and NAL details")
    parser.add_argument("--nal", type=int, help="List accounts for a given NAL ID")
    parser.add_argument("--team", help="Lookup assigned FSR and Customer Engineer for an account")
    parser.add_argument("--sql-only", action="store_true", help="Only output the generated SQL query without executing")

    args = parser.parse_args()

    if not (args.account or args.nal or args.team):
        parser.print_help()
        sys.exit(1)

    if args.account:
        sql = build_account_lookup_sql(args.account)
    elif args.team:
        sql = build_team_lookup_sql(args.team)
    elif args.nal:
        sql = build_nal_roster_sql(args.nal)

    if args.sql_only:
        print(sql)
        sys.exit(0)

    print("Generated SQL for PLX ExecuteSql (includes direct Vector Salesforce URLs):")
    print("-" * 70)
    print(sql)
    print("-" * 70)

if __name__ == "__main__":
    main()
