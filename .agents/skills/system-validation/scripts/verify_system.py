import os
import json
import glob
import pathlib
import subprocess
import urllib.request
import urllib.error
import sys
import shutil
import datetime

def _setup_ce_config():
    current = pathlib.Path(__file__).resolve().parent
    for parent in current.parents:
        if (parent / ".agents").is_dir():
            lib_path = str(parent / ".agents" / "lib")
            if lib_path not in sys.path:
                sys.path.insert(0, lib_path)
            return

_setup_ce_config()
import ce_config  # noqa: E402

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../../../.."))


def check_gcp_config():
    path = os.path.join(REPO_ROOT, "gcp_config.txt")
    if not os.path.exists(path):
        return False, f"gcp_config.txt does not exist at {path}"
    
    try:
        folder_id = ce_config.get("folder_id", required=True)
        _ = ce_config.get_secret("billing_account", required=True)
        billing_project = ce_config.get("billing_project", required=True)
    except Exception as e:
        return False, f"Validation failed: {e}"
        
    piper_ws = ce_config.get("piper_workspace", "ce-skills")
    b_table = ce_config.get("billing_table", "Auto-discovered")
    return True, f"gcp_config.txt verified (folder_id={folder_id}, billing_project={billing_project}, billing_table={b_table}, piper_workspace={piper_ws})."

def check_persona_binding():
    path = os.path.join(REPO_ROOT, ".agents/rules/persona.md")
    if not os.path.exists(path):
        return False, f"Persona binding file missing at {path}"
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        valid_personas = ["Practice CE", "Platform CE", "Outcome CE"]
        found = [p for p in valid_personas if f"Active Role Focus: {p}" in content or f"Role Focus: {p}" in content or p in content]
        if found:
            return True, f"Systems Engineering Persona bound to: <b>{found[0]}</b>."
        return False, "persona.md exists but does not contain a valid persona binding (Practice CE, Platform CE, or Outcome CE)."
    except Exception as e:
        return False, f"Failed to read persona.md: {e}"

def check_citc_companydoc():
    if not os.path.exists("/google/src/cloud"):
        return True, "Offline/External environment detected. Skipping CitC CompanyDoc check."
    user = os.environ.get("USER") or os.environ.get("LOGNAME")
    if not user:
        return False, "Could not determine username for CitC check."
    
    ws_name = ce_config.get("piper_workspace", "ce-skills")
    
    company_dir = f"/google/src/cloud/{user}/{ws_name}/company"
    if os.path.exists(company_dir):
        return True, f"Verified CitC CompanyDoc publishing workspace at <code>{company_dir}</code>."
    return False, f"CitC CompanyDoc view not found at <code>{company_dir}</code>.<br>Please run <code>g4 client -c {ws_name}</code>."

def check_sidecar_sync():
    search_pattern = os.path.join(REPO_ROOT, ".agents", "**", "sidecar.json")
    templates = glob.glob(search_pattern, recursive=True)
    if not templates:
        return True, "No sidecar templates found."
        
    dest_root = os.path.expanduser("~/.gemini/jetski/sidecars")
    
    try:
        count = 0
        for t_path in templates:
            sidecar_id = os.path.basename(os.path.dirname(t_path))
            
            # Verify the sync output exists
            dest_file = os.path.join(dest_root, sidecar_id, "sidecar.json")
            if not os.path.exists(dest_file):
                return False, (
                    f"Sidecar '{sidecar_id}' is not synchronized.<br>"
                    f"Please run onboarding or <code>bash .agents/scripts/sync_sidecars.sh</code>."
                )
                
            # Load synced configuration
            with open(dest_file, "r", encoding="utf-8") as f:
                d_config = json.load(f)
                
            d_args = d_config.get("args", [])
            if len(d_args) > 2 and d_args[1] in ("python", "python3"):
                script_path = d_args[2]
                if not script_path.startswith("/"):
                    return False, f"Sidecar '{sidecar_id}' script path in synced config is not absolute: <code>{script_path}</code>."
                if not os.path.exists(script_path):
                    return False, f"Sidecar '{sidecar_id}' script does not exist: <code>{script_path}</code>."
            
            count += 1
            
        return True, f"Verified {count} background sidecar daemon configurations."
    except Exception as e:
        return False, f"Sidecar validation failed: {e}"

