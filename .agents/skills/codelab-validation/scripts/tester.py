#!/usr/bin/env python3
"""Unified Stateful Codelab Validation and Deterministic Subshell Execution Engine."""

import argparse
import datetime
import fcntl
import json
import logging
import os
import re
import select
import shlex
import subprocess
import sys
import time
import uuid
from typing import Any, Tuple

# Resolve repository root dynamically
_script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(_script_dir, "..", "..", "..", ".."))

# Add script directory to path to import modular components
sys.path.append(_script_dir)
from codelab_parser import (  # noqa: E402
    _EXECUTABLE_FENCE_LANGS as _EXECUTABLE_FENCE_LANGS,
    _FENCE_LINE_RE as _FENCE_LINE_RE,
    _extract_command_blocks as _extract_command_blocks,
    _filter_hermetic_commands as _filter_hermetic_commands,
    get_cmd_hash as get_cmd_hash,
    normalize_command as normalize_command,
)

try:
    from html_reporter import HTMLReporter
except ImportError:
    HTMLReporter = None

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

class SubshellRunner:
    """Manages a persistent, non-blocking bash session safely."""
    def __init__(self, cwd: str):
        env = os.environ.copy()
        # Prioritize repo-local bin and home local bin dynamically using OS path separator
        local_bin = os.path.join(repo_root, "bin")
        home_bin = os.path.expanduser("~/.local/bin")
        current_path = env.get("PATH", "")
        env["PATH"] = os.pathsep.join([local_bin, home_bin, current_path])

        # Pre-seed environment to prevent interactive prompts from hanging subshell execution
        env["DEBIAN_FRONTEND"] = "noninteractive"
        env["CLOUDSDK_CORE_DISABLE_PROMPTS"] = "1"

        self.process = subprocess.Popen(
            ["bash"],
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            text=False,
        )
        assert self.process.stdout is not None
        fd = self.process.stdout.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    def set_env(self, key: str, value: str):
        """Safely exports an environment variable using shlex quoting."""
        self.run_command(f"export {key}={shlex.quote(str(value))}")

    def run_command(self, cmd: str, timeout: int = 300) -> Tuple[int, str]:
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
        """Terminates subshell process gracefully, falling back to force kill to avoid zombies."""
        try:
            self.process.terminate()
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
        except Exception:
            pass


