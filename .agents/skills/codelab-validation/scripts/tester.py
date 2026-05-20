#!/usr/bin/env python3
"""Unified Stateful Codelab Validation and Deterministic Subshell Execution Engine."""

import argparse
import datetime
import fcntl
import hashlib
import json
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

# HTML Status Table Constants (Tasks.md and visual preview compliance)
HTML_SKELETON_TOP = """<div style="max-width: 900px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #ffffff; border-radius: 12px; border: 1px solid #e8eaed; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);">
<div style="padding: 20px 24px; background: #ffffff; border-bottom: 1px solid #e8eaed; border-left: 6px solid #1a73e8;">
<h1 style="margin: 0 0 8px 0; font-size: 22px; color: #1a73e8; font-weight: 600;">Codelab Unified Stateful Validation Board</h1>
<div style="display: flex; flex-wrap: wrap; gap: 16px; font-size: 13px; color: #5f6368;">"""

HTML_SKELETON_MID = """</div>
</div>
<div style="padding: 20px 24px; border-bottom: 1px solid #e8eaed;">
<div style="font-size: 14px; font-weight: 600; margin: 0 0 8px 0; color: #3c4043; text-transform: uppercase; letter-spacing: 0.5px;">Objective</div>
<p style="margin: 0; font-size: 14px; color: #5f6368; line-height: 1.5;">
Validate the codelab step-by-step using stateful verification, ensuring correctness, command cache hits, and persistent subshell execution.
</p>
</div>
<table style="width: 100%; border-collapse: collapse; margin: 0; font-size: 13px;">
<thead>
<tr style="background-color: #f8f9fa; border-bottom: 2px solid #e8eaed; text-align: left; color: #3c4043;">
<th style="padding: 12px 24px; font-weight: 600; width: 100px; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Status</th>
<th style="padding: 12px 12px 12px 0; font-weight: 600; width: 240px; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Execution Step</th>
<th style="padding: 12px 24px 12px 0; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Details & Outputs</th>
</tr>
</thead>
<tbody>"""

HTML_SKELETON_BOT = """</tbody>
</table>
</div>"""

BADGE_MAP = {
    "PENDING": '<span style="background: #f1f3f4; color: #5f6368; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">PENDING</span>',
    "RUNNING": '<span style="background: #e8f0fe; color: #1a73e8; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">RUNNING</span>',
    "DONE": '<span style="background: #e6f4ea; color: #137333; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">DONE</span>',
    "FAILED": '<span style="background: #fce8e6; color: #c53929; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">FAILED</span>',
    "BLOCKED": '<span style="background: #ffebee; color: #c53929; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">BLOCKED</span>',
    "IN PROGRESS": '<span style="background: #e8f0fe; color: #1a73e8; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">IN PROGRESS</span>',
    "COMPLETED": '<span style="background: #e6f4ea; color: #137333; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">COMPLETED</span>'
}

class SubshellRunner:
    """Manages a persistent, non-blocking bash session safely."""
    def __init__(self, cwd: str):
        self.process = subprocess.Popen(
            ["bash"],
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=False,
        )
        assert self.process.stdout is not None
        fd = self.process.stdout.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    def set_env(self, key: str, value: str):
        self.run_command(f"export {key}='{value}'")

    def run_command(self, cmd: str, timeout: int = 300) -> tuple[int, str]:
        assert self.process.stdin is not None
        assert self.process.stdout is not None
        token = f"__DONE_{uuid.uuid4().hex}__"
        
        wrapped_cmd = f"{{ {cmd}\n}} < /dev/null\nstatus=$?\nprintf '\\n%s %d\\n' '{token}' $status\n"
        self.process.stdin.write(wrapped_cmd.encode('utf-8'))
        self.process.stdin.flush()

        output_bytes = bytearray()
        start_time = time.time()

        while True:
            if self.process.poll() is not None:
                return -1, output_bytes.decode('utf-8', errors='replace')

            ready, _, _ = select.select([self.process.stdout], [], [], 0.5)
            if ready:
                try:
                    chunk = os.read(self.process.stdout.fileno(), 4096)
                    if not chunk:
                        break
                    output_bytes.extend(chunk)
                    start_time = time.time()
                    
                    tail = output_bytes[-200:].decode('utf-8', errors='ignore')
                    if token in tail:
                        lines = tail.splitlines()
                        for line in reversed(lines):
                            if token in line:
                                try:
                                    status = int(line.split()[-1])
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
        try:
            self.process.terminate()
            self.process.wait(timeout=5)
        except Exception:
            pass

