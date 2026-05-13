"""Deterministic command extractor and runner with state management (Hash-based)."""

import argparse
import datetime
import fcntl
import hashlib
import logging
import os
import re
import select
import subprocess
import sys
import time
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Reporting UI Skeleton constants
HTML_SKELETON_TOP = """<div style="max-width: 900px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #ffffff; border-radius: 12px; border: 1px solid #e8eaed; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);">
<div style="padding: 20px 24px; background: #ffffff; border-bottom: 1px solid #e8eaed; border-left: 6px solid #1a73e8;">
<h1 style="margin: 0 0 8px 0; font-size: 22px; color: #1a73e8; font-weight: 600;">Codelab Live Test Suite Execution</h1>
<div style="display: flex; flex-wrap: wrap; gap: 16px; font-size: 13px; color: #5f6368;">"""

HTML_SKELETON_MID = """</div>
</div>
<table style="width: 100%; border-collapse: collapse; margin: 0; font-size: 13px;">
<thead>
<tr style="background-color: #f8f9fa; border-bottom: 2px solid #e8eaed; text-align: left; color: #3c4043;">
<th style="padding: 12px 24px; font-weight: 600; width: 100px; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Status</th>
<th style="padding: 12px 12px 12px 0; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Extracted Step Command Block</th>
</tr>
</thead>
<tbody>"""

HTML_SKELETON_BOT = """</tbody>
</table>
</div>"""

BADGE_IN_PROGRESS = '<span style="background: #e8f0fe; color: #1a73e8; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px;">IN PROGRESS</span>'
BADGE_COMPLETED = '<span style="background: #e6f4ea; color: #137333; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px;">COMPLETED</span>'
BADGE_FAILED = '<span style="background: #fce8e6; color: #c5221f; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px;">FAILED</span>'

BADGE_ROW_PENDING = '<span style="background: #f1f3f4; color: #5f6368; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">PENDING</span>'
BADGE_ROW_DONE = '<span style="background: #e6f4ea; color: #137333; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">DONE</span>'
BADGE_ROW_FAILED = '<span style="background: #fce8e6; color: #c5221f; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">FAILED</span>'
BADGE_ROW_RUNNING = '<span style="background: #e8f0fe; color: #1a73e8; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">RUNNING</span>'


class SubshellRunner:
    """Manages a persistent, non-blocking bash session safely."""
    def __init__(self, cwd: str):
        self.process = subprocess.Popen(
            ["bash"],
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=False,  # Use bytes to prevent encoding/buffering deadlocks
        )
        
        # Set stdout to non-blocking IO streams
        assert self.process.stdout is not None
        fd = self.process.stdout.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    def set_env(self, key: str, value: str):
        """Injects variables natively into the active subshell environment."""
        self.run_command(f"export {key}='{value}'")

    def run_command(self, cmd: str, timeout: int = 300) -> tuple[int, str]:
        assert self.process.stdin is not None
        assert self.process.stdout is not None
        token = f"__DONE_{uuid.uuid4().hex}__"
        
        # Safely wrap command ensuring stdin is closed for the command itself,
        # preventing greedy tools from swallowing our shell session.
        wrapped_cmd = f"{{ {cmd}\n}} < /dev/null\nstatus=$?\nprintf '\\n%s %d\\n' '{token}' $status\n"
        
        self.process.stdin.write(wrapped_cmd.encode('utf-8'))
        self.process.stdin.flush()

        output_bytes = bytearray()
        start_time = time.time()

        while True:
            # Check if process died unexpectedly
            if self.process.poll() is not None:
                return -1, output_bytes.decode('utf-8', errors='replace')

            ready, _, _ = select.select([self.process.stdout], [], [], 0.5)
            if ready:
                try:
                    chunk = os.read(self.process.stdout.fileno(), 4096)
                    if not chunk:
                        break
                    output_bytes.extend(chunk)
                    start_time = time.time()  # Reset timeout on active output
                    
                    # Check for our unique token in the decoded tail using error-immune replace modes
                    tail = output_bytes[-200:].decode('utf-8', errors='ignore')
                    if token in tail:
                        lines = tail.splitlines()
                        for line in reversed(lines):
                            if token in line:
                                try:
                                    status = int(line.split()[-1])
                                    # Clean the token from final output string
                                    clean_output = output_bytes.decode('utf-8', errors='replace').replace(line, '')
                                    return status, clean_output.strip()
                                except ValueError:
                                    continue
                except BlockingIOError:
                    pass

            if time.time() - start_time > timeout:
                return -2, output_bytes.decode('utf-8', errors='replace')

        return -3, output_bytes.decode('utf-8', errors='replace')

    def close(self):
        """Terminates underlying subshell processes gracefully."""
        try:
            self.process.terminate()
            self.process.wait(timeout=5)
        except Exception:
            pass


