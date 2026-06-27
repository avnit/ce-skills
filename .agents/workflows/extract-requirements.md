---
description: Orchestrate the automated evaluation of discovery call notes and transcripts to generate comprehensive customer artifacts (Blueprints, Gap Analyses, One-Pagers).
---

# /extract-requirements: SRE-Grade Solutions Engineering Pipeline

This workflow orchestrates the comprehensive, sequential Solutions Engineering pipeline—taking raw customer transcripts through requirement mapping, design, manual visual approval, visual diagram rendering, sandbox testing, pricing auditing, and environment teardown.

## Role & SRE Operating Principles
You are an autonomous **Solutions Engineering Orchestrator** operating in a 10/10 SRE-grade Google Cloud environment. You manage state, handle infrastructure failures gracefully, compile visual assets, and strictly enforce human-in-the-loop approval gates.

1. **State is Truth & Idempotent Resumption**: Always inspect `<appDataDir>/brain/<conversation-id>/task.md` on initialization. Parse the unindented HTML table badges. If a step is marked `<span style="...">RUNNING</span>` or `<span style="...">REVISION_REQUIRED</span>`, resume execution from that exact checkpoint. Never re-run a completed step (`DONE`).
2. **Autonomous Self-Healing**: Do not fail immediately on transient infrastructure blocks (HTTP 503s, API rate limits) or minor harness syntax errors. If a script or command fails, read stderr, patch the source file or wait 60s, and retry up to **3 times** before escalating to the user.
3. **Strict Gating**: When instructed to invoke `ask_question` at Gates A, B, C, or D, you MUST halt all forward execution until explicit human confirmation is received.

## Pipeline Stages

### 1. Phase 1: Scope Intake & Setup

- Ingest the raw customer transcript file, call notes, or Google Doc link.
- **Pre-Flight Context Depth Check**: Evaluate if the transcript contains sufficient technical depth to formulate an architecture. If core drivers or configurations are completely opaque, halt, mark Step 1 as `<span style="...">BLOCKED</span>` in `task.md`, and present the `Clarification Request` to the user via the `ask_question` tool.
- Initialize the unindented HTML `task.md` tracker in the agent's brain. Mark Step 1 `RUNNING`.
- Load `prompts/discovery_analyst.md`.

### 2. Phase 2: Customer Requirements & Gap Analysis

- Mark Step 2 `RUNNING`.
- Execute `prompts/discovery_analyst.md` with `--format blueprint` to output the Lightweight **Artifact Blueprint** (`artifact_blueprint.md`).
- Execute `prompts/discovery_analyst.md` with `--format gap_analysis` to output the **Knowledge Gap Analysis** (`gap_analysis.md`).
- Save both files under `meeting/<customer_name>/`.

### 3. Phase 3: Google Architecture Design

- Execute `prompts/discovery_analyst.md` with `--format design_blueprint` to output the **Design Blueprint** (`design_blueprint.md`) detailing best practices and a Mermaid flow.
- Save to `meeting/<customer_name>/design_blueprint.md`.
- **Pre-Approval Local Render**: Immediately extract the Mermaid code block from the newly created `design_blueprint.md` and compile it locally using the `creating-gcp-diagrams` skill (Phase 2, Section 3 - compile via `mermaid-cli`). Do NOT use the `-p` flag (padding) in `mermaid-cli` as it triggers configuration errors. If `mermaid-cli` fails, read the stderr, fix the markdown syntax in `design_blueprint.md`, and retry.
- Save the rendered image as `meeting/<customer_name>/assets/design_diagram.png` and embed it directly inside `design_blueprint.md` as a standard markdown image link so it renders beautifully in standard IDE preview.

### 4. Phase 4: Gate A - Design & Topology Visual Confirmation

- **Visual Confirmation Gate**: Pause execution and invoke the **`ask_question`** tool to ask the user to review and approve the Design Blueprint (which now contains the pre-rendered visual diagram).
- **Iterative Feedback & Rejection Loop**: If the user requests modifications or rejects the topology, mark Phase 3 as `<span style="...">REVISION_REQUIRED</span>` in `task.md`, capture feedback, loop back to Phase 3 to regenerate `design_blueprint.md` with the requested adjustments, re-compile `assets/design_diagram.png`, and re-present Gate A.
- **Mandatory High-Fidelity Upgrades & Graceful Degradation**: Upon approval, the agent **MUST** immediately execute Phase 3 of the diagramming skill (`creating-gcp-diagrams`) by calling `generate_image` directly in its own context to compile the final, brand-aligned, icon-anchored high-definition visual asset. If image rendering fails due to transient model API errors, gracefully degrade by retaining the clean local Mermaid preview PNG, log a warning in `task.md`, and proceed forward.
- **Zero-Overhead Automatic Ingestion**: Save this high-definition PNG directly to the **same path** (`meeting/<customer_name>/assets/design_diagram.png`), overwriting the pre-approval low-def placeholder. This guarantees that the final `design_blueprint.md` and any downstream documents (like `one_pager.md`) automatically and natively render the premium visual asset without updating any text references.

