#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

def run_command(cmd_args):
    """Runs a system command safely without shell."""
    try:
        result = subprocess.run(
            cmd_args,
            shell=False,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def execute_query(query):
    """Executes a BigQuery query using standard bq CLI with concord-prod project routing."""
    cmd_args = [
        "bq", "query",
        "--project_id=concord-prod",
        "--use_legacy_sql=false",
        "--max_rows=100000",
        "--format=json",
        query
    ]
    success, stdout, stderr = run_command(cmd_args)
    
    if not success:
        if "credentials" in stderr.lower() or "authentication" in stderr.lower() or "access token" in stderr.lower():
            print("❌ Error: Authentication failure. Could not query BigQuery.", file=sys.stderr)
            print("💡 Fix: Please run 'gcert' or 'gcloud auth login' to refresh your corporate credentials.", file=sys.stderr)
        else:
            print(f"❌ BigQuery query failed:\n{stderr}", file=sys.stderr)
        sys.exit(1)
        
    try:
        return json.loads(stdout)
    except Exception as e:
        print(f"❌ Error parsing BigQuery JSON response: {e}", file=sys.stderr)
        sys.exit(1)

def generate_markdown_table(headers, alignments, rows):
    """Constructs a standard Markdown table string."""
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(alignments) + " |"
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)

