---
name: lab-video-automation
description: Automates the step-by-step interactive execution of Google Cloud Codelabs inside whichever active Chrome profile session window is operated by the user over page-level CDP pipes, designed for pairing with screen recorders.
---

# Skill: Lab Video Automation Agent

The **Lab Video Automation Agent Skill** automates the execution lifecycle of Google Cloud Codelabs by attaching directly to whichever specific **Google Chrome profile session window** is currently opened and operated by the user over page-level **Chromium DevTools Protocol (CDP)** debugging transport streams.

It drives terminal injection, enforces keystroke pacing, manages stateful checkpointing (.state tracking), updates real-time markdown UI progress dashboards (`test_status.md`), and verifies buffer synchronization while you capture the visual output externally using standard screen recording software (e.g., QuickTime Player, OBS Studio, Loom). Attaching via page-level CDP completely decouples automation lifecycles from host profile directories, allowing seamless switching across multiple active researcher identities.

---

## ⚠️ Mandatory Prerequisites

Before running the automation engine, ensure the following strict conditions are met:

1. **Pre-Provisioned GCP Project**: You must have an active Google Cloud project available with necessary APIs enabled and billing configured.
2. **Launch Chrome Profile with Debugging Enabled**: You must launch your target local Google Chrome profile session from your terminal specifying an open CDP debugging port:
   ```bash
   # On macOS:
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
   ```
   > **Multi-Profile Guidance**: If you wish to isolate a specific secondary Chrome user data profile, append `--user-data-dir=/path/to/profile` to the terminal start command.
3. **Active Authentication**: Once your chosen profile window opens, navigate to the Google Cloud Console and log in using your authorized project credentials. Keep the dashboard tab visible.

---

## 🏗️ Phase 1: High-Level System Architecture

The script connects to your active multi-profile debugging server over `localhost:9222/json/list`, identifies the running console tab dynamically, attaches isolated control streams via Playwright, compiles structured JSON execution runbooks, and injects lab instructions cleanly in real time.

```
 [Markdown Input] ──> [1. Parsing Engine] ──> [2. Execution Runbook (JSON)]
                                                         │
                                                         ▼
 [External Screen Recorder] <── [3. Playwright Page-Level CDP Controller]
                                 (Stateful Checkpointing & UI Tracking)
```

### The 4 Pillars of the Architecture

1. **The Parsing Engine:** Scans raw markdown files, strips explanatory prose, extracts command sets, computes SHA-256 block hashes, applies negative filters, and compiles highly structured JSON execution plans.
2. **The Page-Level CDP Controller (Playwright):** Dynamically fetches isolated target descriptor paths (`webSocketDebuggerUrl`) via HTTP queries to attach directly to specific user document scopes securely bypassing root-level context constraints.
3. **Stateful Checkpointing & Skipping:** Maintains perfect alignment with `deterministic_runner.py` tracking persistence. Successfully executed block hashes are saved to `<lab_basename>.state`, allowing resume flows to bypass already-completed operations automatically.
4. **The Terminal Guardrail:** Observes terminal text buffers for input prompt stabilization indicators (`$`, `>`), actively monitors runtime execution deltas for critical error signatures, and intercepts unexpected interactive terminal confirmation requests.

---

## 🗺️ Phase 2: Google Cloud Console DOM Topography

Because this skill focuses exclusively on orchestrating actions inside the Google Cloud Console, understanding the visual layout hierarchy and nested elements of the website is critical for stable automation traversal.

### Structural Layout Tree

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Google Cloud Console Main Viewport (console.cloud.google.com)               │
│                                                                             │
│  ├── Top Navigation Bar (Search, Project Selector, Cloud Shell Trigger)     │
│  └── Main Body Content Area                                                 │
│       │                                                                     │
│       └── Embedded Cloud Shell Container Pane (?cloudshell=true)            │
│            │                                                                │
│            └── Host Frame Wrapper                                           │
│                 │                                                           │
│                 └── iframe [src*="cloudshell"]                              │
│                      │                                                      │
│                      └── Content Document (xterm.js Terminal Engine)        │
│                           │                                                 │
│                           ├── Terminal Canvas Grid (.xterm-rows)            │
│                           └── Fallback Wrapper (gcp-shell-fallback-terminal)│
└─────────────────────────────────────────────────────────────────────────────┘
```

### Selectors & Traversal Map

1. **Base Landing Activation**: Navigating to `https://console.cloud.google.com/?cloudshell=true` guarantees the host website expands the bottom terminal layout container.
2. **Iframe Resolution**: The standalone shell terminal renders inside an isolated internal subdocument. The traversal engine targets:
   ```css
   iframe[src*="cloudshell"]
   ```
3. **Terminal Character Row Spans**: Characters render structurally within specific container matrix definitions:
   ```css
   .xterm-rows, gcp-shell-fallback-terminal
   ```
4. **Prompt Buffer Indicators**: Custom polling monitors input cursor lines ending with active primary (`$`) or secondary (`>`) terminal shell indicators.

---

## 💻 Phase 3: Environment Setup & Dependencies

The runtime environment relies entirely on standard Python packages supported natively on macOS workstations.

### Core Prerequisites

| Dependency | Purpose | Key Configuration |
| :--- | :--- | :--- |
| **Python 3.11+** | Execution engine runtime | Asynchronous processing via `asyncio` |
| **Playwright** | CDP attachment & terminal controller | Attaches over DevTools protocol streams |
| **Pydantic v2** | Strict schema verification | Validation of automation runbook instruction units |

### Setup Instructions