def get_active_project():
    if "CLOUDSDK_CORE_PROJECT" in os.environ:
        return os.environ["CLOUDSDK_CORE_PROJECT"]
    try:
        result = subprocess.run(["gcloud", "config", "get-value", "project"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.SubprocessError:
        return "Unknown"

def sanitize_command(cmd: str, project_id: str = "", custom_vars: dict = None) -> str:
    """Sanitizes variable expansion artifacts and deduplicates CLI flags in liveness probes and commands."""
    if custom_vars is None:
        custom_vars = {}
    
    evaluated_cmd = cmd.replace('""', '"').replace("''", "'")
    if project_id:
        evaluated_cmd = evaluated_cmd.replace("<PROJECT_ID>", project_id)
        evaluated_cmd = evaluated_cmd.replace("<project-id>", project_id)
        evaluated_cmd = evaluated_cmd.replace("<your-project-id>", project_id)
        evaluated_cmd = evaluated_cmd.replace("$PROJECT_ID", project_id)
        evaluated_cmd = evaluated_cmd.replace("${PROJECT_ID}", project_id)
        
    sorted_keys = sorted(custom_vars.keys(), key=len, reverse=True)
    for key in sorted_keys:
        val = str(custom_vars[key])
        evaluated_cmd = evaluated_cmd.replace(f"<{key}>", val)
        evaluated_cmd = evaluated_cmd.replace(f"${key}", val)
        evaluated_cmd = evaluated_cmd.replace(f"${{{key}}}", val)
        
    sanitized_lines = []
    for line in evaluated_cmd.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            sanitized_lines.append(line)
            continue
            
        leading_space = len(line) - len(line.lstrip())
        prefix = line[:leading_space]
        
        tokens = line.split()
        seen_tokens = set()
        seen_pairs = set()
        cleaned_tokens = []
        skip_next = False
        
        for idx, token in enumerate(tokens):
            if skip_next:
                skip_next = False
                continue
            if token in {"&&", "||", ";", "|"} or token.endswith(";"):
                seen_tokens.clear()
                seen_pairs.clear()
            elif token.startswith("--"):
                if "=" in token:
                    if token in seen_tokens:
                        continue
                    seen_tokens.add(token)
                else:
                    if idx + 1 < len(tokens) and not tokens[idx + 1].startswith("-"):
                        pair = (token, tokens[idx + 1])
                        if pair in seen_pairs:
                            skip_next = True
                            continue
                        seen_pairs.add(pair)
                    else:
                        if token in seen_tokens:
                            continue
                        seen_tokens.add(token)
            cleaned_tokens.append(token)
        sanitized_lines.append(prefix + " ".join(cleaned_tokens))
    return "\n".join(sanitized_lines)

class StatefulCodelabTester:
    """Orchestrates Codelab steps, state transitions, and command execution."""
    def __init__(self, markdown_file: str, artifact_dir: str = None, timeout: int = 600, phase: str = "test"):
        self.md_path = os.path.abspath(markdown_file)
        self.lab_dir = os.path.dirname(self.md_path)
        self.tester_state_dir = os.path.join(self.lab_dir, ".tester_state")
        self.artifact_dir = artifact_dir
        self.timeout = timeout
        self.phase = phase
        
        # Parse or load step states
        self.steps = []
        self.project_id = get_active_project()
        
        # Determine status files
        self.static_status_file = os.path.join(self.lab_dir, "test_status.md")
        self.artifact_status_file = os.path.join(artifact_dir, "test_status.md") if artifact_dir else self.static_status_file
        self.artifact_task_file = None  # Decoupled: never overwrite master task.md

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
            
            # Extract executable commands via proper fence pairing (never captures narrative)
            commands = _extract_command_blocks(body)
            commands = _filter_hermetic_commands(commands)
            
            # Detect explicit or implicit prerequisites
            prereqs = []
            if re.search(r"(?i)(wait for|after the|until the|prerequisite)", body):
                prereqs.append("Prerequisite delay/propagation condition detected")
                
            # Detect GUI/manual actions
            has_gui = False
            if not commands:
                has_gui = True
            elif re.search(r"(?i)(click|select|navigate|console|ui|save|dropdown|checkbox|fill out|button|radio button|under the|navigate to)", body):
                has_gui = True

            # Detect explicit phase marker for cleanup steps, falling back to title regex if no marker exists
            has_marker = bool(
                re.search(r"<!--\s*(phase:\s*cleanup|cleanup)\s*-->", body, re.IGNORECASE)
                or re.search(r"<!--\s*(phase:\s*cleanup|cleanup)\s*-->", title_line, re.IGNORECASE)
            )
            if has_marker:
                is_cleanup = True
            else:
                is_cleanup = bool(re.search(r"(?i)(clean\s*up|cleanup)", title))

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
                "error": "",
                "has_gui": has_gui,
                "is_cleanup": is_cleanup,
            })
            step_num += 1
            
        return parsed_steps

    def load_or_initialize_state(self):
        progress_file = os.path.join(self.tester_state_dir, "progress.json")
        if os.path.exists(progress_file):
            logging.info("[Tester] Existing progress state found. Resuming run...")
            with open(progress_file, "r") as f:
                progress = json.load(f)
            
            # Parse the fresh codelab first to get any new commands/edits!
            fresh_steps = self.parse_codelab()
            
            self.steps = []
            for idx, fresh_step in enumerate(fresh_steps):
                num = fresh_step["num"]
                step_file = os.path.join(self.tester_state_dir, f"step-{num:03d}.json")
                if os.path.exists(step_file):
                    try:
                        with open(step_file, "r") as sf:
                            cached_step = json.load(sf)
                        
                        # If the step was already successfully completed, preserve its DONE status and outputs
                        if cached_step.get("status") == "DONE":
                            fresh_step["status"] = "DONE"
                            fresh_step["output"] = cached_step.get("output", "")
                            fresh_step["error"] = cached_step.get("error", "")
                        # If it was failed or pending, we keep the fresh step's new commands and set status to FAILED/PENDING
                        else:
                            fresh_step["status"] = cached_step.get("status", "FAILED")
                    except Exception:
                        pass
                
                self.steps.append(fresh_step)
            
            # Re-save the state to ensure the step-XXX.json files on disk are updated with the fresh commands!
            self.save_state(current_idx=max(0, progress.get("current_step", 1) - 1))
        else:
            logging.info("[Tester] No existing state found. Initializing...")
            self.steps = self.parse_codelab()
            self.save_state()

    def _atomic_write_json(self, filepath: str, data: Any):
        """Writes JSON data atomically via a temporary file."""
        tmp_path = f"{filepath}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, filepath)

    def _atomic_write_text(self, filepath: str, text: str):
        """Writes string content atomically via a temporary file."""
        tmp_path = f"{filepath}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp_path, filepath)

    def save_state(self, current_idx: int = 0, overall_status: str = "IN PROGRESS"):
        progress = {
            "codelab": os.path.basename(self.md_path),
            "total_steps": len(self.steps),
            "current_step": current_idx + 1,
            "status": overall_status
        }
        self._atomic_write_json(os.path.join(self.tester_state_dir, "progress.json"), progress)

        for step in self.steps:
            step_file = os.path.join(self.tester_state_dir, f"step-{step['num']:03d}.json")
            self._atomic_write_json(step_file, step)

        user_inputs = {"PROJECT_ID": self.project_id}
        self._atomic_write_json(os.path.join(self.tester_state_dir, "user_inputs.json"), user_inputs)

    def write_visual_boards(self, overall_status: str = "IN PROGRESS"):
        """Generates premium zero-indentation HTML status charts in tasks.md / test_status.md."""
        if HTMLReporter is not None:
            html_content = HTMLReporter.generate_board(self.project_id, self.steps, overall_status, repo_root)
        else:
            html_content = f"<!-- HTMLReporter unavailable -->\n# Codelab Validation: {overall_status}\n"

        self._atomic_write_text(self.artifact_status_file, html_content)
            
        if self.artifact_task_file:
            self._atomic_write_text(self.artifact_task_file, html_content)

    def file_bug_and_notify_mailbox(self, failed_step: int, failed_command: str, error_output: str):
        """Generates structured bug JSON files in local and centralized inboxes for closed-loop learning."""
        bug_epoch = int(time.time())
        bug_id = f"BUG_{failed_step:03d}_{bug_epoch}"
        
        # Local lab bugs directory
        local_bugs_dir = os.path.join(self.lab_dir, "bugs")
        os.makedirs(local_bugs_dir, exist_ok=True)
        local_bug_file = os.path.join(local_bugs_dir, f"bug_{bug_id}.json")
        
        # Centralized system bugs directory
        central_bugs_dir = os.path.expanduser("~/.gemini/jetski/bugs")
        os.makedirs(central_bugs_dir, exist_ok=True)
        central_bug_file = os.path.join(central_bugs_dir, f"bug_{bug_id}.json")
        
        bug_payload = {
            "bug_id": bug_id,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
            "lab_name": os.path.basename(self.lab_dir),
            "step_number": failed_step,
            "step_title": self.steps[failed_step - 1]["title"],
            "error_logs": {
                "failed_command": failed_command,
                "stderr_output": error_output
            },
            "status": "NEW",
            "remediation": ""
        }
        
        try:
            self._atomic_write_json(local_bug_file, bug_payload)
            self._atomic_write_json(central_bug_file, bug_payload)
            logging.info(f"[Tester] Structured Bug File successfully created locally and centrally: {central_bug_file}")
            
            # Trigger background hook to scan central inbox for FIXED bugs
            processor_script = os.path.join(repo_root, ".agents", "skills", "closed-loop-learning", "scripts", "bug_to_lesson_processor.py")
            if os.path.exists(processor_script):
                subprocess.Popen(
                    ["python3", processor_script, "--scan-dir", central_bugs_dir],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
        except Exception as e:
            logging.error(f"[Tester] Failed to write Bug File: {e}")

    def run(self) -> bool:
        self.load_or_initialize_state()
        
        total_commands = sum(len(step.get("commands", [])) for step in self.steps)
        if total_commands == 0:
            print("no executable commands found — nothing was validated")
            logging.error("[Tester] Hard Failure: No executable commands found in any step.")
            self.save_state(0, "FAILED")
            self.write_visual_boards("FAILED")
            return False
        
        # Load custom variables mapped in variables.json
        custom_vars = {}
        vars_file = os.path.join(self.lab_dir, "variables.json")
        if os.path.exists(vars_file):
            try:
                with open(vars_file, "r", encoding="utf-8") as vf:
                    custom_vars = json.load(vf)
                logging.info(f"[Tester] Loaded {len(custom_vars)} custom variables for replacement.")
            except Exception as e:
                logging.error(f"[Tester] Failed to load variables.json: {e}")
        
        # Determine historical state file for commands
        state_file = self.md_path + ".state"
        env_file = self.md_path + ".env"
        
        executed_hashes = []
        if os.path.exists(state_file):
            with open(state_file, "r") as f:
                executed_hashes = [line.strip() for line in f if line.strip()]

        runner = SubshellRunner(cwd=self.lab_dir)
        try:
            logging.info("[Tester Debug] Active Project ID from self.project_id: %s", self.project_id)
            status, gcloud_config_out = runner.run_command("gcloud config list")
            logging.info("[Tester Debug] subshell gcloud config list (status=%d):\n%s", status, gcloud_config_out)
            status, gcloud_auth_out = runner.run_command("gcloud auth list")
            logging.info("[Tester Debug] subshell gcloud auth list (status=%d):\n%s", status, gcloud_auth_out)

            if executed_hashes and os.path.exists(env_file):
                logging.info("[Tester] Restoring environment from active cache...")
                runner.run_command(f"source {env_file}")
            
            # Export all custom variables from variables.json into the subshell environment as a baseline
            for key, val in custom_vars.items():
                if val and not key.startswith("<"):
                    runner.set_env(key, val)
            
            runner.set_env("PROJECT_ID", self.project_id)
            
            # Iterate and run step state transitions
            for idx, step in enumerate(self.steps):
                if step["status"] == "DONE":
                    logging.info("[Tester] Skipping step %d: %s (already DONE)", step["num"], step["title"])
                    continue
                
                is_cleanup_step = step.get("is_cleanup", False)
                if self.phase == "test" and is_cleanup_step:
                    logging.info("[Tester] Skipping cleanup step %d: %s (deferred to explicit cleanup phase)", step["num"], step["title"])
                    step["status"] = "DEFERRED"
                    step["output"] = "Deferred to explicit cleanup phase."
                    continue
                elif self.phase == "cleanup" and not is_cleanup_step:
                    logging.info("[Tester] Skipping non-cleanup step %d: %s during cleanup phase", step["num"], step["title"])
                    continue
                
                logging.info("[Tester] Running step %d: %s...", step["num"], step["title"])
                step["status"] = "RUNNING"
                self.save_state(idx, "IN PROGRESS")
                self.write_visual_boards("IN PROGRESS")
                
                if not step["commands"]:
                    logging.info("[Tester] Step has no commands. Marked as SKIPPED/NO-OP.")
                    step["status"] = "SKIPPED/NO-OP"
                    continue

                step_failed = False
                step_outputs = []
                step_errors = []
                
                for cmd in step["commands"]:
                    # Sanitize variables and deduplicate flags
                    evaluated_cmd = sanitize_command(cmd, project_id=self.project_id, custom_vars=custom_vars)
                    
                    # Compute hash on evaluated command so runtime variable updates properly invalidate cache
                    cmd_hash = get_cmd_hash(evaluated_cmd)
                    if cmd_hash in executed_hashes:
                        logging.info("[Tester] Command already in cache. Skipping execution.")
                        continue
                    
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
                    self.file_bug_and_notify_mailbox(step["num"], evaluated_cmd, step["error"])
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
    parser.add_argument("--phase", choices=["test", "cleanup", "all"], default="test", help="Execution phase (test, cleanup, or all).")
    parser.add_argument("--cleanup", action="store_true", help="Run explicit cleanup phase (equivalent to --phase cleanup).")
    parser.add_argument("--skip-cleanup", action="store_true", help="Deprecated alias for --phase test.")

    args = parser.parse_args()

    if args.cleanup:
        phase = "cleanup"
    elif args.skip_cleanup:
        phase = "test"
    else:
        phase = args.phase
    tester = StatefulCodelabTester(args.markdown_file, args.artifact_dir, args.timeout, phase=phase)
    success = tester.run()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