### 5. Phase 5: One-Pager & Test Plan Compilation

- Execute `prompts/discovery_analyst.md` with `--format one_pager` to compile the **Customer One-Pager** (`one_pager.md`), incorporating the link to the static PNG diagram.
- Execute `prompts/discovery_analyst.md` with `--format test_plan` to compile the lightweight, functional **Test Plan** (`test_plan.md`).
- Save both files under `meeting/<customer_name>/`.

### 6. Phase 6: Gate B - Interactive Testing & Validation

- **Validation Inquiry Gate**: Pause execution and call **`ask_question`** to ask the user if they want to run E2E verification testing. You **MUST** make live execution the recommended default by listing it as the first option prefixed with `(Recommended) Execute live E2E verification testing against sandbox (with --skip-cleanup)`.
- If yes:
  - Execute the `gcloud-auth-verification` skill to verify credentials.
  - **MANDATORY CLEAN PROVISIONING**: You MUST execute `python3 .agents/skills/gcp-provisioning/scripts/create_project.py <customer_name>-poc` to spin up a fresh, isolated sandbox project and run `disable_org_policies.sh`. NEVER propose or reuse an existing pre-configured developer project ID (e.g., `hyperstack-dev`).
  - **ARCHITECTURAL-VALIDATION PARITY**: The steps in `test_plan.md` MUST strictly match the topology in `design_blueprint.md`. If the blueprint specifies GKE, VPC subnets, or PSC endpoints, `test_plan.md` must include explicit commands to verify or provision those specific resources. Never omit core architectural layers to bypass execution time.
  - **Pre-Execution Interaction**: Parse `test_plan.md` and ask the user to confirm or supply missing runtime environment variables (e.g., `PROJECT_ID`, `REGION`) before initiating test execution.
  - **Self-Healing Execution Loop**: Execute the centralized validation engine using exact pathing: `python3 .agents/skills/codelab-validation/scripts/tester.py meeting/<customer_name>/test_plan.md --artifact-dir <appDataDir>/brain/<conversation-id> --skip-cleanup`. If execution fails due to syntax errors or transient API timeouts (HTTP 503s), autonomously apply code patches or poll up to 3 times at 60s intervals before reporting an error.
  - **CRITICAL SAFETY RULE**: You **MUST** append the `--skip-cleanup` flag to the `tester.py` execution command to ensure the validation engine does not automatically teardown or delete the resources at the end of the test run.

### 7. Phase 7: Gate C - Downstream Strategic Deliverables

- Once validated, pause and call **`ask_question`** to present checkboxes allowing the user to request downstream deliverables. You **MUST** encourage full deliverable generation by prefixing the standalone codelab and pricing estimation options with `(Recommended)`.
  - Hourly pricing estimation (invokes `codelab-pricing-estimator` skill)
  - Sandbox audit logs / validation report (invokes `codelab_audit_logging` skill)
  - Standalone official codelab generation of the solution (invokes the `/create-codelab` workflow).
    - **CRITICAL REUSABILITY STANDARD**: The generated codelab **MUST** be completely generic. Use a generic solution name (e.g., `gke-filestore-hyperdisk-ingress`) for the folder and files under `labs/dev/`.
    - **ZERO CUSTOMER-SPECIFIC INFORMATION**: Ensure that **no customer-specific names, project IDs, or VPC identifiers** (such as "Customer_A", "customer-a-vpc") leak into the published codelab. All customer-specific files and identifiers must remain strictly isolated inside the `meeting/<customer_name>/` folder.
    - **NO SKIPPED STEPS**: Do not modify files in-place or skip standard steps. You **MUST** trigger the full `/create-codelab` workflow from Phase 0.5 through Phase 5, feeding the approved `design_blueprint.md` as the intake source. Ensure the output implements all enterprise-ready standards (business problem framing, clean commented configurations, negative testing steps, and warning callouts).

### 8. Phase 8: Gate D - Lifecycle Teardown & Cleanup

- Pause and call **`ask_question`** to ask the user whether to persistent-keep or delete/teardown the provisioned sandbox environment.
- If delete:
  - **Mandatory Pre-Deletion Sweeping**: To prevent orphaned resource hangs or API blocks during project deletion, you MUST force-empty all active Google Cloud Storage buckets (`gcloud storage rm --recursive gs://<bucket_name>`) and sever active VPC peering connections or liens BEFORE deleting the project.
  - Run the Cleanup section of the codelab without the `--skip-cleanup` restriction, or programmatically call `codelab-cleanup` to delete the GCP project and all associated resources (VPC, GKE, subnets, and storage buckets).
- Update `task.md` steps to `DONE` and output a completion report.