def compile_expert_requests(year, output_format, save_path):
    """Queries BigQuery and generates the expert requests segmentation report."""
    start_date = f"{year}-01-01"
    end_date = f"{year+1}-01-01"
    
    query = f"""
    SELECT
        opportunities.stage_name  AS opportunities_stage_name,
        expert_request_from_opps.navigate_product  AS expert_request_from_opps_expert_req_navigate_product,
        COUNT(DISTINCT expert_request_from_opps.expert_request_id ) AS expert_request_from_opps_expert_req_count
    FROM `concord-prod.service_cloudbi.opportunities_streaming`
                       AS opportunities
    LEFT JOIN UNNEST(opportunities.expert_request.details) as expert_request_from_opps
    LEFT JOIN `concord-prod.service_cloudbi.persons` AS expert_req_owner_manager ON expert_request_from_opps.owner_user_name = expert_req_owner_manager.user_name
    WHERE (IF(opportunities.region = 'GOOGLE PUBLIC SECTOR', 'PUBLIC SECTOR', UPPER(opportunities.region)) ) = 'NORTHAM' 
      AND ((opportunities.deal_type ) IN ('Commit Parent', 'Non-Commit') 
      AND (opportunities.stage_name ) IN ('00 - Qualify', '01 - Refine', '02 - Tech Eval/Solution Dev', '03 - Proposal/Negotiation', '04 - Migration/Implementation')) 
      AND (((( DATE_FROM_UNIX_DATE(expert_request_from_opps.created_date)  ) >= ((DATE('{start_date}'))) 
      AND ( DATE_FROM_UNIX_DATE(expert_request_from_opps.created_date)  ) < ((DATE('{end_date}'))))) 
      AND ((expert_request_from_opps.navigate_product ) IN ('AppEco', 'Application Ecosystem', 'Cloud Runtimes', 'Infrastructure', 'Infrastructure Modernization', 'MWW: Microsoft on GCP', 'Microsoft Workloads', 'Microsoft on GCP', 'Networking', 'SAP', 'Security') 
      AND (expert_req_owner_manager.reporting_chain.manager_user_name ) IN ('alanpoole', 'biodun', 'brandonfreitag', 'danidiaz', 'eyvonne', 'heathernevill', 'jasonbisson', 'mcolumbus', 'murriel', 'ngpope', 'obinnaegonu', 'prz', 'reisfeld', 'reserrata', 'sudheerg', 'vdatta', 'wdjones')))
    GROUP BY
        1,
        2
    LIMIT 30000
    """
    
    print(f"🔍 Querying concord-prod for expert requests created in [{year}]...")
    results = execute_query(query)
    
    if not results:
        print(f"\nℹ️ No expert request records found for the year {year}.")
        return
        
    # Standardized ordered list of stage columns (maintaining chronology)
    ordered_stages = [
        '00 - Qualify',
        '01 - Refine',
        '02 - Tech Eval/Solution Dev',
        '03 - Proposal/Negotiation',
        '04 - Migration/Implementation'
    ]

    # Map results into a 2D pivot grid: pivot_grid[product][stage] = count
    pivot_grid = {}
    for r in results:
        prod = r.get('expert_request_from_opps_expert_req_navigate_product', 'Unknown')
        stage = r.get('opportunities_stage_name', 'Unknown')
        count = int(r.get('expert_request_from_opps_expert_req_count', 0))
        
        if prod not in pivot_grid:
            pivot_grid[prod] = {s: 0 for s in ordered_stages}
            
        if stage in ordered_stages:
            pivot_grid[prod][stage] = count
        else:
            # Catch any other stage in case the sales pipeline evolves
            if stage not in pivot_grid[prod]:
                pivot_grid[prod][stage] = 0
            pivot_grid[prod][stage] = count
            if stage not in ordered_stages:
                ordered_stages.append(stage)

    # Compile row-totals and prepare rows data
    pivoted_rows = []
    for prod, stage_counts in pivot_grid.items():
        row_total = sum(stage_counts.values())
        pivoted_rows.append({
            'product': prod,
            'counts': stage_counts,
            'total': row_total
        })
        
    # Sort products by calculated horizontal Total count in descending order
    pivoted_rows.sort(key=lambda x: -x['total'])

    if output_format == 'json':
        output_str = json.dumps(pivoted_rows, indent=2)
        print(output_str)
    else:
        headers = ["Navigate Product"] + ordered_stages + ["Total"]
        alignments = [":---"] + [":---"] * len(ordered_stages) + [":---"]
        
        # Format rows. Null values (0) are styled using '∅' (matching your Sheets dashboard)
        rows = []
        for pr in pivoted_rows:
            prod_name = pr['product']
            counts = pr['counts']
            total_val = pr['total']
            
            stage_cols = []
            for s in ordered_stages:
                c = counts.get(s, 0)
                stage_cols.append(str(c) if c > 0 else "∅")
                
            rows.append([prod_name] + stage_cols + [str(total_val)])
            
        # Generate title and metadata
        title = f"## Service CloudBI: Expert Requests Pivot Dashboard [{year}]"
        metadata = [
            f"*   **Target Database**: `concord-prod.service_cloudbi`",
            f"*   **Region Filter**: NORTHAM",
            f"*   **Opportunity Stages**: Qualify, Refine, Tech Eval, Proposal, Implementation",
            f"*   **Report Compiled At**: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}",
            "",
            "---"
        ]
        
        output_str = title + "\n\n" + "\n".join(metadata) + "\n\n" + generate_markdown_table(headers, alignments, rows)
        print("\n" + output_str + "\n")
        
    if save_path:
        try:
            parent_dir = os.path.dirname(save_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                if output_format == 'json':
                    json.dump(results, f, indent=2)
                else:
                    f.write(output_str + "\n")
            print(f"💾 Success! Exported report artifact to: {save_path}")
        except Exception as e:
            print(f"❌ Failed to save report artifact: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(
        description="GCP Expert Request Management Reporter CLI. Connects to concord-prod to analyze Service CloudBI asks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compile 2026 Expert Request report (Default):
  python3 get_expert_requests.py

  # Compile 2025 Expert Request report:
  python3 get_expert_requests.py --year 2025

  # Save report to local Markdown file:
  python3 get_expert_requests.py --save-artifact "artifacts/expert_requests_mtd.md"
"""
    )
    
    parser.add_argument("--year", default=2026, type=int, help="Filter by the created year of expert requests. Default is 2026.")
    parser.add_argument("--output", default="table", choices=["table", "json"], help="Console and file output layout format.")
    parser.add_argument("--save-artifact", help="Absolute or relative path to save the Markdown report.")
    
    args = parser.parse_args()
    
    compile_expert_requests(
        year=args.year,
        output_format=args.output,
        save_path=args.save_artifact
    )

if __name__ == "__main__":
    main()
