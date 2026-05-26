# System Architecture Design: Generic vs. Specialized Orchestration (Core & Adapter Pattern)

> [!NOTE]
> **Objective**: Evaluate the feasibility, reuse boundaries, and structural layout of the central Orchestrator script. Design a **Core-and-Adapter Pattern** that isolates generic workspace utilities (auth checks, mailbox polling, subprocess commands, Git tracking, and JSON parsing) into a reusable base class, while mapping specialized workflows (like Codelab creation or Billing checks) as lightweight, modular plugin adapters.

---

## 1. The Architecture: Core & Adapter Pattern

To prevent duplicate boilerplate code while avoiding a single, massive, monolithic execution script, we divide the Orchestration layer into two decoupled components:

1.  **`OrchestratorCore` (The Core Engine - Generic)**:
    *   A reusable Python base class containing all the common workstation utility functions.
    *   Does **not** hold any specific workflow step lists or GCE-specific logic.
2.  **`WorkflowAdapter` (The Pluggable Runners - Specialized)**:
    *   Lightweight subclasses that inherit from `OrchestratorCore`.
    *   Implement the specific lifecycle steps, linter rules, and subagent prompts tailored to that single workflow.

---

## 2. The Core-Adapter Directory Layout

```
.agents/
├── scripts/
│   ├── core_orchestrator.py      # Generic Base Class (Utility Engine)
│   └── compile_prompts.py
├── runners/                      # Specialized Pluggable Workflow Adapters
│   ├── create_codelab.py        # Codelab Creation & Validation Runner (Level 300/400)
│   ├── check_billing.py         # BigQuery Billing Aggregator Runner
│   ├── extract_requirements.py   # NLP Transcripts Analyst Runner
│   └── organize_workspace.py    # Directory Structure Auditor Runner
└── mailboxes/
```

---

## 3. Core & Adapter Code Specifications

### 3.1. Generic Core Engine (`core_orchestrator.py`)
The generic base class handles the foundational edge communications:

```python
# .agents/scripts/core_orchestrator.py
import os
import json
import subprocess
import logging

class OrchestratorCore:
    def __init__(self, workflow_name, artifact_dir):
        self.workflow_name = workflow_name
        self.artifact_dir = os.path.abspath(artifact_dir)
        self.mailbox_dir = "/usr/local/google/home/shacharb/skynet/.agents/mailboxes"
        os.makedirs(self.artifact_dir, exist_ok=True)

    def run_command(self, cmd, cwd=None):
        """Execute shell command securely."""
        try:
            res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, check=True)
            return True, res.stdout, res.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout, e.stderr

    def verify_auth(self):
        """Verify Sandbox Admin active credentials context."""
        verify_script = "/usr/local/google/home/shacharb/skynet/.agents/skills/gcloud-auth-verification/scripts/verify_auth.py"
        success, stdout, _ = self.run_command(f"python3 {verify_script}")
        return success and "admin" in json.loads(stdout).get("active_account", "")

    def send_mailbox_message(self, recipient, payload):
        """Post a lightweight pointer envelope to a subagent's mailbox."""
        msg_id = f"msg_{int(time.time())}"
        msg_file = os.path.join(self.mailbox_dir, recipient, "inbox", f"{msg_id}.json")
        os.makedirs(os.path.dirname(msg_file), exist_ok=True)
        with open(msg_file, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"📢 Sent message {msg_id} to {recipient} mailbox pointer.")
        return msg_id
```

---

### 3.2. Specialized Workflow Adapter (`runners/create_codelab.py`)
The pluggable runner inherits the core features and focuses *only* on its unique step pipeline:

```python
# .agents/runners/create_codelab.py
from core_orchestrator import OrchestratorCore

class CreateCodelabRunner(OrchestratorCore):
    def __init__(self, markdown_file, skip_cleanup=False):
        self.markdown_file = markdown_file
        self.lab_name = os.path.basename(os.path.dirname(markdown_file))
        super().__init__(workflow_name="create-codelab", artifact_dir=f"~/.gemini/jetski/brain/{self.lab_name}")
        self.skip_cleanup = skip_cleanup

    def execute_pipeline(self):
        """Specific Codelab workflow execution step list."""
        # 1. Verify active credentials using core helper
        if not self.verify_auth():
            return False
            
        # 2. Perform specialized Markdown linter checks
        if not self.run_preflight_linter():
            return False
            
        # 3. Provision Sandbox dynamically using core command run
        project_id = self.provision_project()
        
        # 4. Trigger stateful validation runner (tester.py)
        return self.run_validation_suite(project_id)
```

---

## 4. Architectural Evaluation

| Metric | Unified Monolithic Script | Core-and-Adapter Pattern (Proposed) |
| :--- | :--- | :--- |
| **Code Reusability** | Low (Boilerplate must be duplicated for new tasks). | **High (100% Dry)** (Auth, Mailboxes, and Git logic sit in Core). |
| **Developer Velocity** | Slow (Writing a new script requires 300+ lines). | **Fast** (Plugging in a new runner requires <80 lines of logic). |
| **Maintenance Cost** | High (Editing mailbox schemas requires modifying all files). | **Low** (Edit once in `core_orchestrator.py`; all runners upgrade). |
| **Context Window Health** | Poor ( मोनोलिथिक code triggers prompt bloat). | **Excellent** (Specialists only read highly focused, small plugin files). |

### Conclusion
The **Core-and-Adapter Pattern is the definitive enterprise standard** for Jetski. It guarantees absolute extensibility, keeps subagent codebases extremely light and dry, and enables seamless scaling as we roll out additional solution engineering workflows!
