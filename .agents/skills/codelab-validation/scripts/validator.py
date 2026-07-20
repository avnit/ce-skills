#!/usr/bin/env python3
"""Orchestration script for E2E Codelab Validation.

This script fetches/copies the codelab, provisions a temporary GCP project if needed,
runs the stateful tester, and compiles a comprehensive validation report.
All run-specific inputs and outputs are stored inside the `labs/validate/` subdirectory under the repository root.
"""

import argparse
import datetime
import json
import os
import random
import re
import shutil
import subprocess
import sys
import urllib.request
import html
from html.parser import HTMLParser

# Resolve repository root dynamically
_script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(_script_dir, "..", "..", "..", ".."))

# Run-specific paths will be determined dynamically inside main()

def clean_filename(name):
    """Sanitizes a string for use in filenames."""
    return re.sub(r'[^a-z0-9-]', '', name.lower().strip().replace(' ', '-'))


class CodelabHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script = False
        self.in_style = False
        self.in_title = False
        self.current_header_level = None
        self.in_pre = False
        self.title_text = ""
        self.current_header_text = []
        self.current_pre_text = []
        self.current_pre_attrs = ""
        self.elements = []
        self.full_text = []

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        if tag_lower == 'script':
            self.in_script = True
        elif tag_lower == 'style':
            self.in_style = True
        elif tag_lower == 'title':
            self.in_title = True
        elif tag_lower in ['h1', 'h2', 'h3', 'h4']:
            self.current_header_level = int(tag_lower[1])
            self.current_header_text = []
        elif tag_lower == 'pre':
            self.in_pre = True
            self.current_pre_text = []
            attr_pairs = []
            for name, val in attrs:
                attr_pairs.append(f'{name}="{val}"' if val is not None else name)
            self.current_pre_attrs = " ".join(attr_pairs)

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower == 'script':
            self.in_script = False
        elif tag_lower == 'style':
            self.in_style = False
        elif tag_lower == 'title':
            self.in_title = False
            if self.title_text:
                self.elements.append(('title', self.title_text.strip()))
        elif tag_lower in ['h1', 'h2', 'h3', 'h4']:
            level = int(tag_lower[1])
            if self.current_header_level == level:
                header_str = "".join(self.current_header_text).strip()
                self.elements.append(('header', level, header_str))
            self.current_header_level = None
        elif tag_lower == 'pre':
            self.in_pre = False
            pre_str = "".join(self.current_pre_text).strip()
            self.elements.append(('pre', pre_str, self.current_pre_attrs))
            self.current_pre_attrs = ""

    def handle_data(self, data):
        if self.in_script or self.in_style:
            return
        
        self.full_text.append(data)
        
        if self.in_title:
            self.title_text += data
        elif self.current_header_level is not None:
            self.current_header_text.append(data)
        elif self.in_pre:
            self.current_pre_text.append(data)


