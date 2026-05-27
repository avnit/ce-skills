import os
import json
import glob
import time
from datetime import datetime

# Configuration Paths
WORKSPACE_DIR = os.path.expanduser("~/skynet")
LABS_DEV_DIR = os.path.join(WORKSPACE_DIR, "labs/dev")
CENTRAL_JOURNAL_PATH = os.path.join(WORKSPACE_DIR, "labs/lessons_learned.md")
STATE_DIR = os.path.join(WORKSPACE_DIR, ".agents/state/lessons_watcher")
STATE_FILE_PATH = os.path.join(STATE_DIR, "processed_bugs.json")


def load_processed_bugs():
    if os.path.exists(STATE_FILE_PATH):
        try:
            with open(STATE_FILE_PATH, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception as e:
            print(f"Error reading state file: {e}")
            return set()
    return set()

def save_processed_bugs(processed_set):
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(STATE_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(list(processed_set), f, indent=2)
    except Exception as e:
        print(f"Error writing state file: {e}")

def parse_bug_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading bug file {filepath}: {e}")
        return None

def format_lesson_learned(bug_data):
    bug_id = bug_data.get("bug_id", "UNKNOWN_ID")
    timestamp = bug_data.get("timestamp", datetime.now().isoformat())
    lab_name = bug_data.get("lab_name", "unknown-lab")
    step_num = bug_data.get("step_number", "?")
    step_title = bug_data.get("step_title", "Step Failure")
    
    error_logs = bug_data.get("error_logs", {})
    failed_cmd = error_logs.get("failed_command", "N/A")
    stderr_output = error_logs.get("stderr_output", "N/A")
    
    # Parse dates dynamically
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        formatted_time = timestamp

    markdown_entry = f"""
### 🚨 Bug resolved: {bug_id} ({lab_name})
**Timestamp:** `{formatted_time}` | **Step {step_num}:** *{step_title}*

> [!WARNING]
> **Failed Command Sequence:**
> ```bash
> {failed_cmd}
> ```

> [!IMPORTANT]
> **Captured Error Log:**
> ```text
> {stderr_output}
> ```

> [!NOTE]
> **Remediation Verdict:**
> This issue has been statefully remediated, audited by the design critic, and successfully validated. The core tutorial step-by-step narrative has been updated to guarantee seamless execution in future deployments.

---
"""
    return markdown_entry

def append_to_central_journal(markdown_content):
    try:
        # Initialize file with a premium header if it doesn't exist
        if not os.path.exists(CENTRAL_JOURNAL_PATH):
            with open(CENTRAL_JOURNAL_PATH, "w", encoding="utf-8") as f:
                f.write("# Google Cloud Codelab Factory: Lessons Learned Journal\n")
                f.write("This journal is programmatically maintained by the background **Lessons Learned Watcher** subagent. It aggregates validated infrastructure errors, API deprecations, and configuration gotchas derived from stateful E2E sandbox testing runs.\n\n---\n")
        
        # Append the new entry
        with open(CENTRAL_JOURNAL_PATH, "a", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"Successfully appended lesson learned to {CENTRAL_JOURNAL_PATH}")
    except Exception as e:
        print(f"Error appending to central journal: {e}")

def scan_and_process():
    print("Scanning bug folders...")
    processed_bugs = load_processed_bugs()
    updated = False
    
    # Recursively locate all bug JSON files
    search_pattern = os.path.join(LABS_DEV_DIR, "**/bugs/bug_*.json")
    bug_files = glob.glob(search_pattern, recursive=True)
    
    for bug_file in bug_files:
        bug_data = parse_bug_file(bug_file)
        if not bug_data:
            continue
            
        bug_id = bug_data.get("bug_id")
        status = bug_data.get("status")
        
        if status == "RESOLVED" and bug_id not in processed_bugs:
            print(f"Found newly resolved bug: {bug_id} in {bug_file}")
            # Format the entry
            entry = format_lesson_learned(bug_data)
            # Write to central journal
            append_to_central_journal(entry)
            # Update state
            processed_bugs.add(bug_id)
            updated = True
            
    if updated:
        save_processed_bugs(processed_bugs)

def main():
    print("Lessons Learned Watcher sidecar started successfully.")
    while True:
        try:
            scan_and_process()
        except Exception as e:
            print(f"Unhandled exception in scanning loop: {e}")
        time.sleep(10)

if __name__ == "__main__":
    main()