def _filter_hermetic_commands(commands: list[str]) -> list[str]:
    clean = []
    for cmd in commands:
        if "while true" in cmd.lower() or "gcloud compute ssh" in cmd.lower():
            continue
        clean.append(cmd)
    return clean

def normalize_command(cmd: str) -> str:
    lines = []
    for line in cmd.splitlines():
        line_s = line.strip()
        if not line_s or line_s.startswith("#"):
            continue
        if " #" in line_s:
            line_s = line_s.split(" #", 1)[0].strip()
        words = line_s.split()
        lines.append(" ".join(words))
    return "\n".join(lines)

def get_cmd_hash(cmd: str) -> str:
    return hashlib.sha256(normalize_command(cmd).encode("utf-8")).hexdigest()

def get_active_project():
    try:
        result = subprocess.run(["gcloud", "config", "get-value", "project"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.SubprocessError:
        return "Unknown"

class StatefulCodelabTester:
    """Orchestrates Codelab steps, state transitions, and command execution."""
    def __init__(self, markdown_file: str, artifact_dir: str = None, timeout: int = 600, skip_cleanup: bool = False):
        self.md_path = os.path.abspath(markdown_file)
        self.lab_dir = os.path.dirname(self.md_path)
        self.tester_state_dir = os.path.join(self.lab_dir, ".tester_state")
        self.artifact_dir = artifact_dir
        self.timeout = timeout
        self.skip_cleanup = skip_cleanup
        
        # Parse or load step states
        self.steps = []
        self.project_id = get_active_project()
        
        # Determine status files
        self.static_status_file = os.path.join(self.lab_dir, "test_status.md")
        self.artifact_status_file = os.path.join(artifact_dir, "test_status.md") if artifact_dir else self.static_status_file
        self.artifact_task_file = os.path.join(artifact_dir, "task.md") if artifact_dir else None

        os.makedirs(self.tester_state_dir, exist_ok=True)

    def parse_codelab(self) -> list[dict]:
        """Parses markdown into sequential steps using H2 headers and extracts bash commands."""
        with open(self.md_path, "r") as f:
            content = f.read()
            
        # Regex to split by H2 headers (## Step name)
        h2_pattern = re.compile(r"^(##\s+.*)$", re.MULTILINE)
        sections = h2_pattern.split(content)
        
        parsed_steps = []
        step_num = 1
        
        # The first element is intro text before the first ##
        for idx in range(1, len(sections), 2):
            title_line = sections[idx].strip()
            title = title_line.replace("##", "").strip()
            body = sections[idx+1] if idx+1 < len(sections) else ""
            
            # Extract bash commands
            bash_pattern = re.compile(r"```bash\n(.*?)\n[ \t]*```", re.DOTALL)
            commands = [c.strip() for c in bash_pattern.findall(body)]
            commands = _filter_hermetic_commands(commands)
            
            # Detect explicit or implicit prerequisites
            prereqs = []
            if re.search(r"(?i)(wait for|after the|until the|prerequisite)", body):
                prereqs.append("Prerequisite delay/propagation condition detected")
                
            # Standardize instructions from body
            clean_body_lines = [line.strip() for line in body.splitlines() if line.strip() and not line.strip().startswith("```")]
            instructions = " ".join(clean_body_lines[:3]) + "..." if clean_body_lines else "Execute steps."

            parsed_steps.append({
                "num": step_num,
                "title": title,
                "status": "PENDING",
                "instructions": instructions,
                "prerequisites": prereqs,
                "commands": commands,
                "output": "",
                "error": ""
            })
            step_num += 1
            
        return parsed_steps

    def load_or_initialize_state(self):
        progress_file = os.path.join(self.tester_state_dir, "progress.json")
        if os.path.exists(progress_file):
            logging.info("[Tester] Existing progress state found. Resuming run...")
            with open(progress_file, "r") as f:
                progress = json.load(f)
            
            self.steps = []
            for num in range(1, progress["total_steps"] + 1):
                step_file = os.path.join(self.tester_state_dir, f"step-{num:03d}.json")
                if os.path.exists(step_file):
                    with open(step_file, "r") as sf:
                        self.steps.append(json.load(sf))
        else:
            logging.info("[Tester] No existing state found. Initializing...")
            self.steps = self.parse_codelab()
            self.save_state()

    def save_state(self, current_idx=0, overall_status="IN PROGRESS"):
        # Save general progress
        progress = {
            "codelab": os.path.basename(self.md_path),
            "total_steps": len(self.steps),
            "current_step": current_idx + 1,
            "status": overall_status
        }
        with open(os.path.join(self.tester_state_dir, "progress.json"), "w") as f:
            json.dump(progress, f, indent=2)

        # Save individual steps
        for step in self.steps:
            step_file = os.path.join(self.tester_state_dir, f"step-{step['num']:03d}.json")
            with open(step_file, "w") as f:
                json.dump(step, f, indent=2)

        # Save user inputs cache
        user_inputs = {"PROJECT_ID": self.project_id}
        with open(os.path.join(self.tester_state_dir, "user_inputs.json"), "w") as f:
            json.dump(user_inputs, f, indent=2)

    def write_visual_boards(self, overall_status="IN PROGRESS"):
        """Generates premium zero-indentation HTML status charts in tasks.md / test_status.md."""
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        lines = [
            HTML_SKELETON_TOP,
            f'<div style="display: flex; align-items: center; gap: 6px;"><strong>Overall Status:</strong> {BADGE_MAP[overall_status]}</div>',
            f'<div><strong>Project ID:</strong> {self.project_id}</div>',
            f'<div><strong>Last Updated:</strong> {timestamp}</div>',
            HTML_SKELETON_MID
        ]

        for step in self.steps:
            status = step["status"]
            badge = BADGE_MAP[status]
            row_style = 'border-bottom: 1px solid #e8eaed; background-color: #fafbfc;'
            if status == "RUNNING":
                row_style = 'border-bottom: 2px solid #1a73e8; background-color: #ffffff;'

            details = step["instructions"]
            if step["commands"]:
                cmd_preview = step["commands"][0][:100] + "..." if len(step["commands"][0]) > 100 else step["commands"][0]
                details += f'<br><code style="font-family: monospace; font-size: 11px; color: #202124; background: #f1f3f4; padding: 2px 4px; border-radius: 4px;">{cmd_preview}</code>'

            lines.append(f'<tr style="{row_style}">')
            lines.append(f'<td style="padding: 14px 24px; vertical-align: top;">{badge}</td>')
            lines.append(f'<td style="padding: 14px 12px 14px 0; vertical-align: top; font-weight: 600; color: {"#1a73e8" if status == "RUNNING" else "#3c4043"};">Step {step["num"]}: {step["title"]}</td>')
            lines.append(f'<td style="padding: 14px 24px 14px 0; vertical-align: top; color: #5f6368;">{details}')
            
            if step.get("error"):
                safe_err = step["error"].replace("<", "&lt;").replace(">", "&gt;")
                lines.append(f'<pre style="font-family: ui-monospace, monospace; font-size: 11px; background: #f1f3f4; padding: 8px 12px; border-radius: 6px; color: #202124; margin: 8px 0 0 0; white-space: pre-wrap; word-break: break-all;">{safe_err}</pre>')
            lines.append('</td></tr>')

        lines.append(HTML_SKELETON_BOT)
        html_content = "\n".join(line.strip() for line in lines)

        # Write to active status files
        with open(self.artifact_status_file, "w") as f:
            f.write(html_content)
            
        if self.artifact_task_file:
            with open(self.artifact_task_file, "w") as f:
                f.write(html_content)

    def run(self) -> bool:
        """Executes step-by-step state validation."""
        self.load_or_initialize_state()
        
        # Determine historical state file for commands
        state_file = self.md_path + ".state"
        env_file = self.md_path + ".env"
        
        executed_hashes = []
        if os.path.exists(state_file):
            with open(state_file, "r") as f:
                executed_hashes = [line.strip() for line in f.readlines()]

        runner = SubshellRunner(cwd=self.lab_dir)
        try:
            if executed_hashes and os.path.exists(env_file):
                logging.info("[Tester] Restoring environment from active cache...")
                runner.run_command(f"source {env_file}")
            
            runner.set_env("PROJECT_ID", self.project_id)
            
            # Iterate and run step state transitions
            for idx, step in enumerate(self.steps):
                if step["status"] == "DONE":
                    logging.info("[Tester] Skipping step %d: %s (already DONE)", step["num"], step["title"])
                    continue
                
                if self.skip_cleanup and re.search(r"(?i)(clean\s*up|cleanup)", step["title"]):
                    logging.info("[Tester] Skipping cleanup step %d: %s (skip-cleanup enabled)", step["num"], step["title"])
                    step["status"] = "DONE"
                    step["output"] = "Skipped per request to retain resources."
                    continue
                
                logging.info("[Tester] Running step %d: %s...", step["num"], step["title"])
                step["status"] = "RUNNING"
                self.save_state(idx, "IN PROGRESS")
                self.write_visual_boards("IN PROGRESS")
                
                if not step["commands"]:
                    logging.info("[Tester] Step has no commands. Automatically completed.")
                    step["status"] = "DONE"
                    continue

                step_failed = False
                step_outputs = []
                step_errors = []
                
                for cmd in step["commands"]:
                    cmd_hash = get_cmd_hash(cmd)
                    if cmd_hash in executed_hashes:
                        logging.info("[Tester] Command already in cache. Skipping execution.")
                        continue
                    
                    # Replace variable placeholders
                    evaluated_cmd = cmd.replace("<PROJECT_ID>", self.project_id)
                    
                    # Run command in persistent subshell
                    status, output = runner.run_command(evaluated_cmd, timeout=self.timeout)
                    
                    if status != 0:
                        step_failed = True
                        step["status"] = "FAILED"
                        step["error"] = f"Command failed with status {status}.\nOutput:\n{output}"
                        step_errors.append(step["error"])
                        break
                    
                    step_outputs.append(output)
                    executed_hashes.append(cmd_hash)
                    with open(state_file, "a") as f:
                        f.write(cmd_hash + "\n")
                        
                    # Export environment variables to cache
                    runner.run_command(f"export -p > {env_file}")

                if step_failed:
                    self.save_state(idx, "FAILED")
                    self.write_visual_boards("FAILED")
                    logging.error("[Tester] Step %d failed.", step["num"])
                    return False
                
                # Step successfully completed
                step["status"] = "DONE"
                step["output"] = "\n".join(step_outputs)
                
            # All steps done!
            self.save_state(len(self.steps) - 1, "COMPLETED")
            self.write_visual_boards("COMPLETED")
            
            # Proactively copy final validation report back into static space
            if self.artifact_status_file != self.static_status_file and os.path.exists(self.artifact_status_file):
                import shutil
                shutil.copy2(self.artifact_status_file, self.static_status_file)
                logging.info("[Tester] Copied finalized test report to static directory.")
                
            logging.info("[Tester] Validation suite completed successfully!")
            return True
            
        finally:
            runner.close()

def main():
    parser = argparse.ArgumentParser(description="Unified stateful codelab verification CLI.")
    parser.add_argument("markdown_file", help="Path to the codelab markdown guide file.")
    parser.add_argument("--artifact-dir", help="Conversation context artifact directory.")
    parser.add_argument("--timeout", type=int, default=600, help="Step timeout in seconds.")
    parser.add_argument("--skip-cleanup", action="store_true", help="Skip cleanup steps in the codelab.")
    
    args = parser.parse_args()
    
    tester = StatefulCodelabTester(args.markdown_file, args.artifact_dir, args.timeout, args.skip_cleanup)
    success = tester.run()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
