#!/usr/bin/env python3
"""CLI utility to render raw PLX F1 JSON/TSV output into a standardized 33-column Cloud Blocker Markdown Report artifact.
"""

import argparse
import json
import os
import sys

CLEAN_HEADERS = [
    "#",
    "CR Buganizer Issue ID (Link for all sellers)",
    "CR Triage / Cloud Connect Admin Link",
    "CR Title",
    "Cr Severity",
    "CR Created Date",
    "CR Requester",
    "CR Age (In Days)",
    "CR Triaged/Linked to CB?",
    "CR Linked to Opp/Workload",
    "Vector Opp/Workload ID linked to CR",
    "Vector Account Name",
    "Account Sales Region",
    "Sales Sub Region",
    "Cloud Blocker (FR/RSR) Title",
    "go/CB-Resolution-Status",
    "CB Buganizer Issue ID",
    "Cb If Submitted During GTM Interlock",
    "Cb Interlock Submission Period",
    "Cb Qualified For Semester",
    "Cb Submission Intake Period",
    "Cb Committed For Semester",
    "Cb Commitment Period",
    "Type of CB Request",
    "Region Name (for RSRs)",
    "Owning Super Product Area",
    "CB go/Cloud-PST Product Group",
    "CB go/Cloud-PST Execution Area",
    "CB go/Cloud-PST Product / Variant / Feature Name",
    "CB Assignee",
    "CB Delivery Date (from PM/Engr.)",
    "Launch Status",
    "Actual Launch Date",
    "Eng. Execution Status Summary",
]


def render_markdown_report(
    raw_data,
    account_name="Account",
    reporting_id=None,
    sales_region=None,
    segment=None,
    nal_cluster=None,
    nal_id=None,
):
  if isinstance(raw_data, str):
    try:
      parsed = json.loads(raw_data)
      if "results" in parsed:
        lines = parsed["results"].strip().split("\n")
        rows = [line.split("\t") for line in lines[1:] if line.strip()]
      else:
        lines = raw_data.strip().split("\n")
        rows = [line.split("\t") for line in lines[1:] if line.strip()]
    except Exception:
      lines = raw_data.strip().split("\n")
      rows = [line.split("\t") for line in lines[1:] if line.strip()]
  elif isinstance(raw_data, dict) and "results" in raw_data:
    lines = raw_data["results"].strip().split("\n")
    rows = [line.split("\t") for line in lines[1:] if line.strip()]
  else:
    rows = raw_data

  out = []
  out.append(f"# Cloud Blockers & Customer Requests Report: `{account_name}`\n")
  if reporting_id:
    out.append(
        f"- **Vector Parent Account Reporting ID:** [`{reporting_id}`]"
        f"(https://vector.lightning.force.com/lightning/r/Account/{reporting_id}/view)"
        " (Verified via `vector-customers`)"
    )
  out.append(f"- **Account Name:** {account_name}")
  if sales_region:
    out.append(f"- **Sales Region:** {sales_region}")
  if segment:
    out.append(f"- **Customer Segment:** {segment}")
  if nal_id or nal_cluster:
    nal_str = f"`{nal_id}`" if nal_id else ""
    out.append(f"- **NAL ID / Cluster:** {nal_str} ({nal_cluster or 'N/A'})")
  out.append(f"- **Total Records Returned:** {len(rows)} Records")
  out.append(
      "- **Data Source:** PLX F1 `cloud_blockers_data` +"
      " Buganizer `issuestatsfresh.latest`\n"
  )
  out.append("---")

  out.append("| " + " | ".join(CLEAN_HEADERS) + " |")
  out.append("| " + " | ".join(["---"] * len(CLEAN_HEADERS)) + " |")

  for idx, r in enumerate(rows, start=1):
    row_vals = [str(idx)]
    for val in r:
      if val == "null" or val is None or val == "":
        row_vals.append("")
      else:
        clean_val = str(val).replace("\n", " ").replace("|", "\\|")
        row_vals.append(clean_val)
    out.append("| " + " | ".join(row_vals) + " |")

  return "\n".join(out)


def main():
  parser = argparse.ArgumentParser(
      description="Render PLX F1 Cloud Blocker Output to Markdown Report"
  )
  parser.add_argument(
      "--input-file",
      required=True,
      help="Path to raw PLX output JSON or TSV file",
  )
  parser.add_argument(
      "--output-file", required=True, help="Path to write formatted Markdown"
  )
  parser.add_argument(
      "--account-name", default="Account", help="Customer Account Name"
  )
  parser.add_argument(
      "--reporting-id", help="SFDC Vector Parent Account Reporting ID"
  )
  parser.add_argument("--sales-region", help="Sales Region (e.g. NORTHAM)")
  parser.add_argument("--segment", help="Customer Segment (e.g. Enterprise)")
  parser.add_argument("--nal-cluster", help="NAL Cluster (e.g. West 4 (CL))")
  parser.add_argument("--nal-id", help="NAL ID")

  args = parser.parse_args()

  if not os.path.exists(args.input_file):
    print(f"Error: Input file '{args.input_file}' not found.", file=sys.stderr)
    sys.exit(1)

  with open(args.input_file, "r") as f:
    content = f.read()

  md_content = render_markdown_report(
      content,
      account_name=args.account_name,
      reporting_id=args.reporting_id,
      sales_region=args.sales_region,
      segment=args.segment,
      nal_cluster=args.nal_cluster,
      nal_id=args.nal_id,
  )

  os.makedirs(os.path.dirname(os.path.abspath(args.output_file)), exist_ok=True)
  with open(args.output_file, "w") as f:
    f.write(md_content)

  print(f"Successfully rendered report to '{args.output_file}'")


if __name__ == "__main__":
  main()
