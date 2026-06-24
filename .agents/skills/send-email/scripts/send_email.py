#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import sys
import tempfile
import time

def run_command(cmd_args, retries=3, backoff=2):
    """Runs a system command safely without shell, with dynamic exponential backoff retries for remote SSH/SCP calls."""
    is_remote = len(cmd_args) > 0 and cmd_args[0] in ["ssh", "scp"]
    
    for attempt in range(retries):
        try:
            result = subprocess.run(
                cmd_args,
                shell=False,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            if is_remote and result.returncode == 255:
                raise subprocess.SubprocessError(f"SSH/SCP connection failure (code 255): {result.stderr.strip()}")
                
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            if is_remote and attempt < retries - 1:
                sleep_time = backoff * (2 ** attempt)
                print(f"⚠️ Network Bridge Warning: Remote execution attempt {attempt+1} failed: {e}. Retrying in {sleep_time}s...", file=sys.stderr)
                time.sleep(sleep_time)
            else:
                return False, "", str(e)

def load_gcp_config():
    """Recursively searches parent directories for gcp_config.txt and parses configuration key-values."""
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

def markdown_to_html(md_text):
    """Converts simple Markdown formatting and tables into styled premium corporate HTML."""
    if not md_text:
        return ""
    
    # Style definitions for stunning Google Cloud look
    style_block = """
    <style>
        body {
            font-family: 'Outfit', 'Inter', 'Segoe UI', Roboto, Helvetica, sans-serif;
            color: #202124;
            line-height: 1.6;
            background-color: #f4f6f8;
            padding: 20px;
        }
        .report-card {
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.06);
            border: 1px solid #e0e0e0;
            padding: 30px;
            max-width: 850px;
            margin: 0 auto;
        }
        h2 {
            color: #1a73e8;
            font-weight: 600;
            margin-top: 0;
            margin-bottom: 16px;
            border-bottom: 1px solid #dadce0;
            padding-bottom: 12px;
            font-size: 20px;
        }
        h3 {
            color: #3c4043;
            font-weight: 500;
            margin-top: 24px;
            margin-bottom: 12px;
            font-size: 16px;
        }
        hr {
            border: 0;
            border-top: 1px solid #dadce0;
            margin: 24px 0;
        }
        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin: 20px 0;
            font-size: 13px;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #dadce0;
        }
        th {
            background-color: #1a73e8;
            color: #ffffff;
            font-weight: 600;
            text-align: left;
            padding: 12px 16px;
            border-bottom: 2px solid #1557b0;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        td {
            padding: 12px 16px;
            border-bottom: 1px solid #e0e0e0;
            color: #3c4043;
            background-color: #ffffff;
        }
        tr:nth-child(even) td {
            background-color: #f8f9fa;
        }
        tr:hover td {
            background-color: #f1f3f4 !important;
        }
        tr:last-child td {
            border-bottom: none;
        }
        ul {
            padding-left: 20px;
            margin: 10px 0;
        }
        li {
            margin-bottom: 6px;
            color: #5f6368;
        }
        code {
            background-color: #f1f3f4;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Roboto Mono', monospace;
            font-size: 12px;
            color: #c5221f;
        }
        .dimmed {
            color: #bdc1c6;
            font-weight: 300;
        }
    </style>
    """
    
    html = md_text
    
    # Parse standard inline styles
    # Bold: **text**
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    # Inline Code: `code`
    html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)
    
    # Replace custom alert blocks
    html = re.sub(r'>\s*\[!NOTE\]\s*\n>\s*(.*)', r'<div style="background-color: #fef7e0; border-left: 4px solid #f9ab00; padding: 12px; border-radius: 4px; margin: 15px 0; font-size: 13px; color: #3c4043;"><strong>Note:</strong> \1</div>', html)
    html = re.sub(r'>\s*\[!IMPORTANT\]\s*\n>\s*(.*)', r'<div style="background-color: #fce8e6; border-left: 4px solid #d93025; padding: 12px; border-radius: 4px; margin: 15px 0; font-size: 13px; color: #3c4043;"><strong>Important:</strong> \1</div>', html)
    
    # Parse list items: * text
    html = re.sub(r'^\*\s+(.*)', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'(<li>.*?</li>)+', lambda m: f"<ul>{m.group(0)}</ul>", html, flags=re.DOTALL)
    
    # Parse markdown dividers (---)
    html = re.sub(r'^---$', r'<hr>', html, flags=re.MULTILINE)
    
    # Parse headers
    html = re.sub(r'^## (.*)', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.*)', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    
    # Parse tables
    lines = html.splitlines()
    table_started = False
    in_header = True
    table_rows = []
    parsed_lines = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('|'):
            table_started = True
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if all(c == '---' or c.startswith(':---') for c in cells):
                in_header = False
                continue
            table_rows.append((in_header, cells))
        else:
            if table_started:
                table_html = ["<table>"]
                for is_hdr, cells in table_rows:
                    tag = "th" if is_hdr else "td"
                    cell_html = ""
                    for c in cells:
                        cell_val = c
                        if c == '∅':
                            cell_val = '<span class="dimmed">∅</span>'
                        cell_html += f"<{tag}>{cell_val}</{tag}>"
                    table_html.append(f"<tr>{cell_html}</tr>")
                table_html.append("</table>")
                parsed_lines.append("\n".join(table_html))
                table_started = False
                in_header = True
                table_rows = []
            
            parsed_lines.append(line)
            
    # Flush remaining table at EOF
    if table_started:
        table_html = ["<table>"]
        for is_hdr, cells in table_rows:
            tag = "th" if is_hdr else "td"
            cell_html = ""
            for c in cells:
                cell_val = c
                if c == '∅':
                    cell_val = '<span class="dimmed">∅</span>'
                cell_html += f"<{tag}>{cell_val}</{tag}>"
            table_html.append(f"<tr>{cell_html}</tr>")
        table_html.append("</table>")
        parsed_lines.append("\n".join(table_html))
        
    final_body = "\n".join(parsed_lines)
    
    # Convert double line breaks to HTML breaks
    final_body = re.sub(r'\n{2,}', '<br><br>', final_body)
    
    return f"<html><head>{style_block}</head><body><div class='report-card'>{final_body}</div></body></html>"

