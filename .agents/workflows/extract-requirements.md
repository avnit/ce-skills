---
description: Orchestrate the automated evaluation of meeting notes and transcripts to extract comprehensive customer requirements and technical artifacts
---

Consult the **extracting-requirements-from-meetings** skill to steer the analytical extraction sequence for compiling a high-fidelity Artifact Blueprint.

Required parameters from the user:
1. Target Meeting Source File, Transcript Path, or Google Doc Link (e.g., `meeting/customerX/discovery_transcript.txt` or `https://docs.google.com/document/d/...`)

Overall Orchestration Lifecycle:
1. **Phase 1: Scope Intake & Source Retrieval**
   - Consult the **extracting-requirements-from-meetings** skill guidelines alongside the core **[meeting_analyzer.md](prompts/meeting_analyzer.md)** system profile.
   - Initialize the mandatory unindented HTML task tracking table (`task.md`) mapping out the progressive extraction steps:
     - Step 1: Retrieve target meeting notes or transcript assets.
     - Step 2: Evaluate multi-tab document layouts (prioritizing Transcript tabs natively).
     - Step 3: Apply technical requirement extraction models via `meeting_analyzer.md` system logic.
     - Step 4: Map functional drivers to prioritized advisory deliverables (P0, P1, P2).
     - Step 5: Present finalized Artifact Blueprint structures cleanly to the user.
2. **Phase 2: Technical Implementation Analysis**
   - Update the active row state in `task.md` to `RUNNING`.
   - Scan the raw transcript source text focusing intensely on specific engineering variables (CIDRs, subnets, accounts) and past competitive pain points.
   - Differentiate rigorously between functional "must-have" requirements and long-term optional optimizations.
3. **Phase 3: Artifact Blueprint Assembly & Persistence**
   - Compile the extracted metrics directly into the **Blueprint Template** defined within the skill specification.
   - **Native Persistence Standard**: Ensure the finalized Artifact Blueprint document is explicitly saved to the native project filesystem under the target customer collaboration subfolder (e.g., using `write_to_file` with `IsArtifact: false` to save as `meeting/<customer_name>/artifact_blueprint.md`).
   - Render the output summary alongside the clickable project file link inside the active view buffer.
   - Mark final task execution state as `COMPLETED` in `task.md`.
