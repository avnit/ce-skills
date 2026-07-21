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

- **Phase 0.5: Meta-Planning & Strategy Gate (Mandatory)**: Before presenting any intake questions or using search/research tools, you **MUST** generate a high-level strategy plan `implementation_plan.md` inside `<appDataDir>/brain/<conversation-id>/`. You MUST explicitly pause execution and request user approval of the proposed plan before proceeding.
- **Phase 0.6 Intake Gate**: Invoke the **`ask_question`** tool to present interactive intake questions to the user:
  - **Question 1: Execution Scope**: (Recommended) Full End-to-End (E2E) Verification vs. Generate Artifacts Only.
  - **Question 2: Delivery Format**: (Recommended) Pure gcloud CLI vs. Terraform IaC.
- Ingest the raw customer transcript file, call notes, or Google Doc link.
- **Pre-Flight Context Depth Check**: Evaluate if the transcript contains sufficient technical depth to formulate an architecture. If core drivers or configurations are completely opaque, halt, mark Step 1 as `<span style="...">BLOCKED</span>` in `task.md`, and present the `Clarification Request` to the user via the `ask_question` tool.
- Initialize the unindented HTML `task.md` tracker in the agent's brain based on the chosen scope. Mark Step 1 `RUNNING`.
- Load `prompts/discovery_analyst.md`.

### 2. Phase 2: Customer Requirements & Gap Analysis

- Mark Step 2 `RUNNING`.
- **Proof of Read Constraint**: You MUST use `view_file` to read `prompts/discovery_analyst.md`. Before generating, output a `<template_proof>` block containing the exact headers AND the verbatim first 10 words of the Artifact Blueprint and Knowledge Gap Analysis instructions.
- Read `prompts/discovery_analyst.md` and generate the **Artifact Blueprint** (`artifact_blueprint.md`) strictly following its defined schema.
- Read `prompts/discovery_analyst.md` and generate the **Knowledge Gap Analysis** (`gap_analysis.md`) strictly following its defined schema.
- Save both files under `meeting/<customer_name>/`.

### 3. Phase 3: Google Architecture Design

- **Pre-Flight Constraint**: Output checklist confirming: '[ ] I will save diagrams strictly to meeting/<customer_name>/assets/'.
- **Proof of Read Constraint**: Use `view_file` to read `prompts/customer_architect.md`. Output `<template_proof>` block containing exact headers and verbatim first 10 words.
- **Pre-Flight MCP Health Check**: Before researching, verify `google-developer-knowledge` connectivity (e.g., `search_documents`). If the MCP server fails or is unreachable, keep `search_web` allowed as a secondary fallback tool.
- **Turn 1 (RAG Research)**: Read `artifact_blueprint.md` and `prompts/customer_architect.md`. Use `google-developer-knowledge` (`search_documents` / `answer_query`) or fallback to `search_web` to research required GCP services. Save findings to `meeting/<customer_name>/mcp_research_notes.md`.
- **Turn 2 (Grounded Generation)**: Read `meeting/<customer_name>/mcp_research_notes.md` alongside requirements, invoke **customer-design-blueprint** skill to draft **Design Blueprint** (`design_blueprint.md`). Save to `meeting/<customer_name>/design_blueprint.md`.
- **Pre-Approval Visual Render**: Call `creating-gcp-diagrams` skill using `generate_image` with spatial layout prompting and local GCP category icons. Save as `meeting/<customer_name>/assets/design_diagram.png` and embed directly inside `design_blueprint.md`.
- **Grounded Critic Audit Loop**: Spawn `arch-critic` subagent via `invoke_subagent`. Critic queries official GCP WAF benchmarks via MCP and writes findings to `critic_response.json`.
- **Critic Resolution**: Parse `critic_response.json` and auto-remediate low/medium severity architectural issues in `design_blueprint.md` in-place.

### 4. Phase 4: Gate A - Design & Topology Visual Confirmation

- **Pre-Flight Constraint**: Before generating, output a checklist confirming: '[ ] I will save diagrams strictly to meeting/<customer_name>/assets/'.
- **Visual Confirmation Gate**: Pause execution and invoke the **`ask_question`** tool to ask the user to review and approve the finalized Design Blueprint (which has been audited by the critic and contains the pre-rendered visual diagram).
- **Iterative Feedback & Rejection Loop**: If the user requests modifications or rejects the topology, mark Phase 3 as `<span style="...">REVISION_REQUIRED</span>` in `task.md`, capture feedback, loop back to Phase 3 to regenerate `design_blueprint.md` with the requested adjustments, regenerate the visual asset via `creating-gcp-diagrams`, and re-present Gate A.
- **Zero-Overhead Automatic Ingestion**: Save the high-definition PNG directly to the **same path** (`meeting/<customer_name>/assets/design_diagram.png`), overwriting the placeholder. This guarantees that the final `design_blueprint.md` and any downstream documents (like `one_pager.md`) automatically and natively render the premium visual asset without updating any text references.

### 5. Phase 5: One-Pager & Test Plan Compilation

- **Proof of Read Constraint**: You MUST use `view_file` to read the `customer-one-pager` skill and `prompts/test_engineer.md`. Before generating, output a `<template_proof>` block for both.
- Invoke the **`customer-one-pager`** skill, feed it the `design_blueprint.md` as context, and generate the **Customer One-Pager** (`one_pager.md`) incorporating the link to the static PNG diagram.
- Read `prompts/test_engineer.md`, feed it the `design_blueprint.md` as context, and generate the **Test Plan** (`test_plan.md`), strictly enforcing all rigorous automation and "Bulletproofing UX" validation rules (e.g., `sed` replacements, `EOF` block scripts, and specific Positive/Negative assertions).
- Save both files under `meeting/<customer_name>/`.

