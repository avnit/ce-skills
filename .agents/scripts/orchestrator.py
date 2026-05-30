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

sys.path.append("/usr/local/google/home/shacharb/skynet/.agents/scripts")
try:
    from mailbox_handler import MailboxBroker
except ImportError:
    pass

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
        """Phase 1: Statically parse and audit gcloud commands and formatting layout."""
        logging.info("Starting Phase 1: Pre-Flight Static & Formatting Audit...")
        
        if not os.path.exists(self.markdown_file):
            logging.error(f"Codelab markdown file not found at: {self.markdown_file}")
            return False

        # Ingest pre-generated Codelab Reviewer subagent style audit report
        logging.info("Reading pre-generated Subagent Codelab Style Audit Report...")
        
        report_file = os.path.join(self.lab_dir, "style_audit_report.json")
        
        if not os.path.exists(report_file):
            logging.error(f"LINT ERROR: Style audit report not found at {report_file}!")
            logging.error("Please ensure the 'codelab-reviewer' subagent has executed first.")
            return False

        try:
            with open(report_file, "r", encoding="utf-8") as rf:
                report_data = json.load(rf)
        except Exception as e:
            logging.error(f"Failed to read subagent style audit report: {e}")
            return False

        status = report_data.get("audit_status", "NEEDS_REVISION")
        scorecard = report_data.get("scorecard", {})
        remediations = report_data.get("critical_remediations", [])

        logging.info(f"Subagent Style Audit Verdict: {status} | Scores: {scorecard}")

        if status == "NEEDS_REVISION":
            logging.error("LINT ERROR: Codelab Markdown Formatting standards violated!")
            for rem in remediations:
                step = rem.get("step_number", "N/A")
                issue = rem.get("issue_type", "N/A")
                desc = rem.get("description", "N/A")
                rec = rem.get("recommendation", "N/A")
                logging.error(f"Formatting Check Failure (Step {step} - {issue}): {desc}")
                logging.error(f"  Suggested Recommendation: {rec}")
            return False

        logging.info("Dynamic Markdown Formatting Audit passed successfully.")
            
        with open(self.markdown_file, "r") as f:
            content = f.read()
            
        # Extract bash blocks
        bash_blocks = re.findall(r"```bash\n(.*?)\n```", content, re.DOTALL)
        commands = []
        for block in bash_blocks:
            current_cmd = ""
            for line in block.split("\n"):
                line_s = line.strip()
                if not line_s or line_s.startswith("#"):
                    continue
                if line_s.endswith("\\"):
                    current_cmd += " " + line_s[:-1].strip()
                else:
                    current_cmd += " " + line_s
                    commands.append(current_cmd.strip())
                    current_cmd = ""
            if current_cmd.strip():
                commands.append(current_cmd.strip())
            
        logging.info(f"Extracted {len(commands)} commands for static linting.")
        
        # Perform static checks (Mocking Developer Docs MCP rules statically)
        for cmd in commands:
            if "network-firewall-policies rules create" in cmd and "--layer4-configs" not in cmd:
                logging.error("LINT ERROR: Found 'network-firewall-policies rules create' command missing the mandatory --layer4-configs parameter flag!")
                return False
            if "instance-templates create" in cmd and "--region" not in cmd:
                logging.error("LINT ERROR: Found GCE 'instance-templates create' command missing --region tag, which will trigger API parameter blocks!")
                return False
                
        logging.info("Pre-Flight Static Command & Formatting Audit passed successfully.")
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
        os.environ["CLOUDSDK_CORE_PROJECT"] = self.project_id
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
        """Phase 3: Asynchronously run stateful E2E testing and poll Orchestrator mailbox reactively."""
        logging.info("Starting Phase 3: Reactive Stateful E2E Validation...")
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
            cwd="/usr/local/google/home/shacharb/skynet"
        )
        
        broker = MailboxBroker()
        
        # Active reactive event polling loop
        while True:
            time.sleep(5)
            
            # Poll Orchestrator Inbox for reactive subagent messages
            messages = broker.poll_inbox("orchestrator")
            for filename, file_path, envelope in messages:
                action_type = envelope.get("action_type")
                sender = envelope.get("sender")
                message_id = envelope.get("message_id")
                pointers = envelope.get("blackboard_pointers", {})
                payload = envelope.get("payload", {})
                
                logging.info(f"Received message '{message_id}' from '{sender}' | Action: {action_type}")
                
                if action_type == "REMEDIATE" or payload.get("status") == "FAILED":
                    bug_id = payload.get("bug_id")
                    bug_report = pointers.get("bug_report")
                    findings = payload.get("findings_summary", "No findings summary provided.")
                    
                    logging.error(f"Validation failure envelope detected: {bug_id}")
                    logging.error(f"Subagent findings: {findings}")
                    
                    # Resolve absolute path of the bug pointer
                    if bug_report and os.path.exists(bug_report):
                        logging.info(f"Loading decentralized Bug File from: {bug_report}")
                        try:
                            with open(bug_report, "r", encoding="utf-8") as bf:
                                bug_details = json.load(bf)
                            failed_command = bug_details.get("error_logs", {}).get("failed_command", "N/A")
                            stderr_output = bug_details.get("error_logs", {}).get("stderr_output", "N/A")
                            
                            # Perform self-healing or diagnose
                            self.execute_self_healing_on_bug(bug_id, failed_command, stderr_output, bug_report)
                        except Exception as e:
                            logging.error(f"Failed to read subagent bug details: {e}")
                    
                    # POSIX Atomic Archive to outbox
                    broker.archive_to_outbox("orchestrator", filename)
                    
                    # Terminate subagent process if running
                    if proc.poll() is None:
                        proc.terminate()
                    return False
                
                # Archive processed message to outbox
                broker.archive_to_outbox("orchestrator", filename)
            
            # Check if process exited
            exit_code = proc.poll()
            if exit_code is not None:
                if exit_code == 0:
                    logging.info("E2E validation completed successfully! Verdict: SUCCESS")
                    return True
                else:
                    logging.error(f"Validation script exited with non-zero return code: {exit_code}")
                    # Check if there's a leftover message in the inbox we missed in this tick
                    leftover_messages = broker.poll_inbox("orchestrator")
                    if leftover_messages:
                        continue
                    return False

    def execute_self_healing_on_bug(self, bug_id, failed_command, stderr_output, bug_path):
        """Executes syntax diagnostic self-healing on target bug files."""
        logging.info(f"Self-Healing Engine triggered for Bug ID: {bug_id}")
        
        # Check if this is the classic Network Firewall policy error (missing --layer4-configs)
        if "network-firewall-policies rules create" in failed_command and "Must be specified" in stderr_output and "--layer4-configs" not in failed_command:
            logging.info("Identified syntax gotcha: Missing --layer4-configs on firewall rules create!")
            
            try:
                with open(bug_path, "r") as bf:
                    bug_data = json.load(bf)
                
                bug_data["status"] = "HEALED"
                bug_data["remediation"] = {
                    "suggested_command": failed_command + " --layer4-configs=tcp:80,tcp:443,icmp",
                    "explanation": "Added missing mandatory --layer4-configs flag for global network firewall ingress rule."
                }
                
                with open(bug_path, "w") as bf:
                    json.dump(bug_data, bf, indent=2)
                
                logging.info(f"Bug file updated to HEALED status with remediation payload: {bug_path}")

                # Perform active in-place source markdown file patching to prevent infinite loops
                suggested_command = bug_data["remediation"]["suggested_command"]
                if os.path.exists(self.markdown_file):
                    logging.info(f"Applying active in-place patch to source Markdown: {self.markdown_file}")
                    with open(self.markdown_file, "r", encoding="utf-8") as mf:
                        md_content = mf.read()
                    
                    # Exact string replacement of the failed command with the healed command
                    patched_md = md_content.replace(failed_command, suggested_command)
                    
                    with open(self.markdown_file, "w", encoding="utf-8") as mf:
                        mf.write(patched_md)
                    logging.info("Source Codelab Markdown patched successfully!")
                else:
                    logging.error(f"Markdown source file does not exist at path: {self.markdown_file}")

                # Perform active in-place patch to cached step JSON file if it exists to prevent stale cache replay
                failed_step = bug_data.get("step_number")
                if failed_step:
                    step_file = os.path.join(self.lab_dir, ".tester_state", f"step-{failed_step:03d}.json")
                    if os.path.exists(step_file):
                        logging.info(f"Applying active in-place patch to cached step JSON file: {step_file}")
                        try:
                            with open(step_file, "r", encoding="utf-8") as sf:
                                step_data = json.load(sf)
                            
                            cmd_list = step_data.get("commands", [])
                            for c_idx, cmd in enumerate(cmd_list):
                                if cmd.strip() == failed_command.strip():
                                    cmd_list[c_idx] = suggested_command
                                    break
                            
                            step_data["commands"] = cmd_list
                            
                            with open(step_file, "w", encoding="utf-8") as sf:
                                json.dump(step_data, sf, indent=2)
                            logging.info("Cached step JSON file patched successfully!")
                        except Exception as e:
                            logging.error(f"Failed to patch cached step JSON file: {e}")

            except Exception as e:
                logging.error(f"Failed to update bug file state or patch source markdown: {e}")
        else:
            logging.warning("Bug matches no predefined syntax remediation signatures. Manual review recommended.")

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
    parser.add_argument("markdown_file", nargs="?", default=None, help="Path to the target codelab .lab.md file.")
    parser.add_argument("--artifact-dir", help="Optional custom artifact folder.")
    parser.add_argument("--skip-cleanup", action="store_true", help="Retain GCP test resources.")
    
    args = parser.parse_args()
    
    if not args.markdown_file:
        logging.error("markdown_file is required")
        sys.exit(1)
        
    orchestrator = Orchestrator(args.markdown_file, args.artifact_dir, args.skip_cleanup)
    success = orchestrator.execute_pipeline()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
