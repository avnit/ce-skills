---
description: Orchestrate the automated evaluation of discovery call notes and transcripts to generate comprehensive customer artifacts (Blueprints, Gap Analyses, One-Pagers).
---

# Workflow: Customer Discovery & Solutions-Engineering Pipeline

This workflow orchestrates the comprehensive, sequential Solutions Engineering pipeline—taking raw customer transcripts and taking them through requirement mapping, design, manual visual approval, visual diagram rendering, sandbox testing, pricing auditing, and environment teardown.

## Pipeline Stages

### 1. Phase 1: Scope Intake & Setup
- Ingest the raw customer transcript file, call notes, or Google Doc link.
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

### 4. Phase 4: Gate A - Design Blueprint Approval & Image Rendering
- **Visual Confirmation Gate**: Pause execution and invoke the **`ask_question`** tool to ask the user to review and approve the Design Blueprint and Mermaid diagram.
- Upon approval:
    - Execute the `creating-gcp-diagrams` skill to convert the Mermaid text block from `design_blueprint.md` into a static PNG file (e.g. stored under `meeting/<customer_name>/assets/diagram.png`).

### 5. Phase 5: One-Pager & Test Plan Compilation
- Execute `prompts/discovery_analyst.md` with `--format one_pager` to compile the **Customer One-Pager** (`one_pager.md`), incorporating the link to the static PNG diagram.
- Execute `prompts/discovery_analyst.md` with `--format test_plan` to compile the lightweight, functional **Test Plan** (`test_plan.md`).
- Save both files under `meeting/<customer_name>/`.

### 6. Phase 6: Gate B - Interactive Testing & Validation
- **Validation Inquiry Gate**: Pause execution and call **`ask_question`** to ask the user if they want to run E2E verification testing.
- If yes:
    - Execute the `gcloud-auth-verification` skill to verify credentials.
    - Invoke Gcp Provisioning (`create-project` workflow or `gcp-provisioning` skill) to spin up a sandbox project.
    - Execute E2E testing based on `test_plan.md` using the centralized validation engine `tester.py`.
    - **CRITICAL SAFETY RULE**: You **MUST** append the `--skip-cleanup` flag to the `tester.py` execution command to ensure the validation engine does not automatically teardown or delete the resources at the end of the test run.

### 7. Phase 7: Gate C - Downstream Strategic Deliverables
- Once validated, pause and call **`ask_question`** to present checkboxes allowing the user to request:
    - Hourly pricing estimation (invokes `codelab-pricing-estimator` skill)
    - Sandbox audit logs / validation report (invokes `codelab_audit_logging` skill)
    - Standalone official codelab generation of the solution (invokes the `/create-codelab` workflow).
        - **CRITICAL REUSABILITY STANDARD**: The generated codelab **MUST** be completely generic. Use a generic solution name (e.g., `gke-filestore-hyperdisk-ingress`) for the folder and files under `labs/dev/`.
        - **ZERO CUSTOMER-SPECIFIC INFORMATION**: Ensure that **no customer-specific names, project IDs, or VPC identifiers** (such as "Customer_A", "customer-a-vpc") leak into the published codelab. All customer-specific files and identifiers must remain strictly isolated inside the `meeting/<customer_name>/` folder.
        - **NO SKIPPED STEPS**: Do not modify files in-place or skip standard steps. You **MUST** trigger the full `/create-codelab` workflow from Phase 0.5 through Phase 5, feeding the approved `design_blueprint.md` as the intake source. Ensure the output implements all enterprise-ready standards (business problem framing, clean commented configurations, negative testing steps, and warning callouts).

### 8. Phase 8: Gate D - Lifecycle Teardown & Cleanup
- Pause and call **`ask_question`** to ask the user whether to persitent-keep or delete/teardown the provisioned sandbox environment.
- If delete:
    - Run the Cleanup section of the codelab without the `--skip-cleanup` restriction, or programmatically call `codelab-cleanup` to delete the GCP project and all associated resources (VPC, GKE, subnets, and storage buckets).
- Update `task.md` steps to `DONE` and output a completion report.
