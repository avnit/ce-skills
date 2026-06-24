---
name: publish-artifact
description: Publishes generated artifacts (codelabs, one-pagers, blueprints, etc.) to the central ce-skills-artifacts repository under a structured user-centric path.
---

# Publish Artifact Skill

This skill allows you to automate the publishing of local artifacts to the remote `ce-skills-artifacts` repository (`https://github.com/cloud-gtm/ce-skills-artifacts.git`).

The repository is organized to keep everyone's artifacts structured and easily discoverable:
`<username>/<category>/<subject>/`

## When to use this skill

Use this skill when the user explicitly asks to publish, upload, or push an artifact they've created (e.g., a one-pager, codelab, or design blueprint) to the artifacts repository.

## Usage Instructions

To publish an artifact, you need to execute the publishing script with the appropriate arguments.

1. First, ensure the artifact(s) to be published exist in the local workspace.
2. Run the publishing script using the `run_command` tool:

```bash
bash .agents/skills/publish-artifact/scripts/publish.sh -f "<path_to_local_artifact>" -c "<category>" -s "<subject>"
```

### Script Arguments:

- `-f <file_path>`: (Required) The absolute or relative path to the local artifact file you want to publish.
- `-c <category>`: (Required) The category of the artifact. Examples: `customers`, `codelabs`, `diagrams`, `whitepapers`.
- `-s <subject>`: (Required) The specific subject name (e.g., the customer name like `customer_x`, or the codelab topic).

### Example

If the user wants to publish `demo/one-pager.md` for "Customer X":

```bash
bash .agents/skills/publish-artifact/scripts/publish.sh -f "demo/one-pager.md" -c "customers" -s "customer_x"
```

## How it works internally

The script will:

1. Clone the `ce-skills-artifacts.git` repository into a temporary directory if not already present.
2. Determine the current user (`$USER`).
3. Create the target directory structure: `<username>/<category>/<subject>/`.
4. Copy the specified file into the target directory.
5. `git add`, `git commit -m "Publish artifact <filename> for <subject>"`.
6. `git push --set-upstream fork <branch_name>`
7. Use `gh pr create` to automatically open a Pull Request against the main repository.
8. Clean up the temporary clone.

**Important Note**: This script relies on the GitHub CLI (`gh`). The user must be authenticated with `gh auth login` for the fork and PR creation to succeed. The script will output the link to the generated Pull Request. Because this uses a Pull Request workflow, the user does NOT need `Write` access to the `cloud-gtm/ce-skills-artifacts` repository—any organization member with read access can successfully publish artifacts.
