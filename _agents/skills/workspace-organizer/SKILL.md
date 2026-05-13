---
name: workspace-organizer
description: Enforces core repository directory standards, audits root-level clutter, authors persistent structured reports, and securely gates execution via decoupled interactive user approval.
---

# Skill: Workspace Organizer

This skill establishes absolute structural standards for repository file placement to eliminate root-level file bloat and ensure complex project dependencies scale cleanly.

## Established Namespace Boundaries

Every file authored by sub-agents must be routed explicitly into its corresponding core directory namespace:

1. **`_agents/skills/` (Programmatic Runtime Skills)**
   - **Contents**: Complete programmatic runtime capability folders containing a primary `SKILL.md` manifest alongside helper subdirectories (`scripts/`, `resources/`, `examples/`).
   - **Rule**: Never place plain Python runner scripts or utility shell scripts directly in the root if they support programmatic agent tools.
2. **`.agents/` (Declarative Agent Configurations)**
   - **Contents**: High-level framework steering components split into `workflows/` (interactive slash-command guides) and `rules/` (permanent frontmatter instructions activated via `trigger: always_on`).
3. **`prompts/` (Sub-Agent Instructions)**
   - **Contents**: Multi-agent persona text guides (`architect.md`, `writer.md`, `reviewer.md`) loaded dynamically by orchestrator flows.
4. **`scripts/` (Shared Utility Executables)**
   - **Contents**: Common, standalone scripts used globally across the repository lifecycle (e.g. generic cleanup wrappers, deployment hooks) that are not tied to a specific isolated skill.
5. **`resources/` (Global Templates & Configurations)**
   - **Contents**: Shared base configurations, baseline YAML routing manifests, or placeholder templates.
6. **`labs/` (Codelab Playground Space)**
   - **Contents**: Sandboxed instructional packages divided cleanly by tier (`dev/` for experimental iterations, `prod/` for finalized builds). Each tutorial must be encapsulated within its own dedicated directory holding `blueprint.md`, `.lab.md`, and local `img/` subfolders.

## Relocation & Mitigation Hygiene

When executing a workspace organization sweep, follow this explicit interactive protocol:

### 📋 Step 1: Audit Workspace Root
Run the local audit script to discover flat root files and untracked directories programmatically:
```bash
python3 _agents/skills/workspace-organizer/scripts/audit_workspace.py
```

### 📊 Step 2: Author Live Audit Report Artifact
**CRITICAL DECOUPLED UI RULE**: Do NOT output complex comparative markdown tables directly into terminal responses or `ask_question` title fields, as interactive UI modals strip and collapse line breaks and grid syntax, making them unreadable.
Instead, author a dedicated live full markdown artifact file (`workspace_audit_report.md`) saved to the active conversation artifacts directory (`<appDataDir>/brain/<conversation-id>/workspace_audit_report.md`). Structure the file beautifully with standard Markdown formatting:
- **Executive Summary**: Total flat files discovered.
- **Findings Grid**: Clear table listing `Asset Name`, `Current Location`, `Proposed Action` (Move, Delete, Ignore), and `Target Namespace Folder`.
- **Visual Guidance**: GitHub alerts highlighting specific file risks or dependencies.

### 🛑 Step 3: Require Explicit User Approval Gateway
Invoke the **`ask_question`** tool to solicit explicit multiple-choice consent. Point the question title directly to the live markdown report file using clickable links so the user can read the grid natively in their IDE preview tab:
- `question`: "Please review the live Workspace Audit Report artifact ([workspace_audit_report.md](file:///<appDataDir>/brain/<conversation-id>/workspace_audit_report.md)). How would you like to address these flat repository findings?"
- `options`:
  - "(Recommended) Yes, I approve the complete mitigation plan. Execute the proposed moves and cleanups."
  - "No, let's adjust specific targets (e.g., ignore certain files or move to alternate custom folders)."
  - "Skip / Abort workspace sweep."
- `is_multi_select`: false

### 🚀 Step 4: Execute Actions Safely
Only upon receiving explicit user confirmation via the `ask_question` tool response, execute the finalized commands sequentially in the terminal. Update the active tracking file (`task.md`) to reflect the completed relocations.