def _filter_hermetic_commands(commands: list[str]) -> list[str]:
    """Filters out interactive or continuous loops from extracted commands."""
    clean = []
    for cmd in commands:
        if "while true" in cmd.lower() or "gcloud compute ssh" in cmd.lower():
            continue
        clean.append(cmd)
    return clean


def extract_bash_commands(markdown_content: str) -> list[str]:
    """Extracts all fenced bash code blocks from markdown content."""
    pattern = re.compile(r"```bash\n(.*?)\n[ \t]*```", re.DOTALL)
    matches = pattern.findall(markdown_content)
    commands = [match.strip() for match in matches]
    return _filter_hermetic_commands(commands)


def get_cmd_hash(cmd: str) -> str:
    """Computes SHA-256 hash of a command string."""
    return hashlib.sha256(cmd.encode("utf-8")).hexdigest()


def get_active_project():
    """Gets the active gcloud project specifically targeting subprocess exceptions."""
    try:
        result = subprocess.run(["gcloud", "config", "get-value", "project"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.SubprocessError:
        return "Unknown"


def update_status_file(status_file, project_id, commands, current_idx, step_results):
    """Updates the test_status.md file using isolated unindented HTML string components."""
    overall_status_badge = BADGE_IN_PROGRESS
    if current_idx >= len(commands):
        overall_status_badge = BADGE_COMPLETED
    elif step_results.get(current_idx) is False:
        overall_status_badge = BADGE_FAILED

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    lines = [
        HTML_SKELETON_TOP,
        f'<div style="display: flex; align-items: center; gap: 6px;"><strong>Overall Status:</strong> {overall_status_badge}</div>',
        f'<div><strong>Project ID:</strong> {project_id}</div>',
        f'<div><strong>Last Updated:</strong> {timestamp}</div>',
        HTML_SKELETON_MID
    ]

    for idx, cmd in enumerate(commands):
        badge = BADGE_ROW_PENDING
        row_style = 'border-bottom: 1px solid #e8eaed; background-color: #fafbfc;'
        
        if idx < current_idx:
            if step_results.get(idx, False):
                badge = BADGE_ROW_DONE
            else:
                badge = BADGE_ROW_FAILED
        elif idx == current_idx:
            if step_results.get(idx) is False:
                badge = BADGE_ROW_FAILED
            else:
                badge = BADGE_ROW_RUNNING
                row_style = 'border-bottom: 2px solid #1a73e8; background-color: #ffffff;'

        cmd_preview = cmd.split('\n')[0][:80] + "..." if len(cmd.split('\n')[0]) > 80 else cmd.split('\n')[0]
        safe_cmd = cmd_preview.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        lines.append(f'<tr style="{row_style}">')
        lines.append(f'<td style="padding: 14px 24px; vertical-align: top;">{badge}</td>')
        lines.append(f'<td style="padding: 14px 24px 14px 0; vertical-align: top;"><span style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 12px;">{safe_cmd}</span></td>')
        lines.append('</tr>')

    lines.append(HTML_SKELETON_BOT)

    with open(status_file, "w") as f:
        f.write("\n".join(lines))


def run_validation_suite(commands: list[str], cwd: str, state_file: str, env_file: str, status_file: str, timeout=300) -> dict:
    """Executes commands sequentially inside an isolated SubshellRunner mapping linear cache validation."""
    if not commands:
        return {"success": True, "stdout": "No commands to run.", "stderr": ""}

    # Load previously executed hashes
    executed_hashes = []
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            executed_hashes = [line.strip() for line in f.readlines()]
        logging.info("[Runner] Found %d previously executed commands.", len(executed_hashes))

    # Linear Truncation Cache Coherence: Validate if historical hashes form an exact continuous sequence prefix
    valid_cache_prefix = []
    for idx, cmd in enumerate(commands):
        cmd_hash = get_cmd_hash(cmd)
        if idx < len(executed_hashes) and executed_hashes[idx] == cmd_hash:
            valid_cache_prefix.append(cmd_hash)
        else:
            break
            
    if len(valid_cache_prefix) < len(executed_hashes):
        logging.info("[Runner] Cache mismatch detected at step %d. Linear truncation applied.", len(valid_cache_prefix))
        executed_hashes = valid_cache_prefix
        with open(state_file, "w") as f:
            f.write("\n".join(executed_hashes) + "\n" if executed_hashes else "")

    project_id = get_active_project()
    step_results = {idx: True for idx in range(len(commands)) if idx < len(executed_hashes)}
    
    update_status_file(status_file, project_id, commands, len(executed_hashes), step_results)

    runner = SubshellRunner(cwd=cwd)
    try:
        # Restore native environment variables if resuming execution
        if executed_hashes and os.path.exists(env_file):
            logging.info("[Runner] Restoring cached environment variables natively...")
            runner.run_command(f"source {env_file}")

        # Inject runtime project context natively into underlying bash process
        runner.set_env("PROJECT_ID", project_id)

        for idx, cmd in enumerate(commands):
            cmd_hash = get_cmd_hash(cmd)
            if idx < len(executed_hashes):
                logging.info("[Runner] Skipping step %d (already verified in cache prefix)", idx)
                continue

            logging.info("[Runner] Evaluating step %d...", idx)
            update_status_file(status_file, project_id, commands, idx, step_results)
            
            # Safely map raw placeholder text to prevent bash redirection syntax drops on generic string templates
            evaluated_cmd = cmd.replace("<PROJECT_ID>", project_id)
            status, output = runner.run_command(evaluated_cmd, timeout=timeout)
            if output:
                logging.info(f"[Output tail]: {output[-200:]}")

            if status != 0:
                logging.error("[Runner] Step %d failed with status %d", idx, status)
                step_results[idx] = False
                update_status_file(status_file, project_id, commands, idx, step_results)
                return {"success": False, "failed_idx": idx}

            step_results[idx] = True
            with open(state_file, "a") as f:
                f.write(cmd_hash + "\n")
            executed_hashes.append(cmd_hash)
            
            # Export live environment variables
            runner.run_command(f"export -p > {env_file}")

        update_status_file(status_file, project_id, commands, len(commands), step_results)
        return {"success": True}
    finally:
        runner.close()


def main():
    parser = argparse.ArgumentParser(description="Deterministic command runner for Codelab testing.")
    parser.add_argument("markdown_file", help="Path to the markdown file containing bash commands.")
    parser.add_argument("--timeout", type=int, default=600, help="Timeout in seconds for each command.")
    parser.add_argument("--artifact-dir", help="Path to the system artifact directory to output live preview status dashboards.")
    
    args = parser.parse_args()
    
    md_path = args.markdown_file
    if not os.path.exists(md_path):
        print(f"File not found: {md_path}")
        sys.exit(1)

    with open(md_path, "r") as f:
        content = f.read()

    commands = extract_bash_commands(content)
    print(f"Extracted {len(commands)} bash blocks.")

    cwd = os.getcwd()
    state_file = md_path + ".state"
    env_file = md_path + ".env"
    
    # Isolate live status dashboards directly into artifact preview space if designated
    static_lab_status_file = os.path.join(os.path.dirname(md_path), "test_status.md")
    status_file = os.path.join(args.artifact_dir, "test_status.md") if args.artifact_dir else static_lab_status_file

    result = run_validation_suite(commands, cwd, state_file, env_file, status_file, timeout=args.timeout)

    print("\n--- Validation Summary ---")
    if result.get("success"):
        print("Validation successful!")
        # Upon total suite success, copy finalized live status audit record back into static repository space
        if args.artifact_dir and os.path.exists(status_file) and status_file != static_lab_status_file:
            import shutil
            shutil.copy2(status_file, static_lab_status_file)
            print(f"Persisted final verification audit report cleanly to {static_lab_status_file}")
        sys.exit(0)
    else:
        print(f"Validation failed at step {result.get('failed_idx')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
