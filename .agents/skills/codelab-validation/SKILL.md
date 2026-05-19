---
name: codelab-validation
description: >
  Validates natural-language codelabs by interpreting tutorial steps,
  executing them, and handling prerequisite gates for long-running
  operations. Use when the user asks to validate, test, or check a
  codelab, or to resume a previously started validation.
---

# Codelab Validation

You validate codelabs written in natural language using a stateful, step-by-step workflow.

## Entry Point: Read State First

Every invocation starts by checking `.tester_state/progress.json`.

### No state exists → Parse the codelab

1. Read the codelab source file.
2. Think like a Software Engineer. Break it into ordered steps. For each step, determine:
   - **title**: Short name.
   - **instructions**: A single string describing the action to take.
     **CRITICAL**: Maintain idempotency. If a step implies multiple actions,
     **split it into multiple steps**.
     Examples:
     - **Explicit**: "Run `boq agent create`" (Split "Create file and run command" into two steps).
     - **Implicit**: "A CL needs to be created" (e.g., if there is a code change).
   - **prerequisite**: Does this step require a prior condition to be met?
     Check for **both explicit and implicit** gates:
     - **Explicit**: Phrases like:
       - "After the deployment finishes…"
       - "Wait for the build to complete, then…"
       - "You should now see the service URL…"
     - **Implicit**:
       - **Pre-existing State**: Does it assume resources or data are already
         present? (e.g., a GCS bucket exists, a CL in a previous step is
         submitted, specific data is loaded).
       - **Environment Configuration**: Does it imply specific settings or
         permissions? (e.g., IAM roles, APIs enabled, quotas).
     If found, record:
     - `prerequisites`: A list of strings describing conditions that must be met.
   - If no prerequisites, set `prerequisites` to [].

3. **Identify User Inputs**:
   - Scan for variables that require user values (e.g., `PROJECT_ID`, `REGION`, `ZONE`).

4. **INTERACTIVE CONFIRMATION (CRITICAL)**:
   - Present the parsed plan to the user.
   - List all steps, identified prerequisites (explicit & implicit), and required user inputs.
   - **Ask the user to confirm the plan and provide necessary values.**
   - **DO NOT proceed until the user confirms.** If they want to modify steps or prerequisites, adjust the plan accordingly.

5. Write state files. (Only after confirmation). See `references/state_schema.md`.
   - Write `.tester_state/progress.json` and `.tester_state/step-NNN.json` files.
   - Save all user-provided values for identified variables into `.tester_state/user_inputs.json`.

### State exists → Resume

1. Read `current_step` from `.tester_state/progress.json` and the corresponding `.tester_state/step-NN.json` file.
2. Read `.tester_state/user_inputs.json` to retrieve previously provided values. Use these values automatically instead of asking the user again.

**`pending`** (no prerequisite, or prerequisite is null):
→ Execute the step. Set status to `done`.
  - Set `execution_summary` to key outcome (e.g. "Resource X created").
  - Advance.

**`pending`** (has prerequisites):
→ Verify that all prerequisites are met.
→ If met: execute the step. Set `done`.
  - Set `execution_summary` to key outcome.
  - Advance.
→ **Blocked State Strategy**:
  1. Determine if the environment supports persistence (Check if
     `~/.gemini/smith/` exists).
  2. If yes: You **MUST** immediately invoke the **smith-monitoring** skill to
     register a persistent monitor for this blocker. Set status to `blocked`.
  3. If no (Standard JetSki):
    → **Check if human intervention is required** (e.g., "Submit the CL"):
      - If yes: Notify the user, set status to `blocked`.
        - **Provide ALL related links** (e.g., CL link, console URL).
        - Set `blocked_reason` to "waiting for user".
        - Set `execution_summary` to specific request (e.g., "Waiting for CL 123456 submission").
        - Wait.
    → Else: set status to `blocked`.
        - Set `blocked_reason` to "prerequisite not met".
        - Set `execution_summary` to failure detail (e.g., "Cluster not ready: some error detail").
        - Record `last_check` timestamp.

**`blocked`**:
→ Verify prerequisites again.
→ Met: execute the step. Set `done`.
  - Set `execution_summary` to key outcome.
  - Advance.
→ Not met: increment `check_attempts`. Stay `blocked`.
→ 3+ consecutive failures: set `failed`.
  - Set `execution_summary` to "Repeated prerequisite failure".

**`done`**:
→ Advance to next step.

**`failed`**:
→ Stop. Report the failure using the **Error Handling & Bug Reporting** procedure.

**All steps `done`**:
→ Set progress status to `completed`.

### 📋 Live Visual Task Board Tracking (Mandatory)

