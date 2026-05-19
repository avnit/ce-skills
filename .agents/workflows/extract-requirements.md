---
description: Orchestrate the automated evaluation of discovery call notes and transcripts to generate comprehensive customer artifacts (Blueprints, Gap Analyses, One-Pagers).
---

# Workflow: Customer Discovery Analysis

Consult the **extracting-requirements-from-meetings**, **customer-gap-analysis**, or **customer-one-pager** skills to steer the analytical extraction sequence using the unified solutions architect prompt.

Required parameters from the user:
1. Target Meeting Source File, Transcript Path, or Google Doc Link (e.g., `meeting/customerX/discovery_transcript.txt`).
2. Target Deliverable Format (Blueprint, Gap Analysis, or One-Pager).

Overall Orchestration Lifecycle:

1. **Phase 1: Scope Intake & Target Alignment**
   - Consult the target skill manifest guidelines alongside the unified **[discovery_analyst.md](prompts/discovery_analyst.md)** system profile.
   - Initialize the mandatory unindented HTML task tracking table (`task.md`) mapping out the progressive extraction steps:
     - Step 1: Retrieve and ingest target meeting notes or transcript assets (prioritizing raw transcripts).
     - Step 2: Load the unified `discovery_analyst.md` system prompt with the designated format flag (e.g., `--format blueprint`, `--format gap_analysis`, `--format one_pager`).
     - Step 3: Extract deep engineering variables, pain points, and objectives.
     - Step 4: Synthesize functional requirements into the target deliverable template.
     - Step 5: Save the finalized artifact to the native filesystem and present it cleanly to the user.

2. **Phase 2: Technical Implementation Analysis**
   - Update the active row state in `task.md` to `RUNNING`.
   - Scan the raw transcript text, focusing intensely on specific variables (VPCs, CIDRs, IAM roles, subnets) and comparisons with other clouds.
   - Map functional specifications and blockers.

3. **Phase 3: Deliverable Assembly & Workspace Persistence**
   - Compile the extracted data into the target markdown template (Artifact Blueprint, Gap Analysis Report, or One-Pager).
   - **Native Persistence Standard**: Save the finalized document inside the customer subfolder under `meeting/` (e.g., `meeting/<customer_name>/artifact_blueprint.md`, `gap_analysis.md`, or `one_pager.md`).
   - Render the output summary alongside the clickable project file link inside the active view buffer.
   - Mark the final task execution state as `COMPLETED` in `task.md`.
