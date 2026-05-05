---
name: codelab-testing
description: How to test codelabs using deterministic execution and LLM debugging.
---

# Skill: Codelab Testing

This skill provides instructions for testing codelabs to ensure all commands work as expected.

## Setup for Testing

Before running tests, you must provision a new Google Cloud project and disable restrictive organization policies. Follow the instructions in the [GCP Provisioning Skill](file:///Users/shacharb/Downloads/ce-scale/_agents/skills/gcp-provisioning/SKILL.md).

1.  Create a new project:
    ```bash
    python3 _agents/skills/gcp-provisioning/scripts/create_project.py <lab_name>
    ```
2.  Disable org policies:
    ```bash
    bash _agents/skills/gcp-provisioning/scripts/disable_org_policies.sh PROJECT_ID
    ```
3.  Set the active project in `gcloud`:
    ```bash
    gcloud config set project PROJECT_ID
    ```

## Deterministic Execution

To verify the commands in a codelab, use the `deterministic_runner.py` script. This script extracts bash commands from the markdown file and runs them sequentially.

### How to Run

```bash
python3 _agents/skills/codelab-testing/scripts/deterministic_runner.py path/to/your/codelab.md
```

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

## Handling Failures

If testing fails:

1.  **Analyze the Error**: Look at the `stderr` output from the failed command.
2.  **Verify via Documentation**: Use **Code Search** or **MCP** to verify the command syntax and flags.
3.  **Fix the Content**: Update the codelab markdown file with the corrected command.
4.  **Involve User**: If you are unsure how to fix the error, or if it requires project-level changes that you cannot perform, **ask the user** for guidance.

## Best Practices

- Always run tests in a clean environment or ensure cleanup is handled.
- Do not run commands that are destructive or perform infinite loops.
