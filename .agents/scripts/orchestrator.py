#!/usr/bin/env python3
"""Central Orchestrator Event Loop for Multi-Subagent Codelab Validation & Self-Healing."""

import argparse
import datetime
import json
import logging
import os
import re
import subprocess
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s INFO: [Orchestrator] %(message)s")

class Orchestrator:
    def __init__(self, markdown_file, artifact_dir=None, skip_cleanup=False):
        self.markdown_file = os.path.abspath(markdown_file)
        self.lab_name = os.path.basename(os.path.dirname(self.markdown_file))
        self.lab_dir = os.path.dirname(self.markdown_file)
        
        # Retrieve or generate conversation-id artifact folder
        if artifact_dir:
            self.artifact_dir = os.path.abspath(artifact_dir)
        else:
            self.artifact_dir = os.path.join(
                os.path.expanduser("~/.gemini/jetski/brain"),
                f"orch-{int(time.time())}"
            )
        os.makedirs(self.artifact_dir, exist_ok=True)
        
        self.skip_cleanup = skip_cleanup
        self.project_id = None
        
        # Path configuration
        self.mailbox_dir = os.path.join("/usr/local/google/home/shacharb/skynet/.agents/mailboxes")
        self.progress_file = os.path.join(self.lab_dir, ".tester_state", "progress.json")
        self.bugs_dir = os.path.join(self.lab_dir, "bugs")
        os.makedirs(self.bugs_dir, exist_ok=True)

    def run_command(self, cmd, cwd=None, capture=True):
        """Executes a system shell command synchronously."""
        logging.info(f"Executing: {cmd}")
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                capture_output=capture,
                text=True,
                check=True,
                encoding="utf-8"
            )
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            logging.error(f"Command failed: {cmd}\nExit code: {e.returncode}\nStderr: {e.stderr}")
            return False, e.stdout, e.stderr

    def phase_0_verify_auth(self):
        """Phase 0: Verify Sandbox Admin active authentication context."""
        logging.info("Starting Phase 0: Pre-Flight Auth Check...")
        verify_script = "/usr/local/google/home/shacharb/skynet/.agents/skills/gcloud-auth-verification/scripts/verify_auth.py"
        
        success, stdout, _ = self.run_command(f"python3 {verify_script}")
        if not success:
            logging.error("Auth check script failed.")
            return False
            
        try:
            auth_info = json.loads(stdout)
            active_account = auth_info.get("active_account", "")
            logging.info(f"Currently active gcloud identity: {active_account}")
            
            if "admin" not in active_account:
                logging.warning("Active account does not template to Sandbox Admin (admin@...). Permissions block may occur.")
            return True
        except json.JSONDecodeError:
            logging.error("Failed to parse verify_auth.py JSON output.")
            return False

    def phase_1_preflight_lint(self):
        """Phase 1: Statically parse and audit gcloud commands for syntax gotchas."""
        logging.info("Starting Phase 1: Pre-Flight Static Command Audit...")
        
        if not os.path.exists(self.markdown_file):
            logging.error(f"Codelab markdown file not found at: {self.markdown_file}")
            return False
            
        with open(self.markdown_file, "r") as f:
            content = f.read()
            
        # Extract bash blocks
        bash_blocks = re.findall(r"```bash\n(.*?)\n```", content, re.DOTALL)
        commands = []
        for block in bash_blocks:
            commands.extend([cmd.strip() for cmd in block.split("\n") if cmd.strip() and not cmd.strip().startswith("#")])
            
        logging.info(f"Extracted {len(commands)} commands for static linting.")
        
        # Perform static checks (Mocking Developer Docs MCP rules statically)
        for cmd in commands:
            if "network-firewall-policies rules create" in cmd and "--layer4-configs" not in cmd:
                logging.error("LINT ERROR: Found 'network-firewall-policies rules create' command missing the mandatory --layer4-configs parameter flag!")
                return False
            if "instance-templates create" in cmd and "--region" not in cmd:
                logging.error("LINT ERROR: Found GCE 'instance-templates create' command missing --region tag, which will trigger API parameter blocks!")
                return False
                
        logging.info("Pre-Flight Static Command Audit passed successfully.")
        return True

    def phase_2_provision_sandbox(self):
        """Phase 2: Dynamically create a test project and link billing."""
        logging.info("Starting Phase 2: GCP Sandbox Project Provisioning...")
        provision_script = "/usr/local/google/home/shacharb/skynet/.agents/skills/gcp-provisioning/scripts/create_project.py"
        
        success, stdout, _ = self.run_command(f"python3 {provision_script} {self.lab_name}")
        if not success:
            logging.error("GCP project provisioning script failed.")
            return False
            
        # Extract project ID from stdout
        match = re.search(r"SUCCESS: Project (.*?) setup complete", stdout)
        if not match:
            logging.error("Failed to parse generated Project ID from provisioning output.")
            return False
            
        self.project_id = match.group(1).strip()
        logging.info(f"Successfully provisioned sandbox Project ID: {self.project_id}")
        
        # Disable org policies
        logging.info("Disabling organization policy constraints...")
        policy_script = "/usr/local/google/home/shacharb/skynet/.agents/skills/gcp-provisioning/scripts/disable_org_policies.sh"
        success, _, _ = self.run_command(f"bash {policy_script} {self.project_id}")
        if not success:
            logging.error("Failed to override organization policies.")
            return False
            
        # Set active project
        success, _, _ = self.run_command(f"gcloud config set project {self.project_id}")
        if not success:
            logging.error("Failed to configure active gcloud project context.")
            return False
            
        return True

    def phase_3_execute_validation(self):
        """Phase 3: Asynchronously run stateful E2E testing and poll progress loop."""
        logging.info("Starting Phase 3: Stateful E2E Validation...")
        tester_script = "/usr/local/google/home/shacharb/skynet/.agents/skills/codelab-validation/scripts/tester.py"
        
        # Construct validation execution command
        cmd = f"python3 {tester_script} {self.markdown_file} --artifact-dir {self.artifact_dir}"
        if self.skip_cleanup:
            cmd += " --skip-cleanup"
            
        # Launch validation as background subprocess
        logging.info("Invoking stateful tester engine in background...")
        proc = subprocess.Popen(
            cmd,
            shell=True,
            cwd="/usr/local/google/home/shacharb/skynet",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Active event polling loop
        while proc.poll() is None:
            time.sleep(10)
            
            # Intercept live progress state
            if os.path.exists(self.progress_file):
                try:
                    with open(self.progress_file, "r") as f:
                        progress = json.load(f)
                        
                    logging.info(
                        f"Active Step: {progress.get('current_step')} / {progress.get('total_steps')} "
                        f"| Status: {progress.get('status')}"
                    )
                    
                    # Check for failure states
                    if progress.get("status") == "FAILED":
                        logging.error("Validation failure detected on the Blackboard! Initiating diagnostic loop...")
                        proc.terminate()
                        self.phase_3_5_diagnose_and_self_heal(progress.get("current_step"))
                        return False
                except (json.JSONDecodeError, IOError):
                    continue
                    
        # Handle completion exit codes
        if proc.returncode == 0:
            logging.info("E2E validation completed successfully! Verdict: SUCCESS")
            return True
        else:
            logging.error(f"Validation script crashed with exit code: {proc.returncode}")
            return False

    def phase_3_5_diagnose_and_self_heal(self, failed_step):
        """Phase 3.5: Diagnoses failures, generates structured bugs, and heals syntax in-place."""
        logging.info(f"Beginning Self-Healing Diagnostic for Step {failed_step}...")
        step_file = os.path.join(self.lab_dir, ".tester_state", f"step-{failed_step:03d}.json")
        
        if not os.path.exists(step_file):
            logging.error(f"Step details state file not found at: {step_file}")
            return
            
        with open(step_file, "r") as f:
            step_data = json.load(f)
            
        failed_command = step_data.get("commands", ["Unknown"])[-1]
        error_output = step_data.get("error", "Unknown execution error.")
        
        # 1. Write structured Bug File locally (Data Isolation)
        bug_id = f"BUG_{failed_step:03d}_{int(time.time())}"
        bug_file = os.path.join(self.bugs_dir, f"bug_{bug_id}.json")
        
        bug_payload = {
            "bug_id": bug_id,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "lab_name": self.lab_name,
            "step_number": failed_step,
            "step_title": step_data.get("title"),
            "error_logs": {
                "failed_command": failed_command,
                "stderr_output": error_output
            },
            "status": "NEW"
        }
        
        with open(bug_file, "w") as bf:
            json.dump(bug_payload, bf, indent=2)
        logging.info(f"Structured Bug File filed locally: {bug_file}")
        
        # 2. Write Pointer Envelope to Mailbox (Clean communication)
        mailbox_envelope = {
            "status": "FAILED",
            "bug_id": bug_id,
            "bug_pointer": f"labs/dev/{self.lab_name}/bugs/bug_{bug_id}.json"
        }
        
        mailbox_file = os.path.join(
            self.mailbox_dir, "orchestrator", "inbox", f"msg_{int(time.time())}.json"
        )
        os.makedirs(os.path.dirname(mailbox_file), exist_ok=True)
        with open(mailbox_file, "w") as mf:
            json.dump(mailbox_envelope, mf, indent=2)
            
        # Subagents must notify user cleanly using chat pointer
        print(f"\n📢 [Chaos Tester] I found bug {bug_id}! Pointer: file://{bug_file}\n")

    def execute_pipeline(self):
        """Orchestrates the full E2E verification loop."""
        if not self.phase_0_verify_auth():
            return False
        if not self.phase_1_preflight_lint():
            return False
        if not self.phase_2_provision_sandbox():
            return False
        if not self.phase_3_execute_validation():
            # Self-healing was triggered. Let user choose to re-engage
            return False
        return True

def main():
    parser = argparse.ArgumentParser(description="Master Orchestrator Runner Script.")
    parser.add_argument("markdown_file", help="Path to the target codelab .lab.md file.")
    parser.add_argument("--artifact-dir", help="Optional custom artifact folder.")
    parser.add_argument("--skip-cleanup", action="store_true", help="Retain GCP test resources.")
    
    args = parser.parse_args()
    
    orchestrator = Orchestrator(args.markdown_file, args.artifact_dir, args.skip_cleanup)
    success = orchestrator.execute_pipeline()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