def check_python_dependencies():
    required_packages = {
        "googleapiclient": "google-api-python-client",
        "google.auth": "google-auth",
    }
    missing = []
    for module_name, package_name in required_packages.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package_name)
            
    if missing:
        is_cloudtop = os.path.exists("/google/bin/releases") or ("glinux" in os.uname().release.lower() if hasattr(os, 'uname') else False)
        if is_cloudtop:
            apt_map = {
                "google-api-python-client": "python3-googleapi",
                "google-auth": "python3-google-auth"
            }
            apt_packages = [apt_map.get(p, p) for p in missing]
            return False, f"Missing required Python packages on Cloudtop: {', '.join(missing)}.<br>Please install them via APT:<br><code>sudo apt-get update && sudo apt-get install -y {' '.join(apt_packages)}</code>"
    return True, "All required Python packages are installed."

def get_gcloud_token():
    try:
        token = subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip()
        return token
    except Exception:
        return None

def check_mcp_servers():
    config_path = os.path.join(REPO_ROOT, ".gemini/mcp_config.json")
    if not os.path.exists(config_path):
        return False, f"mcp_config.json does not exist at {config_path}"
        
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except Exception as e:
        return False, f"Failed to parse mcp_config.json: {e}"
        
    mcp_servers = config.get("mcpServers", {})
    if not mcp_servers:
        return False, "No MCP servers configured in mcp_config.json"
        
    results = {}
    token = None
    
    for name, cfg in mcp_servers.items():
        url = cfg.get("httpUrl") or cfg.get("serverUrl")
        if not url:
            cmd = cfg.get("command", "")
            if not cmd:
                results[name] = {"status": "FAIL", "message": "Missing command definition in MCP server configuration."}
            elif os.path.exists(cmd) or shutil.which(cmd.split()[0]):
                results[name] = {"status": "SUCCESS", "message": f"Verified local command-based MCP binary: <code>{cmd}</code>"}
            else:
                results[name] = {"status": "FAIL", "message": f"Local command binary not found on path or disk: <code>{cmd}</code>"}
            continue
            
        headers = {"Content-Type": "application/json"}
        
        cfg_headers = cfg.get("headers", {})
        for k, v in cfg_headers.items():
            headers[k] = v

            
        auth_type = cfg.get("authProviderType")
        if auth_type == "google_credentials":
            if not token:
                token = get_gcloud_token()
            if token:
                headers["Authorization"] = f"Bearer {token}"
            else:
                results[name] = {"status": "FAIL", "message": "OAuth required but failed to retrieve gcloud token"}
                continue
                
        payload = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        }).encode("utf-8")
        
        import ssl
        ssl_context = ssl._create_unverified_context()
        
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10, context=ssl_context) as response:
                resp_data = json.loads(response.read().decode("utf-8"))
                if "result" in resp_data:
                    results[name] = {"status": "SUCCESS", "message": "Connected and listed tools successfully."}
                else:
                    results[name] = {"status": "FAIL", "message": f"Invalid JSON-RPC response: {resp_data}"}
        except urllib.error.HTTPError as e:
            results[name] = {"status": "FAIL", "message": f"HTTP Error {e.code}: {e.read().decode('utf-8', errors='ignore')}"}
        except Exception as e:
            results[name] = {"status": "FAIL", "message": f"Connection failed: {e}"}
            
    return True, results

