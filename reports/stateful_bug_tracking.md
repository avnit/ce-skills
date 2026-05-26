# System Architecture Design: Stateful Bug Tracking & Asynchronous Re-engagement Loop

> [!NOTE]
> **Objective**: Design a structured, event-driven **Stateful Bug Tracking System** that models the QA-to-Architect escalation lifecycle. Enable subagents to file structured bug files on the Blackboard, allow the Orchestrator (or a human engineer) to apply in-place fixes, and cleanly trigger subagent re-engagement to resume from the exact failure point without losing state.

---

## 1. The Stateful Bug Tracking Concept

In monolithic systems, when a task fails, the execution collapses, losing all cached progress. In our collaborative subagent system, we treat failures as **asynchronous, trackable events** modeled after standard enterprise bug-tracking lifecycles (such as JIRA or Buganizer).

### The Escalation & Resume Loop

```
[ Chaos Tester (QA) ] ──> [ FAILED ] ──> Writes bug_UUID.json (NEW) to Local Lab Directory
                                                 │
                                                 ▼ (Lightweight Pointer Message to Orchestrator)
                                      [ ORCHESTRATOR WAKES UP ]
                                      - Receives pointer: bug_id="BUG_801"
                                      - Reads labs/dev/[lab]/bugs/bug_801.json dynamically
                                                 │
                                                 ▼
                                      [ Orchestrator (Architect) ]
                                                 │
                                                 ├─> (Auto-Heals) ─> Patches HCL/Code ─> Mark RESOLVED
                                                 │
                                                 └─> (Fails) ──────> Pause & Prompt Human (BLOCKED)
                                                                                │
                                                                                ▼ (Human Patches)
                                                                          Mark RESOLVED
                                                                                │
                                                                                ▼
                                      [ Re-engage Subagent ]
                                - Ingests RESOLVED bug_pointer
                                - Reads progress.json (Cache-Hit)
                                - Resumes exactly at failed step!
```

---

## 2. Directory Layout on the Blackboard & Workspace

To prevent global memory bloating, all detailed diagnostic logs (stdderr outputs, VM states) are **strictly isolated within the local lab folder**. The global Blackboard only holds tiny active pointers.

### 2.1 Local Lab Directory (Detailed Logs - Git Tracked)
```
labs/dev/[lab-name]/
├── [lab-name].lab.md
├── blueprint.md
├── OWNERS
└── bugs/                            # Isolated, local bug directory for this lab
    ├── bug_BUG801.json              # Detailed stack trace & failed command log
    └── bug_BUG802.json
```

### 2.2 Shared Blackboard State (Pointers Only)
```
<appDataDir>/brain/<conversation-id>/workspace_state/
└── active_bug_pointers.json         # List of lightweight active pointers
```

---

## 3. The Lightweight Pointer Message Schema

When a subagent fails, the **ONLY** data it transmits to the Orchestrator's mailbox (or parent chat window) is a lightweight JSON pointer envelope:

```json
{
  "status": "FAILED",
  "bug_id": "BUG_801",
  "bug_pointer": "labs/dev/gclb-multi-region-iap/bugs/bug_BUG801.json"
}
```

### 3.1 Detailed Local Bug Schema (`bug_BUG801.json`)
The actual detailed diagnostic payload remains safely locked inside the local file, read dynamically by the Orchestrator *only* when performing audits:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "bug_id": { "type": "string", "description": "Unique identifier, e.g. BUG_801" },
    "timestamp": { "type": "string", "format": "date-time" },
    "subagent_id": { "type": "string", "description": "The conversation ID of the failing subagent" },
    "step_number": { "type": "integer" },
    "step_title": { "type": "string" },
    "error_logs": {
      "type": "object",
      "properties": {
        "failed_command": { "type": "string" },
        "stderr_output": { "type": "string" }
      },
      "required": ["failed_command", "stderr_output"]
    },
    "status": { "type": "string", "enum": ["NEW", "INVESTIGATING", "BLOCKED_HUMAN_REQUIRED", "RESOLVED"] },
    "resolution": {
      "type": "object",
      "properties": {
        "root_cause": { "type": "string" },
        "fix_applied": { "type": "string" },
        "files_modified": { "type": "array", "items": { "type": "string" } }
      }
    }
  },
  "required": ["bug_id", "timestamp", "subagent_id", "step_number", "step_title", "error_logs", "status"]
}
```

---

## 4. Technical ROI of the Pointer Isolation Model

1.  **Total Memory Protection (Context Shielding)**: Preventing massive, multi-kilobyte GCE and CLI stack traces from leaking into the parent conversation thread preserves the Orchestrator's attention span, avoiding "Lost in the Middle" prompt drift.
2.  **Clean Git Paper Trail**: Because the detailed bug logs reside in the `/bugs/` directory inside `labs/dev/[lab-name]/`, they are naturally committed to Git. This creates a perfect historical record of your codebase's validation failures and automated self-healing fixes.
3.  **Zero Overhead Human Interactivity**: If a human engineer needs to step in to unblock a `BLOCKED_HUMAN_REQUIRED` state, they open the local `bug_BUG801.json` file in their IDE, toggle the status, and proceed cleanly.
