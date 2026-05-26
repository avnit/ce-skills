# System Architecture Design: Transition to True Decentralized Actor-Mailboxes

> [!IMPORTANT]
> **Core Alignment Objection Resolved**: In the initial bootstrap pilot, `orchestrator.py` polled progress and wrote bug logs/mailbox messages *on behalf* of the subagent. This constitutes a "faked" mailbox implementation. To satisfy true **Erlang/Akka Actor Model standards**, we must fully decentralize execution: **each individual subagent must possess the native capacity to write and read its own inbox/outbox messages directly from its own context.**

---

## 1. The Decentralized Actor Model

Under a true Actor Model, the Orchestrator does not poll or maintain nested knowledge of a subagent's internal steps. The subagent is an active, autonomous entity that runs its script, and when it catches an exception, **the subagent itself compiles and writes the bug file and mailbox envelope to the Blackboard.**

```
                             [ ORCHESTRATOR ]
                              (Reactive Loop)
                                    ▲
                                    │ Reads reply pointer
                                    │ (msg_BUG801.json)
                                    │
                      ┌─────────────┴─────────────┐
                      │  orchestrator Inbox       │
                      │  (mailboxes/orch/inbox/)  │
                      └─────────────▲─────────────┘
                                    │ Writes pointer
                                    │
                          [ CHAOS TESTER (QA) ]
                           - Runs tester.py natively
                           - Catches syntax error
                           - Writes labs/dev/[lab]/bugs/bug_BUG801.json
```

---

## 2. Skill-Level Integration (Decentralizing `tester.py`)

Instead of having `orchestrator.py` poll progress files, we embed the bug and mailbox pointer writing routines **directly inside the subagent's skill scripts** (specifically, `tester.py` inside `.agents/skills/codelab-validation/scripts/tester.py`).

### Remediated `tester.py` Error Interceptor (Python Spec)
When a step command execution fails inside the subshell, `tester.py` intercepts the CalledProcessError and executes the mailbox write natively:

```python
# Refactored section inside tester.py
import os
import json
import time
import datetime

def file_bug_and_notify_mailbox(failed_step, failed_command, stderr_output, lab_name, lab_dir):
    bug_id = f"BUG_{failed_step:03d}_{int(time.time())}"
    bugs_dir = os.path.join(lab_dir, "bugs")
    os.makedirs(bugs_dir, exist_ok=True)
    
    # 1. Write Detailed Bug File locally (Data Isolation)
    bug_file = os.path.join(bugs_dir, f"bug_{bug_id}.json")
    bug_payload = {
        "bug_id": bug_id,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "lab_name": lab_name,
        "step_number": failed_step,
        "error_logs": {
            "failed_command": failed_command,
            "stderr_output": stderr_output
        },
        "status": "NEW"
    }
    with open(bug_file, "w") as f:
        json.dump(bug_payload, f, indent=2)
        
    # 2. Write Pointer Envelope directly into Orchestrator Inbox
    mailbox_dir = "/usr/local/google/home/shacharb/skynet/.agents/mailboxes/orchestrator/inbox"
    os.makedirs(mailbox_dir, exist_ok=True)
    
    pointer_envelope = {
        "status": "FAILED",
        "bug_id": bug_id,
        "bug_pointer": f"labs/dev/{lab_name}/bugs/bug_{bug_id}.json"
    }
    
    msg_file = os.path.join(mailbox_dir, f"msg_{int(time.time())}.json")
    with open(msg_file, "w") as f:
        json.dump(pointer_envelope, f, indent=2)
        
    # 3. Print Chat-Pointer reference for User Visibility
    print(f"\n📢 [Chaos Tester] I found bug {bug_id}! Pointer: file://{bug_file}\n")
```

---

## 3. Refactored Orchestrator Loop (Pure Reactive State)

With mailbox-writing delegated to the active subagent, the central `orchestrator.py` loop is refactored to be **100% reactive and lightweight**:

*   **Before**: Polled `.tester_state/progress.json` every 10 seconds, terminating the subprocess on `FAILED` and writing files.
*   **After**: Launches `tester.py` and simply polls the Orchestrator mailbox directory (`.agents/mailboxes/orchestrator/inbox/`) for new `msg_NNN.json` files. 
    *   *The Flow*: The moment `tester.py` writes the envelope, `orchestrator.py` detects the file, parses the `bug_pointer` path dynamically, executes diagnostic SSH commands, patches the markdown, marks the bug `RESOLVED`, and writes a `REENGAGE` pointer to `mailboxes/chaos-tester/inbox/` to resume the test run.

---

## 4. Architectural Evaluation: Faked vs. Decentralized Mailboxes

| Architectural Metric | Orchestrator-Faked Polling | Decentralized Actor Mailbox (Remediated) |
| :--- | :--- | :--- |
| **Actor Autonomy** | Low (Orchestrator babysits the subagent's state). | **High** (Subagent acts as an independent, active entity). |
| **Boilerplate Separation** | Weak (Runner contains step-parsing and cgroup-logs logic). | **Perfect** (Runner strictly handles file polling; logic sits in skill). |
| **Multi-threading Safety**| Weak (Concurrent polling of the same JSON can lock files). | **High** (File system inbox queues are naturally thread-safe). |
| **Erlang Compliance** | No. | **Yes** (Matches standard decentralized actor message-passing). |

### Conclusion
Decentralizing the mail-writing logic by embedding it **directly inside the subagent's skill scripts** is the superior, standard-compliant architectural pattern. It creates true autonomous specialists, isolates log bloat to the skill context, and allows the Orchestrator to run as a lightweight, reactive event router!