Initialize the dependencies inside your active Python environment:
```bash
pip install -r _agents/skills/lab-video-automation/resources/requirements.txt
playwright install chromium
```

---

## ⚙️ Phase 4: The Parsing Engine & JSON Runbook Design

Codelabs contain multiple text snippets. Executing sample terminal output examples as live shell commands breaks execution flows. The refactored engine isolates these logic steps cleanly.

### Extraction Protocol
1. Fenced code blocks encapsulated by ````bash` or ````console` are extracted.
2. A **Negative Filter** checks sequences against sample output strings (e.g., `Credentialed accounts:`, `Status: ACTIVE`, `Output:`). Matching blocks are automatically discarded.
3. Approved blocks are assigned a hermetic SHA-256 block hash aligning perfectly with core codelab test runners.
4. Individual commands inside the block are parsed (concatenating trailing backslashes `\`, normalizing space tokens).
5. The compiled map is serialized to disk as a standardized JSON runbook (`<lab_basename>.runbook.json`).

### Sample JSON Runbook Structure
```json
{
  "source_lab": "/path/to/lab.md",
  "target_project": "target-project-id",
  "compiled_timestamp": "2026-05-12T14:20:00.000000",
  "total_steps": 2,
  "execution_plan": [
    {
      "index": 1,
      "block_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "commands": ["gcloud config set project target-project-id"],
      "raw_block": "```bash\ngcloud config set project target-project-id\n```",
      "is_project_init": true
    }
  ]
}
```

---

## 🚀 Phase 5: Playwright Automation & Terminal Interaction

Standard web fill functions fail on xterm canvases. The script anchors active cursor focus via pointer clicks and injects keystroke streams sequentially:
```python
# Ensure the terminal canvas layer is focused
await terminal.click(force=True)

# Stream string arrays using humanized typing pacing delays
await page.keyboard.type(command_string, delay=50)
await page.keyboard.press("Enter")
```

---

## ⏱️ Phase 6: Guardrail Engine, Checkpoints, & Status Tracking

### 1. Stateful Checkpoint Resumption (.state tracking)
To eliminate the need to start codelabs from scratch upon encountering intermittent transient infrastructure lags, the engine tracks block completion state via `<lab_basename>.state`. If an operation fails midway, restarting the identical execution command bypasses already executed SHA-256 block hashes automatically.

### 2. Real-Time UI Dashboards (`test_status.md`)
As commands inject, the engine dynamically updates a local markdown UI status tracker inside the lab source directory. External observers or automated test tools can open `test_status.md` to see visual checklist status indicators (`[x]` completed, `[/]` in-progress, `[!]` failed).

### 3. Heuristic Exceptions & Prompt Monitoring
- **Pristine Delta Slicing**: Isolates terminal output appended immediately after pressing Enter. Scans the precise delta string for custom CLI exceptions (`ERROR:`, `Permission denied`, `invalid argument`), raising clean runtime breaks immediately.
- **Interactive Deadlock Prevention**: Proactively intercepts terminal outputs matching stalled confirmation prompts (e.g., `[Y/n]`, `Enter passphrase:`), automatically streaming appropriate affirmative overrides (`y`) to prevent stalled video recordings.
- **Visual Typing Pacing**: Applies customizable simulated typing character delays (`delay=50`) and visual post-command padding blocks (`post_command_padding_ms=2000`) ensuring screen recordings remain perfectly legible to target users.

---

## 🚨 Phase 7: Resiliency Protocols

- **Human-in-the-Loop (HITL) Gateways**: If an instruction fails and self-healing recovery is unavailing, the script avoids terminating background browser handles. Instead, it presents a threaded intervention prompt (`asyncio.to_thread`) allowing you to manually fix the state in the browser window and choose to **[r]etry**, **[s]kip**, or **[a]bort** the runbook. Toggled via `--no-hitl`.
- **Step Timeout Safety Valves**: Wraps command injections inside localized timeout threshold boundaries. If an infrastructure process hangs beyond limits (default 5 minutes), execution stops safely.
- **Transport Stabilization Loops**: Yields non-blocking check intervals to ensure connected CDP socket endpoints map page metadata correctly before parsing DOM branches.
- **Forced Clean Starts**: Pass `--force-reset` to automatically purge historical `.state` checkpoint cache files and trigger recording streams from Step 1.

---

## 📖 Operational Runbook

### 1. Pre-Compilation Dry-Run Audit
Compile the decoupled JSON instruction runbook and verify generated block hashes without connecting Playwright automation streams:
```bash
python3 _agents/skills/lab-video-automation/scripts/execute_lab.py \
    --lab labs/dev/multi-vpc-dns-forwarding/multi-vpc-dns-forwarding.lab.md \
    --project multi-vpc-dns-1778612130 \
    --dry-run
```

### 2. Executing the Multi-Profile Live Automation Engine
Attach Playwright to your active local Google Chrome window debugging endpoint to drive screen recording automation sequences:
```bash
python3 _agents/skills/lab-video-automation/scripts/execute_lab.py \
    --lab labs/dev/multi-vpc-dns-forwarding/multi-vpc-dns-forwarding.lab.md \
    --project multi-vpc-dns-1778612130 \
    --use-cdp \
    --cdp-url http://localhost:9222
```

### 3. Forcing Full Codelab Resets
Ignore previously cached state logs to execute the video automation cycle cleanly from the beginning:
```bash
python3 _agents/skills/lab-video-automation/scripts/execute_lab.py \
    --lab labs/dev/multi-vpc-dns-forwarding/multi-vpc-dns-forwarding.lab.md \
    --project multi-vpc-dns-1778612130 \
    --use-cdp \
    --force-reset
```
