#!/usr/bin/env python3
"""POSIX-Backed Atomic Mailbox Message Broker for Multi-Subagent Orchestration.

Enforces Carl Hewitt's Actor Model communication axioms, Erlang-style
decoupled resilience, and thread-safe POSIX atomic directory commits.
"""

import os
import json
import time
import uuid
import logging
import datetime
import shutil

logging.basicConfig(level=logging.INFO, format="%(asctime)s INFO: [MailboxBroker] %(message)s")

def resolve_workspace_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != os.path.dirname(current):
        if os.path.exists(os.path.join(current, ".agents")):
            return current
        current = os.path.dirname(current)
    # Fallback
    return "/usr/local/google/home/shacharb/skynet"

WORKSPACE_ROOT = resolve_workspace_root()
MAILBOX_BASE_DIR = os.path.join(WORKSPACE_ROOT, ".agents/mailboxes")

class MailboxBroker:
    def __init__(self, base_dir=MAILBOX_BASE_DIR):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_agent_mailbox(self, agent_name):
        """Get and create inbox/outbox directories for a specific agent."""
        agent_dir = os.path.join(self.base_dir, agent_name)
        inbox = os.path.join(agent_dir, "inbox")
        outbox = os.path.join(agent_dir, "outbox")
        os.makedirs(inbox, exist_ok=True)
        os.makedirs(outbox, exist_ok=True)
        return inbox, outbox

    def send_message(self, sender, recipient, action_type, blackboard_pointers, payload=None):
        """Atomically sends a structured JSON envelope to a recipient's inbox.
        
        Follows POSIX atomic write protocols: writes to /tmp/ first, then renames
        the file to eliminate write collisions and locks in concurrent systems.
        """
        if payload is None:
            payload = {}

        # 1. Setup recipient mailbox
        recipient_inbox, _ = self._get_agent_mailbox(recipient)
        _, sender_outbox = self._get_agent_mailbox(sender)

        # 2. Build structured, schema-compliant message envelope
        msg_epoch = int(time.time())
        msg_uuid = uuid.uuid4().hex[:8]
        message_id = f"MSG_{msg_epoch}_{msg_uuid}"
        filename = f"msg_{msg_epoch}_{msg_uuid}.json"

        envelope = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "message_id": message_id,
            "sender": sender,
            "recipient": recipient,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
            "action_type": action_type,
            "blackboard_pointers": blackboard_pointers,
            "payload": payload
        }

        # 3. Write to temporary location on the exact same partition/folder mount to ensure atomic POSIX rename
        temp_dir = os.path.join(sender_outbox, ".tmp")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"{filename}.tmp")

        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(envelope, f, indent=2)
            
            # 4. Atomically commit the file into the recipient's inbox via POSIX rename
            final_inbox_path = os.path.join(recipient_inbox, filename)
            os.rename(temp_path, final_inbox_path)
            
            # 5. Write duplicate copy to sender's outbox directory for logging/tracing
            final_outbox_path = os.path.join(sender_outbox, filename)
            shutil.copy2(final_inbox_path, final_outbox_path)

            logging.info(f"Message {message_id} atomically dispatched from '{sender}' to '{recipient}'.")
            
            # 6. Print E2E visible Chat-Pointer with clickable workspace hyperlink
            relative_inbox_path = os.path.relpath(final_inbox_path, WORKSPACE_ROOT)
            print(f"\n📢 [{sender.replace('-', ' ').title()}] I sent message '{message_id}' to '{recipient}'.")
            print(f"   Pointer Envelope: [{filename}](file://{final_inbox_path})\n")

            return message_id, final_inbox_path

        except Exception as e:
            logging.error(f"POSIX atomic send failed from '{sender}' to '{recipient}': {e}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            raise e

    def poll_inbox(self, agent_name):
        """Polls an agent's inbox and returns parsed messages."""
        inbox_dir, _ = self._get_agent_mailbox(agent_name)
        if not os.path.exists(inbox_dir):
            return []

        message_files = sorted([f for f in os.listdir(inbox_dir) if f.endswith(".json")])
        parsed_messages = []

        for filename in message_files:
            file_path = os.path.join(inbox_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    envelope = json.load(f)
                parsed_messages.append((filename, file_path, envelope))
            except Exception as e:
                logging.error(f"Failed to parse queued inbox message '{filename}': {e}")

        return parsed_messages

    def archive_to_outbox(self, agent_name, filename):
        """Atomically moves processed inbox messages to the outbox archive."""
        inbox_dir, outbox_dir = self._get_agent_mailbox(agent_name)
        src_path = os.path.join(inbox_dir, filename)
        dest_path = os.path.join(outbox_dir, filename)

        if not os.path.exists(src_path):
            logging.error(f"Archive source file '{src_path}' does not exist.")
            return False

        temp_dest = dest_path + ".tmp"
        try:
            # Copy to temp, then atomically rename on destination
            shutil.copy2(src_path, temp_dest)
            os.rename(temp_dest, dest_path)
            os.remove(src_path)
            logging.info(f"Message '{filename}' atomically archived to outbox.")
            return True
        except Exception as e:
            logging.error(f"Failed to atomically archive processed message '{filename}': {e}")
            if os.path.exists(temp_dest):
                try:
                    os.remove(temp_dest)
                except OSError:
                    pass
            return False

    def clean_expired_messages(self, max_age_days=7):
        """Scans all mailboxes and purges messages older than max_age_days."""
        logging.info(f"Starting mailbox cleaner sweeper (Max Age: {max_age_days} days)...")
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=max_age_days)
        purged_count = 0

        for root, _, files in os.walk(self.base_dir):
            for filename in files:
                if filename.endswith(".json"):
                    file_path = os.path.join(root, filename)
                    try:
                        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(file_path), datetime.timezone.utc)
                        if mtime < cutoff:
                            os.remove(file_path)
                            purged_count += 1
                    except Exception as e:
                        logging.error(f"Sweeper failed to process file '{file_path}': {e}")

        if purged_count > 0:
            logging.info(f"Mailbox sweeper completed. Purged {purged_count} expired message file(s).")
        else:
            logging.info("Mailbox sweeper completed. No expired messages found.")

if __name__ == "__main__":
    # Basic library integrity check
    broker = MailboxBroker()
    broker.clean_expired_messages(7)