### 6. Phase 6: Gate B - Interactive Testing & Validation

- **Pre-Flight Constraint**: Output checklist confirming: '[ ] Clean environment. [ ] Run create_project.py (automatically disables org policies unless --skip-org-policies passed)'.
- **Validation Inquiry Gate**: Pause execution and call **`ask_question`** to ask the user if they want to run E2E verification testing. Make live execution recommended: `(Recommended) Execute live E2E verification testing against sandbox (with --skip-cleanup)`.
- If yes:
  - Execute `gcloud-auth-verification` skill to verify credentials.
  - **ARCHITECTURAL-VALIDATION PARITY**: Steps in `test_plan.md` MUST strictly match `design_blueprint.md` topology. Include commands to verify or provision specific resources.
  - **Pre-Execution Interaction**: Parse `test_plan.md`, confirm missing runtime variables with the user, and write them to `meeting/<customer_name>/variables.json` (the file `tester.py` consumes from the lab directory).
  - **Pre-Flight Code Audit Gate**: Execute the pre-flight code audit gate to validate syntax, unresolved placeholders, and gcloud CLI surface validity before any cloud spend:
    ```bash
    python3 .agents/skills/codelab-validation/scripts/preflight_audit.py \
      meeting/<customer_name>/test_plan.md \
      --variables meeting/<customer_name>/variables.json \
      --check-gcloud-surface \
      --report <appDataDir>/brain/<conversation-id>/preflight_audit_report.md
    ```
    On FAIL (syntax errors, unresolved placeholders, or invalid gcloud command groups): remediate `test_plan.md`—consulting the `google-developer-knowledge` MCP server or `search_web`—and re-run until exit 0 with verdict PASS. **Provisioning MUST NOT begin until the audit passes.**
  - **MANDATORY CLEAN PROVISIONING**: Execute `python3 .agents/skills/gcp-provisioning/scripts/create_project.py <customer_name>-poc` to spin up a fresh sandbox project (which automatically disables org policies). NEVER reuse developer project IDs.
  - **Self-Healing Execution Loop**: Execute validation engine: `python3 .agents/skills/codelab-validation/scripts/tester.py meeting/<customer_name>/test_plan.md --project-id "<PROVISIONED_PROJECT_ID>" --artifact-dir <appDataDir>/brain/<conversation-id> --phase test` (Note: `<PROVISIONED_PROJECT_ID>` is provisioned via `create_project.py`). Autonomously patch or poll up to 3 times on transient errors. Whenever you autonomously solve a validation or script error, strictly update the bug JSON status to `FIXED`, log what failed, what worked, and how it resolved the bug into `remediation`, and run `python3 .agents/skills/closed-loop-learning/scripts/bug_to_lesson_processor.py --scan-dir meeting/<customer_name>/bugs` before proceeding.
  - **CRITICAL SAFETY RULE**: Pass `--phase test` (or deprecated `--skip-cleanup` alias) to `tester.py` to prevent teardown.

### 7. Phase 7: Gate C - Downstream Strategic Deliverables

- Once validated, pause and call **`ask_question`** to present checkboxes allowing the user to request downstream deliverables. You **MUST** encourage full deliverable generation by prefixing the standalone codelab and pricing estimation options with `(Recommended)`.
  - Hourly pricing estimation (invokes `codelab-pricing-estimator` skill)
  - Sandbox audit logs / validation report (invokes `codelab-audit-logging` skill)
  - Standalone official codelab generation of the solution (invokes the `/create-codelab` workflow).
    - **CRITICAL REUSABILITY STANDARD**: The generated codelab **MUST** be completely generic. Use a generic solution name (e.g., `gke-filestore-hyperdisk-ingress`) for the folder and files under `labs/dev/`.
    - **ZERO CUSTOMER-SPECIFIC INFORMATION**: Ensure that **no customer-specific names, project IDs, or VPC identifiers** (such as "Customer_A", "customer-a-vpc") leak into the published codelab. All customer-specific files and identifiers must remain strictly isolated inside the `meeting/<customer_name>/` folder.
    - **NO SKIPPED STEPS**: You **MUST** trigger the `/create-codelab` workflow, but **skip its Phase 2 (Technical Blueprint Design)**. Instead, pass the already-approved `design_blueprint.md` directly into `/create-codelab` Phase 3 (Narrative Content Generation) as the intake source to avoid redundant architectural design loops.

### 8. Phase 8: Gate D - Lifecycle Teardown & Cleanup

- Pause and call **`ask_question`** to ask the user whether to persistent-keep or delete/teardown the provisioned sandbox environment.
- If delete:
  - **Mandatory Pre-Deletion Sweeping**: To prevent orphaned resource hangs or API blocks during project deletion, you MUST force-empty all active Google Cloud Storage buckets (`gcloud storage rm --recursive gs://<bucket_name>`) and sever active VPC peering connections or liens BEFORE deleting the project.
  - Run the Cleanup section of the test plan via explicit `--phase cleanup` (`python3 .agents/skills/codelab-validation/scripts/tester.py meeting/<customer_name>/test_plan.md --project-id "<PROVISIONED_PROJECT_ID>" --phase cleanup`), or programmatically call `codelab-cleanup` to delete the GCP project and all associated resources (VPC, GKE, subnets, and storage buckets).
- Update `task.md` steps to `DONE` and output a completion report.

---
