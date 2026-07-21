---
name: codelab-validation
description: >
  Validates natural-language codelabs statefully using the tester.py engine.
  Use when validating, testing, or checking a codelab or test plan, or resuming
  a validation run.
---

# Codelab Validation

This skill provides instructions for statefully validating Google Cloud codelabs using the unified `tester.py` validation engine.

## Unified Execution Engine

Execute all E2E codelab and test plan validations via the `tester.py` script. The engine parses command blocks, manages step-by-step state transitions, caches executed command hashes (`<lab>.md.state`), persists environment variables (`<lab>.md.env`), and generates HTML status boards (`test_status.md`).

### CLI Invocation

```bash
python3 .agents/skills/codelab-validation/scripts/tester.py \
    path/to/your/codelab.md \
    --project-id "<PROJECT_ID>" \
    --phase test \
    --artifact-dir <appDataDir>/brain/<conversation-id>
```

#### Flags

- `--project-id <PROJECT_ID>` _(Required)_: Target GCP project. Exports `PROJECT_ID` and `CLOUDSDK_CORE_PROJECT` into the subshell environment session. Use `--allow-active-project` only as an explicit escape hatch to consciously adopt ambient workstation config.
- `--phase {test|cleanup|all}` _(Default: `test`)_: Execution phase scope. (`--skip-cleanup` is a deprecated alias for `--phase test`).
- `--artifact-dir <DIR>` _(Optional)_: Conversation context directory for HTML preview status boards.
- `--timeout <SECONDS>` _(Default: 600)_: Step execution timeout in seconds.
- `--fresh` _(Optional)_: Purges `.tester_state/`, `<lab>.md.state`, and `<lab>.md.env` for this lab only before execution.

### Command Execution Tiers

`tester.py` decomposes command blocks into logical-line execution units using three tiers:

1. **`flat`**: Independent commands executed sequentially. Each unit is individually hash-checked, executed with per-unit timeout, cached, and environment-persisted upon success.
2. **`compound_pure`**: Shell construct blocks (loops, `if` statements, functions). Wrapped in `( set -eo pipefail ... )` and executed atomically.
3. **`compound_stateful`**: Compound blocks (control flow/heredocs) that also mutate shell state (e.g. `cd`, `export`). Executed as a raw block in the main subshell. _Warning_: Intermediate command failures within compound stateful blocks cannot be individually isolated.

## State Model & Resumption

State files are managed automatically under `.tester_state/` in the lab directory:

- `.tester_state/progress.json`: Tracks overall progress (`codelab`, `total_steps`, `current_step`, `status`).
- `.tester_state/step-NNN.json`: Step details (`num`, `title`, `status`, `instructions`, `prerequisites`, `commands`, `output`, `error`, `has_gui`, `is_cleanup`).
- `.tester_state/user_inputs.json`: Baseline variables mapped during run initialization.
- `variables.json`: Custom key-value replacements passed to `tester.py`.
- `overlay.json`: Per-lab transformation rules. See [overlay_schema.md](references/overlay_schema.md).

### Step Statuses

All step statuses are uppercase:

- `PENDING`: Waiting for execution.
- `RUNNING`: Currently executing in subshell.
- `DONE`: Executed successfully (or skipped via hash cache).
- `FAILED`: Command exited non-zero or timed out.
- `SKIPPED/NO-OP`: Step contains no executable commands.
- `DEFERRED`: Step skipped during current phase (e.g. cleanup step during `--phase test`).

### Resumption Protocol

Re-running `tester.py` automatically resumes from saved state. Completed step hashes stored in `<lab>.md.state` are skipped, and variables from `<lab>.md.env` are re-sourced into the subshell.

## Agent Role & Protocol

The agent acts as orchestrator around `tester.py`:

1. **Pre-flight Configuration**: Provision a dedicated sandbox project (`create_project.py`), populate `variables.json` for custom placeholders, and pass `--project-id`.
2. **Execution**: Launch `tester.py`. For steps marked `has_gui` or requiring manual external actions, perform the required action and re-run `tester.py` to resume.
3. **Result Interpretation**: Check `tester.py` exit code and read generated `.tester_state/` output files.

### Error Classification & Remediation Protocol

When `tester.py` returns `FAILED`:

#### 1. Category A: Command Syntax & API Errors

- **Indicators**: `gcloud` unknown flag, invalid syntax, missing argument, or YAML parse error.
- **Remediation**: Investigate root cause before retrying. Search developer documentation (the `google-developer-knowledge` MCP server or `search_web`), edit the command block in `.lab.md` or apply a per-lab transform via `overlay.json` (see [overlay_schema.md](references/overlay_schema.md)), and re-run `tester.py`.

#### 2. Category B: Transient Infrastructure Delays

- **Indicators**: API enablement propagation, network creation delays, `503 Service Unavailable`.
- **Remediation**: Wait 60 seconds and re-run `tester.py` (up to 3 attempts).

#### 3. Unrecoverable Failures & Bug Reporting

If remediation fails after 3 attempts:

1. `tester.py` automatically files a bug JSON in `<lab_dir>/bugs/bug_*.json` and central `~/.gemini/jetski/bugs/`.
2. File a tracking issue using the issues CLI (e.g. `${ISSUES:-/google/bin/releases/issues-cli/issues}` create --title "[Codelab Failure] <Title>" --description "<Details>" --component_id 2022529). _Note_: If the issues CLI binary is unavailable (non-Google environment), reference the automatically generated `<lab_dir>/bugs/bug_*.json` file directly.
3. Report the failure and bug details to the user.

## Status Tracking & Reporting

- **Status Board**: `tester.py` generates `test_status.md` using `html_reporter.py`.
- **Task Tracking**: Master `task.md` tracking follows [.agents/rules/tasks.md](.agents/rules/tasks.md).
- **Validation Report**: Summary reports are compiled into `report/validation-report.md`.