def verify_active_account():
    """Verifies that the active gcloud account is a corporate @google.com account."""
    try:
        active_account = subprocess.check_output(
            ["gcloud", "config", "get-value", "account"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        if not active_account.endswith("@google.com"):
            print(f"❌ Error: Active gcloud account [{active_account}] is not a corporate @google.com employee account.", file=sys.stderr)
            print("This corporate skill requires access to internal Google Workspace API endpoints.", file=sys.stderr)
            print("Please switch to your corporate account in your terminal first by running:\n", file=sys.stderr)
            print("    gcloud config set account <ldap>@google.com\n", file=sys.stderr)
            return False
        return True
    except Exception:
        return True

def send_email_api(to, subject, body_or_path, is_html=False, attachment=None):
    """Generic programmatic helper function that can be imported natively by other Python skills.
    Uses the Google Message Router (sendgmr) natively via local LOAS credentials to avoid gcloud auth changes.
    """
    sendgmr_bin = "/google/bin/releases/gws-sre/files/sendgmr/sendgmr"
    
    # ENVIRONMENT AWARENESS CHECK: Are we running natively on Cloudtop?
    is_running_on_cloudtop = os.path.exists(sendgmr_bin)
    
    if not is_running_on_cloudtop:
        print("❌ Error: This skill can only be executed natively on a Google Cloudtop workstation.", file=sys.stderr)
        print("For security and compliance, remote execution via the SSH Bridge has been disabled.", file=sys.stderr)
        return False
        
    # Resolve body content (check if it's a local file path)
    body_content = body_or_path
    if os.path.exists(body_or_path):
        try:
            with open(body_or_path, 'r', encoding='utf-8') as f:
                body_content = f.read()
        except Exception as e:
            print(f"⚠️ Warning: Failed to read body file {body_or_path}, treating as raw text: {e}")
            
    # Build the command arguments
    cmd_args = [
        sendgmr_bin,
        f"-to={to}",
        f"-subject={subject}"
    ]
    
    temp_html_file = None
    temp_text_file = None
    try:
        # Write body_content to a temporary plain text file for -body_file
        temp_text_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
        temp_text_file.write(body_content)
        temp_text_file.close()
        
        cmd_args.append(f"-body_file={temp_text_file.name}")
        
        if is_html:
            html_payload = markdown_to_html(body_content)
            # Write to a temporary file because sendgmr requires a file path for -html_file
            temp_html_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8')
            temp_html_file.write(html_payload)
            temp_html_file.close()
            
            cmd_args.append(f"-html_file={temp_html_file.name}")
            
        if attachment:
            cmd_args.append(f"-attachment_files={attachment}")
            
        print("⚡ Environment Detected: Running natively on Cloudtop. Routing email securely via Google Message Router (sendgmr)...")
        success, stdout, stderr = run_command(cmd_args)
        
        if success:
            print("🚀 Success! Email natively sent via GMR using your active LOAS credentials.")
            return True
        else:
            print(f"❌ sendgmr failed locally on Cloudtop:\n{stderr or stdout}", file=sys.stderr)
            if "loas" in (stderr + stdout).lower() or "cert" in (stderr + stdout).lower():
                print("\n💡 Setup Tip: Your local LOAS credentials or gcert session might have expired.", file=sys.stderr)
                print("Please run `gcert` in your Cloudtop terminal to refresh your session.", file=sys.stderr)
            return False
            
    finally:
        # Clean up temporary files
        if temp_html_file and os.path.exists(temp_html_file.name):
            try:
                os.unlink(temp_html_file.name)
            except OSError:
                pass
        if temp_text_file and os.path.exists(temp_text_file.name):
            try:
                os.unlink(temp_text_file.name)
            except OSError:
                pass

def main():
    parser = argparse.ArgumentParser(
        description="Generic Remote Cloudtop SSH Gmail Sender. Relays beautiful reports natively and securely.",
        epilog="""
Examples:
  # Send simple text email:
  python3 send_email.py --to "user@example.com" --subject "Alert" --body "Test message"

  # Send Markdown report as beautifully styled HTML:
  python3 send_email.py --to "user@example.com" --subject "Spend Review" --body "artifacts/mtd_billing_audit.md" --html

  # Send email with attachment:
  python3 send_email.py --to "user@example.com" --subject "Audit" --body "Attached" --attachment "artifacts/mtd_billing_audit.md"
"""
    )
    
    parser.add_argument("--to", required=True, help="Comma-separated list of recipient email addresses.")
    parser.add_argument("--subject", required=True, help="Subject line of the email.")
    parser.add_argument("--body", required=True, help="Raw email message text, or a path to a local text/markdown file.")
    parser.add_argument("--html", action="store_true", help="Format the body as a beautiful HTML email.")
    parser.add_argument("--attachment", help="Optional local file path to attach to the email.")
    
    args = parser.parse_args()
    
    send_email_api(
        to=args.to,
        subject=args.subject,
        body_or_path=args.body,
        is_html=args.html,
        attachment=args.attachment
    )

if __name__ == "__main__":
    main()
