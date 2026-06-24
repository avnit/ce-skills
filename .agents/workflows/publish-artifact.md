---
description: Orchestrate the end-to-end publishing of local files or directories to the centralized ce-skills-artifacts repository via an automated Pull Request, interactive review, and merge.
---

# Workflow: Publish Artifacts to CE Skills Repository

This workflow guides you through publishing, structuring, and syncing local artifact files or directories (such as Codelabs, One-Pagers, Diagrams, or Blueprints) to the centralized `ce-skills-artifacts` repository (`https://github.com/cloud-gtm/ce-skills-artifacts.git`) using an automated Pull Request model.

## Operational Workflow

### Phase 1: Clarify Parameters & Scoping

1. If the user has not explicitly provided the artifact path, category, and subject, ask directly or use the `ask_question` tool to determine:
   - **File/Folder Path**: The relative or absolute path to the file or directory to publish (e.g., `Customer_a` or `demo/one-pager.md`).
   - **Category**: The artifact classification (e.g., `customers`, `codelabs`, `diagrams`, `whitepapers`).
   - **Subject**: The specific subject identifier (e.g., customer name like `Customer_a`, or codelab topic).

### Phase 2: Pre-flight Dependencies Check

1. Ensure the GitHub CLI (`gh`) is authenticated on the workstation:
   ```bash
   gh auth status
   ```
   If not authenticated, instruct the user to run `gh auth login`.

### Phase 3: Execute Publishing Skill

1. Execute the `publish-artifact` skill script using the `run_command` tool to create the branch, copy the files into the `<username>/<category>/<subject>/` structure, and create a Pull Request:
   ```bash
   .agents/skills/publish-artifact/scripts/publish.sh -f "<path_to_artifact>" -c "<category>" -s "<subject>"
   ```
2. Capture the output from the script, which will include the direct link to the newly created Pull Request (e.g., `https://github.com/cloud-gtm/ce-skills-artifacts/pull/<PR_NUMBER>`).

### Phase 4: Interactive Approval & Merge

1. Display the Pull Request URL prominently to the user.
2. Use the `ask_question` tool to ask the user to review the PR and decide if they want to merge it:
   - **Question**: "I have created Pull Request #<PR_NUMBER> to publish your artifact. Would you like me to automatically merge this Pull Request into main now?"
   - **Options**:
     - "Yes, merge PR #<PR_NUMBER> into main"
     - "No, leave open for manual review"
3. If the user selects "Yes, merge":
   - Execute the GitHub CLI merge command:
     ```bash
     gh pr merge <PR_NUMBER> --merge --delete-branch
     ```
     _(Note: If branch protection requires administrative override, append `--admin` to the command)._
   - Confirm to the user that the artifact is now merged and live on `main`!
