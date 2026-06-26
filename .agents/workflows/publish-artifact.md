---
description: Orchestrate the end-to-end publishing of local files or directories to internal g3doc CompanyDoc (//depot/company/...) supporting team-wide and personal publishing options with instant live preview links.
---

# Workflow: Publish Artifacts to g3doc CompanyDoc

This workflow guides you through publishing, structuring, and syncing local artifact files or directories (such as Codelabs, One-Pagers, Diagrams, or Blueprints) to internal **g3doc CompanyDoc** (`//depot/company/...`) supporting both team-wide and personal publishing options via automated Critique Changelists (CLs).

## Operational Workflow

### Phase 1: Clarify Parameters & Scoping

1. Use the `ask_question` tool to determine the publishing scope and artifact details:
   - **Publishing Scope**: Ask the user to choose between:
     - **Option 1: Team-wide Publish** (`company/teams/<team_name>/<category>/<subject>/`)
     - **Option 2: Personal Publish** (`company/users/<username>/<category>/<subject>/`)
   - **Team Name**: If Option 1 (Team-wide) is selected, ask for the target team folder (e.g., `practice-ce`, `cloud-gtm`, or `ce-skills`).
   - **File/Folder Path**: The relative or absolute path to the file or directory to publish (e.g., `doc/system_design.md` or `demo/one-pager.md`).
   - **Category**: The artifact classification (e.g., `customers`, `codelabs`, `diagrams`, `blueprints`, `whitepapers`).
   - **Subject**: The specific subject identifier (e.g., customer name or feature topic like `closed_loop_learning`).

### Phase 2: Pre-flight Dependencies Check

1. Verify that the user has an active CitC (Clients-in-the-Cloud) workspace accessible under `/google/src/cloud/$USER/`:
   ```bash
   ls -d /google/src/cloud/$USER/*/company 2>/dev/null | head -n 1
   ```
   If no CitC workspace with a `company` mount is found, instruct the user to create one using `g4 client`.

### Phase 3: Execute Publishing Skill

1. Execute the `publish-artifact` skill script using the `run_command` tool to stage the files in Piper, automatically inject required g3doc metadata (`freshness` tags and `[TOC]`), and prepare the changelist:
   ```bash
   bash .agents/skills/publish-artifact/scripts/publish.sh -f "<path_to_artifact>" -c "<category>" -s "<subject>" -p "<personal|team>" [-t "<team_name>"]
   ```
2. Capture the script output, which will output the direct **g3doc Critique CL Preview Link** (e.g., `https://g3doc.corp.google.com/company/...?cl=<CL_NUMBER>`).

### Phase 4: Interactive Review & Mail CL

1. Display the generated **g3doc Preview Link** prominently to the user so they can click and review the rendered documentation.
2. Use the `ask_question` tool to ask the user if they want to mail/submit the Critique CL:
   - **Question**: "I have staged your artifact in Piper and generated CL #<CL_NUMBER>. Would you like me to mail this CL for review or submit it?"
   - **Options**:
     - "Mail CL #<CL_NUMBER> for review"
     - "Leave CL open in workspace for manual editing"
3. If the user selects "Mail CL":
   - Execute the appropriate mail command in the CitC workspace directory:
     ```bash
     g4 mail <CL_NUMBER>
     ```
   - Confirm to the user that the CL is mailed and provide the Critique review link (`http://cl/<CL_NUMBER>`)!
