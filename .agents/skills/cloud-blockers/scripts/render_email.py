#!/usr/bin/env python3
"""CLI utility to convert PLX F1 output or Cloud Blocker Markdown reports into responsive, styled HTML emails suitable for Gmail / GMR delivery.
"""

import argparse
import json
import re
import sys


def parse_markdown_links(text):
  if not text or text == "null":
    return ""
  # Regex to convert markdown links [text](url) to HTML <a href="url">text</a>
  pattern = r"\[(.*?)\]\((https?://.*?)\)"
  replacement = r'<a href="\2" style="color: #1a73e8; text-decoration: none; font-weight: 500;">\1</a>'
  return re.sub(pattern, replacement, str(text))


def render_html_email(raw_data, account_name="Cloud Blockers Report"):
  rows = []
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
      # Check if it's a markdown table
      for line in lines:
        if line.startswith("|") and not line.startswith("| #") and not "---" in line:
          parts = [p.strip() for p in line.split("|")[1:-1]]
          if len(parts) >= 10:
            rows.append(parts)

  total_count = len(rows)

  html = []
  html.append("""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; color: #202124; }
  .card { max-width: 960px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #dadce0; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
  .header { padding: 24px; background: #1a73e8; color: #ffffff; }
  .header h1 { margin: 0 0 8px 0; font-size: 20px; font-weight: 600; }
  .header-meta { font-size: 13px; opacity: 0.9; }
  .stats-bar { display: flex; gap: 16px; padding: 16px 24px; background: #e8f0fe; border-bottom: 1px solid #dadce0; font-size: 13px; color: #174ea6; font-weight: 500; }
  .table-container { padding: 20px 24px; overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }
  th { background-color: #f1f3f4; color: #3c4043; padding: 10px 12px; font-weight: 600; border-bottom: 2px solid #dadce0; white-space: nowrap; }
  td { padding: 10px 12px; border-bottom: 1px solid #e8eaed; vertical-align: top; color: #3c4043; line-height: 1.4; }
  tr:hover { background-color: #f8f9fa; }
  .badge { display: inline-block; padding: 3px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
  .badge-s0 { background: #fce8e6; color: #c5221f; }
  .badge-s1 { background: #feefc3; color: #b06000; }
  .badge-s2 { background: #e8f0fe; color: #1a73e8; }
  .badge-s3 { background: #f1f3f4; color: #5f6368; }
  .badge-triaged { background: #e6f4ea; color: #137333; }
  .badge-pending { background: #fef7e0; color: #b06000; }
  .footer { padding: 16px 24px; background: #f8f9fa; border-top: 1px solid #dadce0; font-size: 12px; color: #70757a; text-align: center; }
</style>
</head>
<body>
<div class="card">
""")

  html.append(f"""
  <div class="header">
    <h1>📊 Cloud Blockers & Customer Requests Report</h1>
    <div class="header-meta">Filter Scope: <strong>{account_name}</strong></div>
  </div>
  <div class="stats-bar">
    <div><strong>Total Records:</strong> {total_count}</div>
    <div><strong>Data Source:</strong> PLX F1 + Buganizer issuestatsfresh</div>
  </div>
  <div class="table-container">
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>CR Buganizer ID</th>
          <th>Admin Link</th>
          <th>CR Title</th>
          <th>Severity</th>
          <th>Created Date</th>
          <th>Requester</th>
          <th>Age</th>
          <th>Triage Status</th>
          <th>Cloud Blocker Title</th>
          <th>Resolution Status</th>
          <th>CB Buganizer ID</th>
        </tr>
      </thead>
      <tbody>
""")

  for idx, r in enumerate(rows, start=1):
    if len(r) < 10:
      continue

    # Extract key fields safely
    cr_id_link = parse_markdown_links(r[1] if len(r) > 1 else "")
    admin_link = parse_markdown_links(r[2] if len(r) > 2 else "")
    cr_title = (
        r[3].replace("\n", " ").replace("[", "").replace("]", "")
        if len(r) > 3
        else ""
    )
    severity = r[4] if len(r) > 4 else ""
    created_date = r[5] if len(r) > 5 else ""
    requester = r[6] if len(r) > 6 else ""
    days_old = r[7] if len(r) > 7 else ""
    triage_status = r[8] if len(r) > 8 else ""

    # Look for Cloud Blocker details (columns 14, 15, 16)
    cb_title = r[14] if len(r) > 14 and r[14] != "null" else ""
    cb_status = r[15] if len(r) > 15 and r[15] != "null" else ""
    cb_id_link = (
        parse_markdown_links(r[16]) if len(r) > 16 and r[16] != "null" else ""
    )

    sev_badge_cls = f"badge-{severity.lower()}" if severity else "badge-s3"
    triage_badge_cls = (
        "badge-triaged"
        if "Triaged" in triage_status and not "Pending" in triage_status
        else "badge-pending"
    )

    html.append(f"""
        <tr>
          <td><strong>{idx}</strong></td>
          <td>{cr_id_link or 'N/A'}</td>
          <td>{admin_link or 'N/A'}</td>
          <td><strong>{cr_title}</strong></td>
          <td><span class="badge {sev_badge_cls}">{severity or 'N/A'}</span></td>
          <td>{created_date}</td>
          <td><code>{requester}</code></td>
          <td>{days_old}d</td>
          <td><span class="badge {triage_badge_cls}">{triage_status}</span></td>
          <td>{cb_title or 'N/A'}</td>
          <td><em>{cb_status or 'N/A'}</em></td>
          <td>{cb_id_link or 'N/A'}</td>
        </tr>
""")

  html.append("""
      </tbody>
    </table>
  </div>
  <div class="footer">
    Generated automatically by <strong>ce-skills</strong> Cloud Blockers Skill via PLX F1.
  </div>
</div>
</body>
</html>
""")

  return "".join(html)


def main():
  parser = argparse.ArgumentParser(
      description="Render PLX Output or Markdown Report into Email HTML"
  )
  parser.add_argument(
      "--input-file",
      "-i",
      default="-",
      help="Path to input TSV/JSON/Markdown file (use '-' for stdin)",
  )
  parser.add_argument(
      "--output-file", "-o", help="Path to write formatted HTML file"
  )
  parser.add_argument(
      "--account-name", default="Cloud Blockers Report", help="Report Scope Name"
  )

  args = parser.parse_args()

  if args.input_file == "-":
    content = sys.stdin.read()
  else:
    with open(args.input_file, "r") as f:
      content = f.read()

  html_out = render_html_email(content, account_name=args.account_name)

  if args.output_file:
    with open(args.output_file, "w") as f:
      f.write(html_out)
    print(f"Successfully generated HTML email artifact: {args.output_file}")
  else:
    print(html_out)


if __name__ == "__main__":
  main()