def download_url(url):
    """Downloads web content and attempts to extract raw markdown/text."""
    print(f"[Validator] Fetching content from URL: {url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            html_or_text = response.read().decode('utf-8', errors='replace')
            
        # If it looks like HTML, extract pre/code elements or clean it up
        if "<html" in html_or_text.lower():
            print("[Validator] HTML detected, extracting text blocks and commands...")
            parser = CodelabHTMLParser()
            parser.feed(html_or_text)
            
            extracted_lines = []
            for item in parser.elements:
                if item[0] == 'title':
                    extracted_lines.append(f"# {item[1]}")
                    extracted_lines.append("")
                elif item[0] == 'header':
                    level = item[1]
                    prefix = "#" * level
                    extracted_lines.append(f"{prefix} {item[2]}")
                    extracted_lines.append("")
                elif item[0] == 'pre':
                    pre_content = item[1]
                    pre_attrs = item[2]
                    
                    # Unescape standard HTML entities
                    clean_code = html.unescape(pre_content).strip()
                    
                    is_bash = False
                    if "language-bash" in pre_attrs or "lang-bash" in pre_attrs or "bash" in pre_attrs:
                        is_bash = True
                    elif "prettyprint" in pre_attrs:
                        shell_indicators = [
                            r'\bgcloud\b', r'\bbq\b', r'\bgsutil\b', r'\bkubectl\b',
                            r'\bcurl\b', r'\bapt-get\b', r'\becho\b', r'\bcat\b'
                        ]
                        if any(re.search(ind, clean_code) for ind in shell_indicators):
                            is_bash = True
                            
                    if is_bash:
                        extracted_lines.append("```bash")
                        extracted_lines.append(clean_code)
                        extracted_lines.append("```")
                        extracted_lines.append("")
            
            markdown_content = "\n".join(extracted_lines)
            if not markdown_content.strip():
                # Fallback: strip HTML completely and unescape entities
                markdown_content = html.unescape("".join(parser.full_text))
        else:
            # Already text/markdown
            markdown_content = html_or_text
            
        return markdown_content
    except Exception as e:
        print(f"[Validator] Error downloading URL: {e}")
        sys.exit(1)


def scan_placeholders(markdown_path):
    """Parses a markdown file and returns a sorted list of unique bracketed placeholders found in bash blocks."""
    with open(markdown_path, "r", encoding="utf-8") as f:
        content = f.read()
    bash_block_pattern = re.compile(r"```bash\n(.*?)\n[ \t]*```", re.DOTALL)
    bash_blocks = bash_block_pattern.findall(content)
    placeholders = set()
    placeholder_pattern = re.compile(r"<([^>]+)>")
    for block in bash_blocks:
        matches = placeholder_pattern.findall(block)
        for match in matches:
            match_clean = match.strip()
            if match_clean and not any(char in match_clean for char in ['=', ';', '|', '&', '$']):
                placeholders.add(match_clean)
    return sorted(list(placeholders))


def apply_overlay(content, overlay_path):
    """Loads and applies per-lab overlay rules from overlay.json if present.

    Returns (updated_content, applied_rules_summary_list).
    """
    if not os.path.exists(overlay_path):
        return content, []

    print(f"[Validator] Loading overlay file: {overlay_path}")
    try:
        with open(overlay_path, "r", encoding="utf-8") as f:
            overlay_data = json.load(f)
    except Exception as e:
        print(f"[Validator] ERROR: Malformed or unreadable overlay.json at {overlay_path}: {e}")
        sys.exit(1)

    if not isinstance(overlay_data, dict):
        print(f"[Validator] ERROR: Invalid overlay schema at {overlay_path}. Top-level JSON must be an object.")
        sys.exit(1)

    applied_rules = []

    # 1. Apply replacements
    replacements = overlay_data.get("replacements", [])
    if not isinstance(replacements, list):
        print("[Validator] ERROR: 'replacements' in overlay.json must be a list.")
        sys.exit(1)

    for idx, rule in enumerate(replacements):
        if not isinstance(rule, dict) or "find" not in rule or "replace" not in rule:
            print(f"[Validator] ERROR: Invalid replacement rule #{idx+1} in overlay.json. Must contain 'find' and 'replace'.")
            sys.exit(1)

        find_str = rule["find"]
        replace_str = rule["replace"]
        is_regex = rule.get("regex", False)

        if is_regex:
            try:
                new_content = re.sub(find_str, replace_str, content)
            except Exception as re_err:
                print(f"[Validator] ERROR: Invalid regex pattern in overlay.json rule #{idx+1}: {re_err}")
                sys.exit(1)
            if new_content != content:
                content = new_content
                rule_desc = f"Regex replacement: r'{find_str}' -> '{replace_str}'"
                print(f"[Validator] Applied overlay: {rule_desc}")
                applied_rules.append(rule_desc)
            else:
                print(f"[Validator] Overlay rule did not match: Regex r'{find_str}'")
        else:
            if find_str in content:
                content = content.replace(find_str, replace_str)
                rule_desc = f"Literal replacement: '{find_str}' -> '{replace_str}'"
                print(f"[Validator] Applied overlay: {rule_desc}")
                applied_rules.append(rule_desc)
            else:
                print(f"[Validator] Overlay rule did not match: Literal '{find_str}'")

    # 2. Apply append_after_match
    append_rules = overlay_data.get("append_after_match", [])
    if not isinstance(append_rules, list):
        print("[Validator] ERROR: 'append_after_match' in overlay.json must be a list.")
        sys.exit(1)

    for idx, rule in enumerate(append_rules):
        if not isinstance(rule, dict) or "match" not in rule or "append_lines" not in rule:
            print(f"[Validator] ERROR: Invalid append_after_match rule #{idx+1} in overlay.json.")
            sys.exit(1)

        match_str = rule["match"]
        append_lines = rule["append_lines"]
        if not isinstance(append_lines, list):
            print(f"[Validator] ERROR: 'append_lines' in rule #{idx+1} must be a list of strings.")
            sys.exit(1)

        joined_lines = "\n".join(append_lines)
        lines_to_append = "\n" + joined_lines

        def transform_bash_block(block_match):
            block_code = block_match.group(1)
            if match_str in block_code:
                if joined_lines in block_code:
                    return block_match.group(0)
                updated_code = block_code.rstrip() + lines_to_append + "\n"
                return f"```bash\n{updated_code}```"
            return block_match.group(0)

        pattern = re.compile(r'```bash\r?\n(.*?)\r?\n```', re.DOTALL)
        new_content = pattern.sub(transform_bash_block, content)
        if new_content != content:
            content = new_content
            rule_desc = f"Append after match '{match_str}': Appended {len(append_lines)} lines"
            print(f"[Validator] Applied overlay: {rule_desc}")
            applied_rules.append(rule_desc)
        else:
            print(f"[Validator] Overlay rule did not match or already applied: Append after match '{match_str}'")

    return content, applied_rules


def setup_active_lab(src, validate_dir, active_lab_path, resume=False):
    """Prepares the active lab guide inside the dedicated lab validate_dir from local path or web URL."""
    # Resolve absolute path first if local
    local_src = None
    if not (src.startswith("http://") or src.startswith("https://")):
        local_src = os.path.abspath(src)
        if not os.path.exists(local_src):
            print(f"[Validator] Error: Local source file not found at {local_src}")
            sys.exit(1)

    # Clear old state and run files in the dedicated directory to ensure a clean execution environment
    if os.path.exists(validate_dir):
        if resume:
            print(f"[Validator] Resuming previous run. Preserving state files in {validate_dir}...")
        else:
            print(f"[Validator] Cleaning up previous run state from {validate_dir}...")
        for item in os.listdir(validate_dir):
            item_path = os.path.join(validate_dir, item)
            # Do not delete the source file itself, variables.json, or overlay.json!
            if local_src and os.path.exists(item_path) and os.path.samefile(item_path, local_src):
                continue
            if item in ["variables.json", "overlay.json"]:
                continue
            if resume and (item == ".tester_state" or item.endswith(".state") or item.endswith(".env")):
                continue  # Preserve the state folder and environment cache files!
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            except Exception as e:
                print(f"[Warning] Could not remove {item_path}: {e}")

    os.makedirs(validate_dir, exist_ok=True)

    if src.startswith("http://") or src.startswith("https://"):
        content = download_url(src)
        with open(active_lab_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[Validator] Saved downloaded lab to: {active_lab_path}")
    else:
        # If the source is already at the destination, no need to copy!
        if os.path.exists(active_lab_path) and os.path.samefile(local_src, active_lab_path):
            pass
        else:
            shutil.copy2(local_src, active_lab_path)
            print(f"[Validator] Copied local lab to: {active_lab_path}")

    # Append frontmatter if missing to satisfy formatting rules
    with open(active_lab_path, "r+", encoding="utf-8") as f:
        content = f.read()
        if not content.startswith("---"):
            frontmatter = "---\nid: active-lab\nsummary: E2E Validation Run\ncategories: dev\n---\n\n"
            f.seek(0, 0)
            f.write(frontmatter + content)
            print("[Validator] Injected missing metadata frontmatter into codelab guide.")

    # Run dynamic placeholder sanitization and generic engine policies
    with open(active_lab_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Comment out interactive authentication commands to prevent hanging
    content = re.sub(r'(?m)^\s*(gcloud auth login\b)', r'# \1', content)
    content = re.sub(r'(?m)^\s*(gcloud auth application-default login\b)', r'# \1', content)

    # 2. Replace project ID placeholders
    content = re.sub(r'(?i)<your[- ]project[- ]id>', '${PROJECT_ID}', content)
    content = re.sub(r'(?i)<project[- ]id>', '${PROJECT_ID}', content)

    # 3. Comment out bash code blocks inside any sections marked as optional to prevent E2E execution blocks
    def comment_optional_sections(text):
        h2_pattern = re.compile(r'^(##\s+.*)$', re.MULTILINE)
        parts = h2_pattern.split(text)
        for idx in range(1, len(parts), 2):
            header = parts[idx]
            body = parts[idx + 1]
            if "(optional)" in header.lower():
                print(f"[Validator] Commenting out optional section: {header.strip()}")
                body = re.sub(r'```bash\r?\n(.*?)\r?\n```(?:\r?\n|$)', r'# ```bash\n# \1\n# ```\n', body, flags=re.DOTALL)
                parts[idx + 1] = body
        return "".join(parts)

    content = comment_optional_sections(content)

    # 4. Apply per-lab overlay transforms if overlay.json exists
    overlay_path = os.path.join(validate_dir, "overlay.json")
    content, applied_transforms = apply_overlay(content, overlay_path)

    with open(active_lab_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("[Validator] Sanitized and automated active lab placeholders.")

    return applied_transforms


def run_command(command, description="Executing command"):
    print(f"[Validator] {description}: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[Validator] Error during {description}: {e.stderr}")
        return False, e.stderr


def compile_report(tester_state_dir, report_dir, report_path, project_id, overall_success, applied_transforms=None):
    """Compiles the finalized test results into validation-report.md."""
    os.makedirs(report_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    progress_file = os.path.join(tester_state_dir, "progress.json")
    steps = []
    
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            progress = json.load(f)
        
        total = progress.get("total_steps", 0)
        for num in range(1, total + 1):
            step_file = os.path.join(tester_state_dir, f"step-{num:03d}.json")
            if os.path.exists(step_file):
                with open(step_file, "r") as sf:
                    steps.append(json.load(sf))
                    
    verdict = "PASSED" if overall_success else "FAILED"
    verdict_color = "#137333" if overall_success else "#c53929"
    
    report = []
    report.append("# Codelab E2E Validation Report")
    report.append("")
    report.append(f"**Timestamp:** {timestamp} UTC")
    report.append(f"**Test Project ID:** `{project_id}`")
    report.append(f"**Overall Verdict:** <span style='color: {verdict_color}; font-weight: bold;'>{verdict}</span>")
    report.append("")
    report.append("## Applied Overlay Transforms")
    report.append("")
    if applied_transforms:
        report.append("The following per-lab overlay transforms were applied during validation:")
        report.append("")
        for t in applied_transforms:
            report.append(f"- {t}")
    else:
        report.append("None — lab validated as written")
    report.append("")
    report.append("## Step-by-Step Execution Summary")
    report.append("")
    report.append("| Step | Title | Status | Details / Output |")
    report.append("| :--- | :--- | :--- | :--- |")
    
    for s in steps:
        status = s.get("status", "PENDING")
        title = s.get("title", "Unnamed Step")
        num = s.get("num", 0)
        
        # Format status cell with HTML badge
        if status == "DONE":
            badge = "🟢 DONE"
        elif status == "FAILED":
            badge = "🔴 FAILED"
        elif status == "BLOCKED":
            badge = "🟡 BLOCKED"
        elif status == "RUNNING":
            badge = "🔵 RUNNING"
        elif status == "DEFERRED":
            badge = "⏸️ DEFERRED"
        else:
            badge = "⚪ PENDING"
            
        details = s.get("output", "").strip()
        if not details:
            details = s.get("error", "").strip()
        if not details:
            details = s.get("instructions", "")
            
        # Clean details for table display
        details = details.replace("\n", "<br>").replace("|", "\\|")
        if len(details) > 300:
            details = details[:297] + "..."
            
        report.append(f"| Step {num} | {title} | {badge} | {details} |")
        
    report.append("")
    report.append("## Architectural & Execution Review")
    report.append("")
    if overall_success:
        report.append("> [!NOTE]\n> All integration commands and setup workflows completed successfully. The architecture represents a valid, functional configuration.")
    else:
        report.append("> [!WARNING]\n> One or more steps failed execution. Please review the failed outputs above to remediate syntax, dependencies, or permission constraints.")
        
    report.append("")
    report.append("## Recommendations for Codelab Improvement")
    report.append("")
    report.append("1. **Stateful Reliability:** Use explicit waits or propagation checks before relying on newly provisioned infrastructure resources.")
    report.append("2. **Idempotency:** Ensure all CLI flags include `--force`, `--quiet`, or equivalent check/update behavior where possible.")
    report.append("3. **Variables:** Rely on standard project discovery (`PROJECT_ID=$(gcloud config get-value project)`) instead of static templates.")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
        
    print(f"[Validator] Validation report written to: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="E2E Codelab Validation Orchestrator.")
    parser.add_argument("--src", required=True, help="Path to codelab md file or HTTP link.")
    parser.add_argument("--name", help="Custom name for the validated codelab folder.")
    parser.add_argument("--project-id", help="Existing GCP project ID to use. If omitted, a new one is provisioned.")
    parser.add_argument("--artifact-dir", help="Destination folder for visual task board.md.")
    parser.add_argument("--skip-cleanup", action="store_true", help="Skip codelab cleanup steps.")
    parser.add_argument("--keep-project", action="store_true", help="Skip deleting the provisioned GCP project.")
    parser.add_argument("--resume", action="store_true", help="Resume validation from the last failed step without cleaning up the state or recreating resources.")
    
    args = parser.parse_args()
    
    print("="*60)
    print("      STARTING CODELAB E2E VALIDATION RUN      ")
    print("="*60)
    
    # Determine dynamic lab folder name based on source or user name
    lab_name = None
    if args.name:
        lab_name = clean_filename(args.name)
    else:
        if args.src.startswith("http://") or args.src.startswith("https://"):
            url_clean = args.src.split("?")[0].split("#")[0]
            segments = [s for s in url_clean.split("/") if s]
            if segments:
                lab_name = clean_filename(segments[-1])
        if not lab_name:
            basename = os.path.basename(args.src)
            name, _ = os.path.splitext(basename)
            if name.endswith(".lab"):
                name = name[:-4]
            lab_name = clean_filename(name)
            
    if not lab_name:
        lab_name = "active-lab"
        
    validate_dir = os.path.join(repo_root, "labs", "validate", lab_name)
    active_lab_path = os.path.join(validate_dir, f"{lab_name}.lab.md")
    report_dir = os.path.join(validate_dir, "report")
    report_path = os.path.join(report_dir, "validation-report.md")
    
    print(f"[Validator] Target Validation Directory: {validate_dir}")
    print(f"[Validator] Target Lab File: {active_lab_path}")
    
    # 1. Resolve active lab source inside dynamic validate_dir
    applied_transforms = setup_active_lab(args.src, validate_dir, active_lab_path, resume=args.resume)
    
    # Scan dynamic variable placeholders
    placeholders = scan_placeholders(active_lab_path)
    vars_file = os.path.join(validate_dir, "variables.json")
    existing_vars = {}
    if os.path.exists(vars_file):
        try:
            with open(vars_file, "r", encoding="utf-8") as vf:
                existing_vars = json.load(vf)
        except Exception:
            pass
    
    updated_vars = {}
    for p in placeholders:
        # Ignore default project ID placeholders that validator.py already handles
        if p.lower() in ["your-project-id", "project-id", "your project id", "project id"]:
            continue
        updated_vars[p] = existing_vars.get(p, "")
        
    # Write or update variables.json file
    with open(vars_file, "w", encoding="utf-8") as vf:
        json.dump(updated_vars, vf, indent=2)
    
    if updated_vars:
        print(f"[Validator] Dynamic variables detected and written to {vars_file}")
        empty_vars = [k for k, v in updated_vars.items() if not v]
        if empty_vars:
            print(f"[Validator] WARNING: The following variables must be populated in variables.json: {empty_vars}")

    # 2. Handle Project ID
    project_id = args.project_id
    temp_project_created = False
    
    if not project_id:
        if args.resume:
            # Try to read active gcloud project
            try:
                active_proj = subprocess.check_output(["gcloud", "config", "get-value", "project"], text=True).strip()
                if active_proj and active_proj.startswith("val-lab-"):
                    project_id = active_proj
                    print(f"[Validator] Resuming: Automatically detected active temporary project: {project_id}")
            except Exception:
                pass
                
        if not project_id:
            print("[Validator] No project-id specified. Provisioning temporary GCP project...")
            round_number = str(random.randint(100000, 999999))
            temp_project_id = f"val-lab-{round_number}"
            
            # Execute create_project.py
            create_cmd = f"python3 .agents/skills/gcp-provisioning/scripts/create_project.py val-lab {round_number}"
            success, output = run_command(create_cmd, "Provisioning test project")
            if not success:
                print("[Validator] Project provisioning failed. Exiting.")
                sys.exit(1)
                
            project_id = temp_project_id
            temp_project_created = True
            print(f"[Validator] Temporary project created successfully: {project_id}")
            
            # Disable Org Policies
            policy_cmd = f"bash .agents/skills/gcp-provisioning/scripts/disable_org_policies.sh {project_id}"
            success, output = run_command(policy_cmd, "Disabling Org Policies")
            if not success:
                print("[Validator] Disabling Org Policies failed. Continuing anyway...")
    else:
        print(f"[Validator] Using existing project: {project_id}")
        
    # Align ADC/gcloud context
    run_command(f"gcloud config set project {project_id}", "Setting gcloud active project")
    
    # 3. Run Tester Suite
    tester_cmd = f"python3 .agents/skills/codelab-validation/scripts/tester.py {active_lab_path} --project-id {project_id}"
    if args.artifact_dir:
        tester_cmd += f" --artifact-dir {args.artifact_dir}"
    if args.skip_cleanup:
        tester_cmd += " --phase test"
    else:
        tester_cmd += " --phase all"
        
    print("[Validator] Launching stateful E2E verification engine...")
    test_success, test_output = run_command(tester_cmd, "Running tester suite")
    
    # 4. Compile Validation Report
    tester_state_dir = os.path.join(validate_dir, ".tester_state")
    compile_report(tester_state_dir, report_dir, report_path, project_id, test_success, applied_transforms=applied_transforms)
    
    # 5. Handle Project Cleanup Instructions
    if temp_project_created:
        print("\n" + "="*60)
        print("                      CLEANUP NOTICE                     ")
        print("="*60)
        print(f"A temporary GCP project was provisioned for this test run: {project_id}")
        if args.keep_project:
            print("[Validator] --keep-project was passed. Retaining project.")
        else:
            print("[Validator] To delete this project, execute the following command:")
            print(f"  python3 .agents/skills/codelab-cleanup/scripts/cleanup_projects.py --delete {project_id} --force")
            print("="*60 + "\n")
            
    sys.exit(0 if test_success else 1)


if __name__ == "__main__":
    main()