To provide the user with real-time visual status feedback directly in their IDE preview tab, System B **MUST** dynamically generate and update the unindented HTML `task.md` tracking sheet at the start of the run, and immediately after **every single step state transition**:

1.  **File Placement**: Save the file as `task.md` directly inside the conversation directory: `<appDataDir>/brain/<conversation-id>/task.md`.
2.  **Syntax Rules**: You MUST strictly adhere to the zero-indentation syntax standard. Every single line of the generated HTML template must be written completely flush left (0 spaces of leading whitespace) to avoid parser corruption.
3.  **Color Mapping**: Map state properties to the standardized inline-CSS colors:
    - `pending` (waiting): **PENDING** background `#f1f3f4`, text `#5f6368`.
    - `pending` (active): **RUNNING** background `#e8f0fe`, text `#1a73e8`.
    - `blocked` (waiting/blocked): **BLOCKED** background `#ffebee`, text `#c53929`.
    - `done`: **DONE** background `#e6f4ea`, text `#137333`.
    - `failed`: **FAILED** background `#fce8e6`, text `#c53929`.
4.  **Error Outputs**: If a step has `error` or `blocked_reason` content, render it beautifully inside a monospace `<pre style="font-family: ui-monospace, monospace; font-size: 11px; background: #f1f3f4; padding: 8px 12px; border-radius: 6px; color: #202124; margin: 8px 0 0 0; white-space: pre-wrap; word-break: break-all;">` container directly under the details inside the Details column.

### Generating a Report

When asked, or when validation completes, or when report error in bug:

-   Read all state files.
-   Produce `report/validation-report.md`:
    -   Summary table: step | title | status | execution_summary | blocked
        duration.
    -   Overall verdict: COMPLETED or FAILED.
    -   For failed/blocked steps: details and last output.
    -   Codelab Improvements: Suggestions to make the codelab more robust.

### 🚨 Error Classification & Handling Protocol

When a terminal command fails during validation execution, you **MUST** immediately classify the failure category to execute the correct remediation path:

#### 1. Category A: API & Command Syntax Errors
*   **Indicators**: `gcloud` error codes representing invalid flags, unknown commands, missing arguments, YAML syntax mismatches, or `command not found`.
*   **Protocol (Immediate Self-Healing)**: **DO NOT RETRY.** Retrying a syntax error is useless. You MUST immediately:
    1. Pause command execution.
    2. Search documentation natively (`search_documents` or `search_web`) to retrieve the exact working command syntax and flag parameters.
    3. Directly edit and fix the command block inside the `.lab.md` file in your workspace.
    4. Return the complete, fixed file in the `fixed_content` schema field.
    5. Immediately resume/re-execute the step with the corrected command.

#### 2. Category B: Transient Infrastructure & Propagation Blocks
*   **Indicators**: Active API enablement delays (e.g., *"API Compute is being enabled..."*), `503 Service Unavailable`, network creation timeouts, or resource state conflicts (e.g., Spanner/MIG resource exists but is not yet active).
*   **Protocol (Stateful Polling & Retry)**: You MUST execute state-based polling up to **3 times**:
    1. Update the step status to `blocked`.
    2. Set `blocked_reason` to "waiting for resource propagation".
    3. Wait for 60 seconds.
    4. Re-verify/re-execute the command.
    5. If the blocker persists after 3 consecutive attempts, set the status to `failed`, stop execution, and file a bug in the issues tracker as defined in the Bug Reporting section.

- If the failure persists or is unrecoverable, **stop execution**, file a bug using the
  **Issues Tracker or Logging System**
  (e.g., log the error to a local file, or use an available issue tracker. Google-internal users can use `/google/bin/releases/issues-cli/issues create --title "[Codelab Failure] <Title>" --description "<Details>" --component_id 2022529`),
  and **notify the user with the bug link**.
  - **Bug Details**: Refer to [bug_report_template.md](references/bug_report_template.md) for the required structure and details.

## Rules

1.  **State is truth.** Read state before acting. Never assume.
2.  **Be idempotent.** `done` → skip. `blocked` → re-check. Calling the agent
    twice on the same state = same outcome.
3.  **One step at a time.** Finish or park the current step first.
4.  **Show your reasoning** when you identify prerequisite gates. Your
    interpretation of natural language may be wrong.
5.  **Capture output.** Record command outputs and timestamps.
6.  **Ask when unsure.** In headless mode, set `failed` with a clarification
    message in the error field.
7.  **Provide links for user interaction.** If a step requires the user to take
    an action elsewhere, ALWAYS output the relevant link.
8.  **Prefer CLI over Browser.** Always use CLI tools (e.g., `issues`, `blaze`) to perform actions or gather information.
9.  **Verify CLI prerequisites.** Before executing a command using a CLI tool, check if the CLI is installed.
