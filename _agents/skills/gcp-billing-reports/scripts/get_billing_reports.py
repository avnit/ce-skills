#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime

def run_command(cmd_args):
    """Runs a command without a shell and returns success status, stdout, and stderr."""
    try:
        result = subprocess.run(
            cmd_args,
            shell=False,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def format_cost(cost_val):
    """Formats cost value to standard 2 decimal places, keeping whole dollars as clean integers."""
    try:
        f_val = float(cost_val)
        if f_val == 0.0:
            return "$0"
        
        # Round to 2 decimal places (nearest cent)
        rounded_val = round(f_val, 2)
        if rounded_val == 0.0:
            # Keep high precision for small sub-cent charges so they aren't hidden
            s_val = f"{f_val:.6f}".rstrip('0').rstrip('.')
            return f"${s_val}"
            
        if rounded_val.is_integer():
            return f"${int(rounded_val)}"
            
        return f"${rounded_val:.2f}"
    except Exception:
        return f"${cost_val}"

def load_gcp_config():
    """Recursively searches parent directories for gcp_config.txt and parses key-value configuration."""
    config = {}
    curr_dir = os.getcwd()
    
    # Search up to 5 parent directories
    for _ in range(5):
        path = os.path.join(curr_dir, "gcp_config.txt")
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and '=' in line and not line.startswith('#'):
                            k, v = line.split('=', 1)
                            config[k.strip()] = v.strip()
                return config
            except Exception as e:
                print(f"⚠️ Warning: Failed to read gcp_config.txt: {e}", file=sys.stderr)
        
        parent = os.path.dirname(curr_dir)
        if parent == curr_dir:
            break
        curr_dir = parent
        
    return config

def execute_query(query):
    """Executes a BigQuery query using standard bq CLI with max_rows bypass."""
    cmd_args = ["bq", "query", "--use_legacy_sql=false", "--max_rows=100000", "--format=json", query]
    success, stdout, stderr = run_command(cmd_args)
    
    if not success:
        if "credentials" in stderr.lower() or "authentication" in stderr.lower() or "access token" in stderr.lower():
            print("❌ Error: Authentication failure. Could not query BigQuery.", file=sys.stderr)
            print("💡 Fix: Please run 'gcloud auth login' or configure application default credentials.", file=sys.stderr)
        else:
            print(f"❌ BigQuery query failed:\n{stderr}", file=sys.stderr)
        sys.exit(1)
        
    try:
        return json.loads(stdout)
    except Exception as e:
        print(f"❌ Error parsing BigQuery JSON response: {e}", file=sys.stderr)
        sys.exit(1)

def get_date_filter(month_str):
    """Generates standard SQL partitioning boundaries for current MTD or a specific historical month."""
    if month_str:
        if not re.match(r'^\d{4}-\d{2}$', month_str):
            print(f"❌ Error: Invalid month format '{month_str}'. Must be YYYY-MM.", file=sys.stderr)
            sys.exit(1)
        try:
            start_date = f"{month_str}-01"
            yr, mo = map(int, month_str.split("-"))
            if mo == 12:
                next_month_str = f"{yr+1}-01-01"
            else:
                next_month_str = f"{yr}-{mo+1:02d}-01"
            return f"_PARTITIONTIME >= TIMESTAMP('{start_date}') AND _PARTITIONTIME < TIMESTAMP('{next_month_str}')"
        except Exception as e:
            print(f"❌ Error calculating date boundaries for month '{month_str}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Dynamic Month-To-Date boundary
        return "_PARTITIONTIME >= TIMESTAMP(DATE_TRUNC(CURRENT_DATE(), MONTH))"

def generate_markdown_table(headers, alignments, rows):
    """Constructs a standard Markdown table string."""
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(alignments) + " |"
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)

def run_project_report(table, date_filter):
    query = f"""
    SELECT 
      COALESCE(project.id, 'Non-Project Charges') as project_id,
      COALESCE(project.name, 'Non-Project Charges') as project_name,
      ROUND(SUM(cost), 4) as mtd_cost
    FROM `{table}`
    WHERE {date_filter}
    GROUP BY project_id, project_name
    ORDER BY mtd_cost DESC
    """
    results = execute_query(query)
    
    headers = ["Project ID", "Project Name", "MTD Cost (USD)"]
    alignments = [":---", ":---", ":---"]
    rows = []
    for r in results:
        rows.append([r['project_id'], r['project_name'], format_cost(r['mtd_cost'])])
        
    return "### MTD Spend per GCP Project\n\n" + generate_markdown_table(headers, alignments, rows)

def run_service_report(table, date_filter):
    query = f"""
    SELECT 
      service.description as service_name,
      ROUND(SUM(cost), 4) as mtd_cost
    FROM `{table}`
    WHERE {date_filter}
    GROUP BY service_name
    ORDER BY mtd_cost DESC
    """
    results = execute_query(query)
    
    headers = ["GCP Service Name", "MTD Cost (USD)"]
    alignments = [":---", ":---"]
    rows = []
    for r in results:
        rows.append([r['service_name'], format_cost(r['mtd_cost'])])
        
    return "### MTD Spend per GCP Service\n\n" + generate_markdown_table(headers, alignments, rows)

def run_sku_report(table, date_filter):
    query = f"""
    SELECT 
      service.description as service_name,
      sku.description as sku_name,
      ROUND(SUM(cost), 4) as mtd_cost
    FROM `{table}`
    WHERE {date_filter}
    GROUP BY service_name, sku_name
    ORDER BY mtd_cost DESC
    LIMIT 10
    """
    results = execute_query(query)
    
    headers = ["GCP Service", "Resource SKU Description", "MTD Cost (USD)"]
    alignments = [":---", ":---", ":---"]
    rows = []
    for r in results:
        rows.append([r['service_name'], r['sku_name'], format_cost(r['mtd_cost'])])
        
    return "### Top 10 Most Expensive Resource SKUs\n\n" + generate_markdown_table(headers, alignments, rows)

def run_trend_report(table, date_filter):
    query = f"""
    SELECT 
      EXTRACT(DATE FROM usage_start_time) as spend_date,
      ROUND(SUM(cost), 4) as daily_cost
    FROM `{table}`
    WHERE {date_filter}
    GROUP BY spend_date
    ORDER BY spend_date ASC
    """
    results = execute_query(query)
    
    headers = ["Spend Date", "Daily Cost (USD)"]
    alignments = [":---", ":---"]
    rows = []
    for r in results:
        # Parse spend_date from JSON representation
        date_val = r['spend_date']
        if isinstance(date_val, dict) and 'value' in date_val:
            date_val = date_val['value']
        rows.append([date_val, format_cost(r['daily_cost'])])
        
    return "### Daily Spend Trend Metrics\n\n" + generate_markdown_table(headers, alignments, rows)

def main():
    parser = argparse.ArgumentParser(
        description="GCP Billing Export Reporting CLI. Connects dynamically to BigQuery to generate MTD sandbox spend reviews.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run Month-To-Date Spend breakdown by Project (Default):
  python3 get_billing_reports.py

  # Run MTD spend by Service category:
  python3 get_billing_reports.py --report service

  # Run historical Month spend for April 2026:
  python3 get_billing_reports.py --month "2026-04" --report all

  # Save complete operational billing report to file:
  python3 get_billing_reports.py --report all --save-artifact "artifacts/monthly_spend.md"
"""
    )
    
    parser.add_argument("--report", default="project", choices=["project", "service", "sku", "trend", "all"], help="Billing report type to generate. 'all' prints all 4 reports.")
    parser.add_argument("--month", help="Optional historical query month override in YYYY-MM format (e.g., 2026-04). Default is the current Month-To-Date.")
    parser.add_argument("--output", default="table", choices=["table", "json"], help="Console output format. 'table' displays standard Markdown tables, 'json' outputs raw parsed objects.")
    parser.add_argument("--save-artifact", help="Absolute or relative path to export the report to a file.")
    
    args = parser.parse_args()
    
    # Load config
    config = load_gcp_config()
    table_name = config.get("billing_table")
    
    if not table_name:
        billing_account = config.get("billing_account")
        if not billing_account:
            print("❌ Error: Could not find 'billing_account' or 'billing_table' in gcp_config.txt.", file=sys.stderr)
            print("💡 Fix: Please create a gcp_config.txt containing folder_id and billing_account.", file=sys.stderr)
            sys.exit(1)
        # Calculate standard detailed resource billing table
        suffix = billing_account.replace("-", "_")
        table_name = f"billing-350700.billing.gcp_billing_export_resource_v1_{suffix}"
        
    date_filter = get_date_filter(args.month)
    month_display = args.month if args.month else datetime.now().strftime("%Y-%m (MTD)")
    
    print(f"📊 Billing Table: `{table_name}`")
    print(f"📅 Query Window:  [{month_display}]")
    
    # Aggregate requested reports
    reports = []
    if args.report == "project" or args.report == "all":
        reports.append(run_project_report(table_name, date_filter))
    if args.report == "service" or args.report == "all":
        reports.append(run_service_report(table_name, date_filter))
    if args.report == "sku" or args.report == "all":
        reports.append(run_sku_report(table_name, date_filter))
    if args.report == "trend" or args.report == "all":
        reports.append(run_trend_report(table_name, date_filter))
        
    # Render Console Output
    title = f"## Google Cloud Billing Audit Report: [{month_display}]"
    metadata = [
        f"*   **Target Billing Account**: `{config.get('billing_account', 'Unknown')}`",
        f"*   **Partition Filter Clause**: `{date_filter}`",
        f"*   **Report Compiled At**: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}",
        "",
        "---"
    ]
    
    full_report_str = title + "\n\n" + "\n".join(metadata) + "\n\n" + "\n\n---\n\n".join(reports)
    
    # Append Deletion Cost Control workflow guide
    if args.report == "project" or args.report == "all":
        workflow_guide = [
            "---",
            "### ⚠️ Cost Control & Sandbox Deletion Workflows",
            "If you identify a forgotten or leaked sandbox project generating high MTD costs in the table above, you can immediately reference its **Project ID** (first column) and call the **`codelab-cleanup`** skill to delete it instantly.",
            "",
            "**Example CLI Cleanup Command**:",
            "```bash",
            "python3 _agents/skills/codelab-cleanup/scripts/cleanup_projects.py --delete PROJECT_ID --force",
            "```"
        ]
        full_report_str += "\n\n" + "\n".join(workflow_guide)
        
    print("\n" + full_report_str + "\n")
    
    # Save file
    if args.save_artifact:
        try:
            parent_dir = os.path.dirname(args.save_artifact)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            with open(args.save_artifact, 'w', encoding='utf-8') as f:
                f.write(full_report_str + "\n")
            print(f"💾 Success! Exported report artifact to: {args.save_artifact}")
        except Exception as e:
            print(f"❌ Failed to save report artifact: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
