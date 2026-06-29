#!/usr/bin/env python3
"""
CLI Entrypoint for Codelab Pricing Estimator.

Orchestrates deterministic discovery across deployed sandbox infrastructure,
calculates hourly running costs, and exports zero-indentation HTML table reports.
"""

import argparse
import os
import sys
import auditor
import cost_engine


def main():
    parser = argparse.ArgumentParser(
        description="Google Cloud Deployed Sandbox Pricing Auditor. Queries Cloud Asset Inventory and native APIs to calculate deterministic hourly running costs.",
        epilog="""
Examples:
  # Audit the currently running sandbox environment project:
  python3 extract_and_estimate.py --project "my-sandbox-project-123"

  # Audit and save the markdown report containing zero-indentation HTML table to disk:
  python3 extract_and_estimate.py --project "my-sandbox-project-123" --save-report "artifacts/deployed_cost.md"
"""
    )
    
    parser.add_argument("--project", required=True, help="GCP Project ID to audit running resources deterministically.")
    parser.add_argument("--save-report", help="Absolute or relative path to export the Markdown cost report.")
    
    args = parser.parse_args()
    
    resources, total_cost = auditor.audit_project_resources(args.project)
    report_str = cost_engine.generate_report(args.project, resources, total_cost)
    
    print("\n" + report_str + "\n")
    
    if args.save_report:
        try:
            parent_dir = os.path.dirname(args.save_report)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            with open(args.save_report, 'w', encoding='utf-8') as f:
                f.write(report_str + "\n")
            print(f"💾 Audit report successfully exported to: {args.save_report}")
        except Exception as e:
            print(f"❌ Failed to save report: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
