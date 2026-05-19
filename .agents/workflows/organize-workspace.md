---
description: Orchestrate automated repository audits to classify flat root files and enforce clean folder structures adhering to core workspace standards
---

# Workflow: Organize Workspace

Steer automated structural audits across the repository to identify misplaced files, flat subdirectories, or root-level clutter, enforcing systematic placement across defined structural namespaces.

## Overall Orchestration Lifecycle

### Phase 1: Scope Intake & Target Definition
1. Consult the **workspace-organizer** skill manifest (`.agents/skills/workspace-organizer/SKILL.md`) to load established directory boundaries and file placement patterns.
2. Invoke the **`ask_question`** tool to present an interactive intake modal allowing the user to configure the exact cleanup scope:
   - **Question 1 (Audit Scope Target)**:
     - `question`: "Select the structural scope for this workspace organization sweep:"
     - `options`:
       - "(Recommended) Audit Root-Level Clutter (Identify and classify flat configuration files, scripts, and manifests sitting directly in the workspace root directory)."
       - "Audit Specific Subdirectory (Scan a designated lab or skill subfolder to enforce clean nested structures for code assets and media)."
       - "Full Repository Deep-Sweep (Analyze all untracked and modified files globally to propose unified git mv mapping)."
     - `is_multi_select`: false
   - **Question 2 (Execution Action)**:
     - `question`: "Select the desired execution enforcement mode:"
     - `options`:
       - "(Recommended) Interactive Proposal (Classify misplaced files and output a structured review board of proposed 'git mv' commands for explicit approval before execution)."
       - "Automated Sweep (Move known standard patterns like helper scripts or metadata files to their designated folders immediately)."
     - `is_multi_select`: false

### Phase 2: Classification & Re-structuring
1. Initialize the live task tracking board (`task.md`) to reflect structural audit progress.
2. Run classification heuristics mapping identified flat assets to appropriate target buckets:
   - Programmatic execution hooks (`scripts/`)
   - Declarative Kubernetes/Cloud manifests (`resources/`)
   - Multi-agent prompts (`prompts/`)
   - Individual tutorial code components (`labs/dev/<lab-name>/`)
3. Propose or execute clean movement sequences leveraging `git mv` or `mv` commands to preserve version tracking history where applicable.
4. Summarize finalized workspace folder structures and conclude execution marking status as `COMPLETED` in `task.md`.