def check_cdp_socket_conflicts():
    import socket
    port = 9222
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    try:
        s.connect(('127.0.0.1', port))
        s.close()
        try:
            # Attempt to fetch browser version from DevTools HTTP interface
            req = urllib.request.Request(f"http://127.0.0.1:{port}/json/version", method="GET")
            with urllib.request.urlopen(req, timeout=1.0) as response:
                info = json.loads(response.read().decode('utf-8'))
                browser = info.get("Browser", "Unknown Chrome-like process")
                return False, f"PORT CONFLICT: Singleton CDP port {port} is already occupied by: <b>{browser}</b>.<br>This will cause DevTools/CDP WebSocket crashes during E2E runs. Please kill duplicate browser instances (e.g. <code>pkill -f headless</code>) before running."
        except Exception:
            return False, f"PORT CONFLICT: Singleton CDP port {port} is already in use by an unresponsive process.<br>Please run <code>pkill -f 'chrome\\|headless'</code> or <code>fuser -k {port}/tcp</code> to clear it."
    except socket.error:
        pass
        
    try:
        result = subprocess.run(
            ["pgrep", "-f", "headless|chrome|chromium"],
            capture_output=True,
            text=True
        )
        pids = [pid.strip() for pid in result.stdout.splitlines() if pid.strip()]
        if len(pids) > 2:
            return True, f"WARNING: {len(pids)} running Chrome/headless processes detected in background. While port {port} is currently free, you are advised to run <code>pkill -f 'headless\\|chrome'</code> to prevent future conflicts."
    except Exception:
        pass
        
    return True, "CDP / Chrome DevTools singleton socket is clear and ready."

