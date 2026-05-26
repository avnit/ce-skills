# System Architecture Design: Stateful Bug Tracking & Asynchronous Re-engagement Loop

> [!NOTE]
> **Objective**: Design a structured, event-driven **Stateful Bug Tracking System** that models the QA-to-Architect escalation lifecycle. Enable subagents to file structured bug files on the Blackboard, allow the Orchestrator (or a human engineer) to apply in-place fixes, and cleanly trigger subagent re-engagement to resume from the exact failure point without losing state.

---

## 1. The Stateful Bug Tracking Concept

In monolithic systems, when a task fails, the execution collapses, losing all cached progress. In our collaborative subagent system, we treat failures as **asynchronous, trackable events** modeled after standard enterprise bug-tracking lifecycles (such as JIRA or Buganizer).

### The Escalation & Resume Loop

```
[ Chaos Tester (QA) ] ──> [ FAILED ] ──> Writes bug_UUID.json (NEW) to Blackboard
                                                 │
                                                 ▼ (Orchestrator Wakes Up)
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
                                - Ingests RESOLVED bug_UUID.json
                                - Reads progress.json (Cache-Hit)
                                - Resumes exactly at failed step!
```

---

## 2. Directory Layout on the Blackboard

We introduce a structured `/bugs/` folder directly inside our workspace state engine:

```
<appDataDir>/brain/<conversation-id>/workspace_state/
├── intake_specs.json
├── blueprint.json
├── validation_state.json
└── bugs/
    ├── bug_BUG801_GCLB_PROV.json        # Active, structured bug log
    └── bug_BUG802_IAP_SSH.json
```

---

## 3. Standardized JSON Bug Schema

All failures must be documented using a highly strict JSON schema to prevent loose text descriptions:

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

## 4. The Human-in-the-Loop "Blocked" Escape Hatch

A massive advantage of this design is that it provides the **ultimate clean gateway for human intervention** when automated self-healing fails:

1.  **Automated Ingest**: If `chaos-tester` fails at Step 7 (VPC Ingress), it writes the bug file to GCS/Blackboard.
2.  **Orchestrator Attempt**: The Orchestrator reads the bug, tries to solve the issue, but fails (e.g. it hits a strict organizational policy block that cannot be bypassed via script).
3.  **Transition to Blocked**: The Orchestrator writes `status: "BLOCKED_HUMAN_REQUIRED"` to the bug file, outputs the exact stack trace to the chat, and **halts execution**.
4.  **Human Action**: The user (you) reads the chat, executes a manual fix (e.g., toggling a policy in the console or typing a password), and writes `status: "RESOLVED"` inside `bug_UUID.json`.
5.  **Re-engagement**: You type "resume" or "go" in the chat. The Orchestrator immediately boots the subagent, which reads the resolved status, matches it against its cached `.tester_state/progress.json` files, skips the successful Steps 1–6, and **resumes E2E validation directly at Step 7!**

---

## 5. Feasibility and Evaluation

| Metric | Traditional Crash & Restart | Stateful Bug Tracking & Re-engage |
| :--- | :--- | :--- |
| **State Retention** | Poor (wastes time/quota recreating resources). | **100% Cached** (Resumes from last successful step). |
| **Human-in-the-Loop UX** | Messy (User must manual-patch and guess where to restart). | **Elegant** (Strict JSON status transitions and auto-resume). |
| **Trace Logging** | Weak (No central structured error logs). | **Excellent** (Complete database of `/bugs/` files saved in Git). |
| **Self-Healing Loop Efficacy**| Low (Generator gets lost in massive chat logs). | **High** (Specific and clean JSON stack trace). |
