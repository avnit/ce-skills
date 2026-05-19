---
name: codelab-testing
description: How to test codelabs using deterministic execution and LLM debugging.
---

# Skill: Codelab Testing

This skill provides instructions for testing codelabs to ensure all commands work as expected.

## Setup for Testing

Before running tests, you must provision a new Google Cloud project and disable restrictive organization policies. Follow the instructions in the [GCP Provisioning Skill](file:///.agents/skills/gcp-provisioning/SKILL.md).

1.  Create a new project:
    ```bash
    python3 .agents/skills/gcp-provisioning/scripts/create_project.py <lab_name>
    ```
2.  Disable org policies:
    ```bash
    bash .agents/skills/gcp-provisioning/scripts/disable_org_policies.sh PROJECT_ID
    ```
3.  Set the active project in `gcloud`:
    ```bash
    gcloud config set project PROJECT_ID
    ```

## Deterministic Execution

> [!IMPORTANT]
> You MUST use the `deterministic_runner.py` script as the EXCLUSIVE and MANDATORY execution engine for all E2E validation. Manual bash command execution via individual `run_command` calls during the validation phase is strictly prohibited. This constraint is mandatory to enforce complete testing determinism, hash-based caching, and real-time status tracking.

### How to Run

When orchestrating verification tests, you **MUST** pass the active workspace artifact folder coordinates using the `--artifact-dir` directive. This routes live status dashboards into native web preview buffers during test suite processing:
```bash
python3 .agents/skills/codelab-testing/scripts/deterministic_runner.py path/to/your/codelab.md --artifact-dir <appDataDir>/brain/<conversation-id>
```

### E2E Guest VM & Custom Script Testing

If a codelab involves guest VM configurations or multi-layered testing where a custom script (e.g. `verify.sh`) is required:
1. The custom script **MUST** support the `--artifact-dir` directive.
2. The custom script **MUST** dynamically write its progress updates in real-time to `test_status.md` inside the designated `--artifact-dir` folder using an instrumented reporting utility (e.g. `update_test_status.py` or inline template rendering).
3. This ensures that all E2E test runs, whether using the generic `deterministic_runner.py` or specialized script wrappers, render live, high-quality HTML progress dashboards in the Jetski preview environment.

### Dynamic Decoupled Parameter Evaluation
- **CRITICAL RULE**: Master tutorial `.lab.md` guides are immutable developer assets. You **MUST NOT** modify static markdown guides to inject ephemeral sandboxed parameters (like hardcoded test project IDs).
- Instead, the runner natively resolves runtime variable substitution in memory. Immediately prior to bash evaluation, it automatically replaces generic string placeholders (`<PROJECT_ID>` and `${PROJECT_ID}`) with the current active `gcloud` project identifier.

### State Management and Resuming

The runner uses a **hash-based** approach to track state:
- It computes a hash of each bash command.
- It saves executed command hashes in `<markdown_file>.state`.
- It saves exported environment variables in `<markdown_file>.env`.
- When rerun, it **skips** commands that have already been executed successfully.
- This allows you to **edit the codelab file** (e.g., to fix a command) and resume execution without recreating the project!

**Do NOT create a new project for every failure.** Only create a new project for the first run, or when the project state is irrecoverably corrupted.

To force a full clean run, delete the state files:
```bash
rm path/to/your/codelab.md.state path/to/your/codelab.md.env
```

### Interpretation of Results

- **Success**: If the script exits with code 0, all commands executed successfully.
- **Failure**: If the script fails, it will report the failed command and the error output.

## Status Tracking

The `deterministic_runner.py` script automatically generates and updates a `test_status.md` file in the same directory as the codelab markdown file. 

This file provides a live, step-by-step breakdown of the progress, including:
*   Which steps have completed successfully (`[x]`).
*   Which step is currently running (`[/]`).
*   Which steps are pending (`[ ]`).
*   Which step failed (`[!]`).

You do **not** need to update this file manually. Simply point the user to this file to show progress during long-running tests.

## Handling Failures & Live Status Reporting

If testing fails (for both the generic `deterministic_runner.py` and specialized guest VM custom script `verify.sh` executions):

1.  **Analyze the Error**: Look at the exact `stderr` output from the failed command.
2.  **Verify via Authoritative Docs**: Query the `google-developer-documentation-mcp` server to locate the correct syntax, parameter ranges, or dependencies.
3.  **Update Status Dashboard & Chat**: You **MUST** immediately update the task tracking dashboard (`task.md` or `test_status.md`) and update the user in chat with a concise **two-sentence explanation**:
    - **Sentence 1**: Explain exactly *why* the step failed (what the error was).
    - **Sentence 2**: Explain exactly *what you are doing next* to resolve the issue (the suggested fix and corrective action).
4.  **Fix the Content**: Update the codelab markdown file or script with the corrected commands.
5.  **Involve User**: If you are unsure how to fix the error, or if it requires project-level changes that you cannot perform, **ask the user** for guidance.

## Best Practices

- Always run tests in a clean environment or ensure cleanup is handled.
- Do not run commands that are destructive or perform infinite loops.