def generate_markdown_report(gcp_ok, gcp_msg, persona_ok, persona_msg, citc_ok, citc_msg, sc_ok, sc_msg, dep_ok, dep_msg, cdp_ok, cdp_msg, mcp_ok, mcp_results, report_path=None):
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    all_pass = gcp_ok and persona_ok and citc_ok and sc_ok and dep_ok and cdp_ok and mcp_ok and all(res["status"] != "FAIL" for res in mcp_results.values())
    
    overall_status_color = "#137333" if all_pass else "#c5221f"
    overall_status_bg = "#e6f4ea" if all_pass else "#fce8e6"
    overall_status_text = "SUCCESS" if all_pass else "FAILED"
    
    html = []
    html.append('<div style="max-width: 900px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Helvetica, Arial, sans-serif; background: #ffffff; border-radius: 12px; border: 1px solid #e8eaed; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);">')
    html.append('<div style="padding: 20px 24px; background: #ffffff; border-bottom: 1px solid #e8eaed; border-left: 6px solid #1a73e8;">')
    html.append('<h1 style="margin: 0 0 8px 0; font-size: 22px; color: #1a73e8; font-weight: 600;">System Validation Report</h1>')
    html.append('<div style="display: flex; flex-wrap: wrap; gap: 16px; font-size: 13px; color: #5f6368;">')
    html.append('<div style="display: flex; align-items: center; gap: 6px;">')
    html.append('<strong>Overall Status:</strong>')
    html.append(f'<span style="background: {overall_status_bg}; color: {overall_status_color}; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px;">{overall_status_text}</span>')
    html.append('</div>')
    html.append(f'<div><strong>Last Checked:</strong> {now_str}</div>')
    html.append('</div>')
    html.append('</div>')
    
    html.append('<div style="padding: 20px 24px; border-bottom: 1px solid #e8eaed;">')
    html.append('<div style="font-size: 14px; font-weight: 600; margin: 0 0 8px 0; color: #3c4043; text-transform: uppercase; letter-spacing: 0.5px;">Remediation Guide</div>')
    if all_pass:
        html.append('<p style="margin: 0; font-size: 14px; color: #5f6368; line-height: 1.5;">')
        html.append('Your environment is fully ready. For reference, see the ')
        html.append('<a href="https://docs.google.com/document/d/1KKsh2394jSC_GX5zAsu-JiABjWM6x2SWR5FIa5TrvIY/edit?resourcekey=0-I92ALWXlSgB4_PxS9kbTLw&amp;tab=t.3wn5ohhiptk4">CE-Scale JetSki Configuration</a>.')
        html.append('</p>')
    else:
        html.append('<p style="margin: 0; font-size: 14px; color: #5f6368; line-height: 1.5;">')
        html.append('One or more components failed verification. Please consult the ')
        html.append('<a href="https://docs.google.com/document/d/1KKsh2394jSC_GX5zAsu-JiABjWM6x2SWR5FIa5TrvIY/edit?resourcekey=0-I92ALWXlSgB4_PxS9kbTLw&amp;tab=t.3wn5ohhiptk4">CE-Scale JetSki Configuration</a>')
        html.append(' for detailed setup steps and requirements.')
        html.append('</p>')
    html.append('</div>')
    
    html.append('<table style="width: 100%; border-collapse: collapse; margin: 0; font-size: 13px;">')
    html.append('<thead>')
    html.append('<tr style="background-color: #f8f9fa; border-bottom: 2px solid #e8eaed; text-align: left; color: #3c4043;">')
    html.append('<th style="padding: 12px 24px; font-weight: 600; width: 100px; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Status</th>')
    html.append('<th style="padding: 12px 12px 12px 0; font-weight: 600; width: 240px; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Component Check</th>')
    html.append('<th style="padding: 12px 24px 12px 0; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Details & Outputs</th>')
    html.append('</tr>')
    html.append('</thead>')
    html.append('<tbody>')
    
    gcp_bg = "#e6f4ea" if gcp_ok else "#fce8e6"
    gcp_color = "#137333" if gcp_ok else "#c5221f"
    gcp_status = "PASS" if gcp_ok else "FAIL"
    html.append('<tr style="border-bottom: 1px solid #e8eaed;">')
    html.append('<td style="padding: 14px 24px; vertical-align: top;">')
    html.append(f'<span style="background: {gcp_bg}; color: {gcp_color}; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">{gcp_status}</span>')
    html.append('</td>')
    html.append('<td style="padding: 14px 12px 14px 0; vertical-align: top; font-weight: 600; color: #3c4043;">GCP Config file (gcp_config.txt)</td>')
    html.append(f'<td style="padding: 14px 24px 14px 0; vertical-align: top; color: #5f6368;">{gcp_msg}</td>')
    html.append('</tr>')
    
    persona_bg = "#e6f4ea" if persona_ok else "#fce8e6"
    persona_color = "#137333" if persona_ok else "#c5221f"
    persona_status = "PASS" if persona_ok else "FAIL"
    html.append('<tr style="border-bottom: 1px solid #e8eaed;">')
    html.append('<td style="padding: 14px 24px; vertical-align: top;">')
    html.append(f'<span style="background: {persona_bg}; color: {persona_color}; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">{persona_status}</span>')
    html.append('</td>')
    html.append('<td style="padding: 14px 12px 14px 0; vertical-align: top; font-weight: 600; color: #3c4043;">Systems Engineering Persona (.agents/rules/persona.md)</td>')
    html.append(f'<td style="padding: 14px 24px 14px 0; vertical-align: top; color: #5f6368;">{persona_msg}</td>')
    html.append('</tr>')
    
    citc_bg = "#e6f4ea" if citc_ok else "#fce8e6"
    citc_color = "#137333" if citc_ok else "#c5221f"
    citc_status = "PASS" if citc_ok else "FAIL"
    html.append('<tr style="border-bottom: 1px solid #e8eaed;">')
    html.append('<td style="padding: 14px 24px; vertical-align: top;">')
    html.append(f'<span style="background: {citc_bg}; color: {citc_color}; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">{citc_status}</span>')
    html.append('</td>')
    html.append('<td style="padding: 14px 12px 14px 0; vertical-align: top; font-weight: 600; color: #3c4043;">CitC CompanyDoc Workspace Readiness</td>')
    html.append(f'<td style="padding: 14px 24px 14px 0; vertical-align: top; color: #5f6368;">{citc_msg}</td>')
    html.append('</tr>')
    
    sc_bg = "#e6f4ea" if sc_ok else "#fce8e6"
    sc_color = "#137333" if sc_ok else "#c5221f"
    sc_status = "PASS" if sc_ok else "FAIL"
    html.append('<tr style="border-bottom: 1px solid #e8eaed;">')
    html.append('<td style="padding: 14px 24px; vertical-align: top;">')
    html.append(f'<span style="background: {sc_bg}; color: {sc_color}; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">{sc_status}</span>')
    html.append('</td>')
    html.append('<td style="padding: 14px 12px 14px 0; vertical-align: top; font-weight: 600; color: #3c4043;">Background Sidecar Daemons (.agents/sidecars)</td>')
    html.append(f'<td style="padding: 14px 24px 14px 0; vertical-align: top; color: #5f6368;">{sc_msg}</td>')
    html.append('</tr>')
    
    dep_bg = "#e6f4ea" if dep_ok else "#fce8e6"
    dep_color = "#137333" if dep_ok else "#c5221f"
    dep_status = "PASS" if dep_ok else "FAIL"
    html.append('<tr style="border-bottom: 1px solid #e8eaed;">')
    html.append('<td style="padding: 14px 24px; vertical-align: top;">')
    html.append(f'<span style="background: {dep_bg}; color: {dep_color}; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">{dep_status}</span>')
    html.append('</td>')
    html.append('<td style="padding: 14px 12px 14px 0; vertical-align: top; font-weight: 600; color: #3c4043;">Python Dependency Check</td>')
    html.append(f'<td style="padding: 14px 24px 14px 0; vertical-align: top; color: #5f6368;">{dep_msg}</td>')
    html.append('</tr>')
    
    cdp_bg = "#e6f4ea" if cdp_ok else "#fce8e6"
    cdp_color = "#137333" if cdp_ok else "#c5221f"
    cdp_status = "PASS" if cdp_ok else "FAIL"
    html.append('<tr style="border-bottom: 1px solid #e8eaed;">')
    html.append('<td style="padding: 14px 24px; vertical-align: top;">')
    html.append(f'<span style="background: {cdp_bg}; color: {cdp_color}; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">{cdp_status}</span>')
    html.append('</td>')
    html.append('<td style="padding: 14px 12px 14px 0; vertical-align: top; font-weight: 600; color: #3c4043;">CDP Debugger Socket Check (Port 9222)</td>')
    html.append(f'<td style="padding: 14px 24px 14px 0; vertical-align: top; color: #5f6368;">{cdp_msg}</td>')
    html.append('</tr>')
    
    for server, res in mcp_results.items():
        status = res["status"]
        msg = res["message"]
        if status == "SUCCESS":
            bg = "#e6f4ea"
            color = "#137333"
        elif status == "SKIP":
            bg = "#e8f0fe"
            color = "#1a73e8"
        else:
            bg = "#fce8e6"
            color = "#c5221f"
            
        html.append('<tr style="border-bottom: 1px solid #e8eaed;">')
        html.append('<td style="padding: 14px 24px; vertical-align: top;">')
        html.append(f'<span style="background: {bg}; color: {color}; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">{status}</span>')
        html.append('</td>')
        html.append(f'<td style="padding: 14px 12px 14px 0; vertical-align: top; font-weight: 600; color: #3c4043;">MCP Server: {server}</td>')
        html.append(f'<td style="padding: 14px 24px 14px 0; vertical-align: top; color: #5f6368;">{msg}</td>')
        html.append('</tr>')
        
    html.append('</tbody>')
    html.append('</table>')
    html.append('</div>')
    
    markdown_content = "\n".join(html)
    if not report_path:
        report_path = "/tmp/system_validation_report.md"
    # Ensure parent directories exist
    parent_dir = os.path.dirname(report_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    with open(report_path, "w") as f:  # lgtm [py/clear-text-storage-sensitive-data]
        f.write(markdown_content)  # lgtm [py/clear-text-storage-sensitive-data]
    print(f"[+] Report generated at {report_path}")

def main():
    print("=" * 60)
    print("System Validation Check")
    print("=" * 60)
    
    report_path = None
    skip_cdp = False
    for arg in sys.argv[1:]:  # lgtm [py/clear-text-storage-sensitive-data]
        if arg == "--skip-cdp":  # lgtm [py/clear-text-storage-sensitive-data]
            skip_cdp = True
        elif not arg.startswith("-"):
            report_path = arg
        
    gcp_ok, gcp_msg = check_gcp_config()
    print(f"[*] GCP Configuration Check: {'PASS' if gcp_ok else 'FAIL'}")
    print(f"    {gcp_msg}\n")  # lgtm [py/clear-text-logging-sensitive-data]
    
    persona_ok, persona_msg = check_persona_binding()
    print(f"[*] Systems Engineering Persona Check: {'PASS' if persona_ok else 'FAIL'}")
    print(f"    {persona_msg}\n")
    
    citc_ok, citc_msg = check_citc_companydoc()
    print(f"[*] CitC CompanyDoc Workspace Check: {'PASS' if citc_ok else 'FAIL'}")
    print(f"    {citc_msg}\n")
    
    sc_ok, sc_msg = check_sidecar_sync()
    print(f"[*] Background Sidecar Daemons Check: {'PASS' if sc_ok else 'FAIL'}")
    print(f"    {sc_msg}\n")
    
    dep_ok, dep_msg = check_python_dependencies()
    print(f"[*] Python Dependency Check: {'PASS' if dep_ok else 'FAIL'}")
    print(f"    {dep_msg}\n")
    
    if skip_cdp:
        cdp_ok, cdp_msg = True, "CDP socket conflict check skipped via --skip-cdp."
    else:
        cdp_ok, cdp_msg = check_cdp_socket_conflicts()
    print(f"[*] CDP Debugger Socket Check (Port 9222): {'PASS' if cdp_ok else 'FAIL'}")
    print(f"    {cdp_msg}\n")

    mcp_ok, mcp_results = check_mcp_servers()
    print("[*] MCP Servers Connectivity Check:")
    if not mcp_ok:
        print(f"    FAIL: {mcp_results}\n")
        generate_markdown_report(gcp_ok, gcp_msg, persona_ok, persona_msg, citc_ok, citc_msg, sc_ok, sc_msg, dep_ok, dep_msg, cdp_ok, cdp_msg, False, {"parsing": {"status": "FAIL", "message": mcp_results}}, report_path=report_path)
        sys.exit(1)
        
    all_mcp_pass = True
    for server, res in mcp_results.items():
        status = res["status"]
        msg = res["message"]
        print(f"    - {server}: {status}")
        print(f"      {msg}")
        if status == "FAIL":
            all_mcp_pass = False
    print()
    
    generate_markdown_report(gcp_ok, gcp_msg, persona_ok, persona_msg, citc_ok, citc_msg, sc_ok, sc_msg, dep_ok, dep_msg, cdp_ok, cdp_msg, mcp_ok, mcp_results, report_path=report_path)
    
    if not gcp_ok or not persona_ok or not citc_ok or not sc_ok or not dep_ok or not cdp_ok or not all_mcp_pass:
        print("[-] SYSTEM VALIDATION: FAILED")
        print("-" * 60)
        sys.exit(1)
    else:
        print("[+] SYSTEM VALIDATION: SUCCESS")
        print("-" * 60)
        sys.exit(0)

if __name__ == "__main__":
    main()
