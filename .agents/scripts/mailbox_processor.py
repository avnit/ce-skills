#!/usr/bin/env python3
"""Active Mailbox Processor Daemon for Multi-Subagent Self-Healing Loops."""

import os
import sys
import json
import shutil
import logging
import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s INFO: [MailboxProcessor] %(message)s")

_script_dir = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.abspath(os.path.join(_script_dir, "..", ".."))
MAILBOX_DIR = os.path.join(WORKSPACE_ROOT, ".agents/mailboxes/orchestrator")
INBOX_DIR = os.path.join(MAILBOX_DIR, "inbox")
OUTBOX_DIR = os.path.join(MAILBOX_DIR, "outbox")

def setup_directories():
    os.makedirs(INBOX_DIR, exist_ok=True)
    os.makedirs(OUTBOX_DIR, exist_ok=True)

def process_inbox():
    setup_directories()
    messages = [f for f in os.listdir(INBOX_DIR) if f.endswith(".json")]
    
    if not messages:
        logging.info("No new mailbox messages in inbox.")
        return

    logging.info(f"Found {len(messages)} message(s) to process.")

    for msg_file in messages:
        msg_path = os.path.join(INBOX_DIR, msg_file)
        logging.info(f"Ingesting message: {msg_file}")

        try:
            with open(msg_path, "r") as f:
                envelope = json.load(f)
        except Exception as e:
            logging.error(f"Failed to parse message JSON {msg_file}: {e}")
            continue

        status = envelope.get("status")
        bug_id = envelope.get("bug_id")
        bug_pointer = envelope.get("bug_pointer")

        logging.info(f"Envelope status: {status} | Bug ID: {bug_id}")

        if status == "FAILED" and bug_pointer:
            # Resolve relative or absolute path of the bug pointer
            full_bug_path = os.path.join(WORKSPACE_ROOT, bug_pointer)
            if not os.path.exists(full_bug_path):
                # Try resolving as relative directly if it contains workspace path
                full_bug_path = bug_pointer

            if os.path.exists(full_bug_path):
                logging.info(f"Loading detailed Bug File: {full_bug_path}")
                try:
                    with open(full_bug_path, "r") as bf:
                        bug_details = json.load(bf)
                    
                    failed_command = bug_details.get("error_logs", {}).get("failed_command", "N/A")
                    stderr_output = bug_details.get("error_logs", {}).get("stderr_output", "N/A")
                    step_number = bug_details.get("step_number", "N/A")
                    step_title = bug_details.get("step_title", "N/A")

                    logging.info(f"CRITICAL FAILURE ON STEP {step_number}: {step_title}")
                    logging.info(f"Failed command: {failed_command}")
                    logging.info(f"Stderr error: {stderr_output}")

                    # Trigger in-memory Self-Healing notification stub
                    # In a full agent-run, this script signals the parent to run self-healing
                    execute_self_healing(bug_id, failed_command, stderr_output, full_bug_path)

                except Exception as e:
                    logging.error(f"Error reading bug file {full_bug_path}: {e}")
            else:
                logging.error(f"Bug file referenced in envelope does not exist: {full_bug_path}")

        # POSIX Atomic Move from inbox to outbox
        dest_path = os.path.join(OUTBOX_DIR, msg_file)
        try:
            # Write to a temp file and atomically rename to prevent race conditions
            temp_dest = dest_path + ".tmp"
            shutil.copy2(msg_path, temp_dest)
            os.rename(temp_dest, dest_path)
            os.remove(msg_path)
            logging.info(f"Message {msg_file} atomically moved to outbox.")
        except Exception as e:
            logging.error(f"Failed to atomically archive message {msg_file}: {e}")

def execute_self_healing(bug_id, failed_command, stderr_output, bug_path):
    logging.info(f"Self-Healing Engine triggered for Bug ID: {bug_id}")
    
    # Check if this is the classic Network Firewall policy error (missing --layer4-configs)
    if "network-firewall-policies rules create" in failed_command and "Must be specified" in stderr_output and "--layer4-configs" not in failed_command:
        logging.info("Identified syntax gotcha: Missing --layer4-configs on firewall rules create!")
        logging.info("Suggested fix: Append --layer4-configs=tcp:80 or similar layer-4 configuration.")
        
        # Write recommendation to the bug file to update its state
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
        except Exception as e:
            logging.error(f"Failed to update bug file state: {e}")
    else:
        logging.warning("Bug matches no predefined syntax remediation signatures. Manual review recommended.")

if __name__ == "__main__":
    process_inbox()
