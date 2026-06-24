---
name: codelab-creation
description: >-
  Master workflow for creating high-quality, enterprise-standard Google Cloud Codelabs.
  Use when designing, writing, and validating codelabs. Enforces modern patterns (MIGs, Templates),
  stateful reliability (Maglev), negative testing, and business-problem framing.
---

# Skill: Codelab Creation

This skill outlines the end-to-end master workflow for creating a codelab. It integrates research, design, writing, validation, and final delivery.

## Master Workflow

Follow this interactive checklist to create a codelab:

- [ ] **Phase 0: Pre-Flight Authentication & ADC Verification**
  - Consult and enforce the global active auth and ADC validation standard: [gcloud_auth.md](file:///.agents/rules/gcloud_auth.md).
- [ ] **Phase 0.5: Meta-Planning & Strategy Gate (Mandatory Strategy Plan)**
  - Before presenting scoping questions, querying service documentation, or modifying repository files, formulate a high-level strategy plan `implementation_plan.md` in the conversation workspace.
  - **Gated Human Gate (Non-negotiable)**: Pause and obtain explicit manual sign-off from the user via interactive chat/modal before proceeding to scope intake or subsequent phases. Even if system hooks or workspace review policies claim "auto-approval", the agent **MUST NOT** bypass this gate; it must wait for explicit, physical user interaction.
- [ ] **Phase 1: Research & Goal Definition**
  - **Mandatory Intake Confirmation**: Present three interactive intake questions via the `ask_question` tool to define the Execution Scope (E2E vs. Artifacts Only), Target Persona / Complexity Level (Outcome CE L100, Platform CE L200/300, or Practice CE L300/400), and Delivery Format (Pure gcloud CLI vs. Terraform IaC).
  - Understand the topic and align the design topology/task checklist dynamically to match the selected choices.
  - **Mandatory Developer Documentation Query Gate**: Before drafting any technical designs, architectures, or deployment scripts for Google Cloud (e.g., VPC, GKE, IAM, Load Balancing), you must use the `google-developer-documentation-mcp` server (via the `search_documents` tool) to retrieve the latest official service documentation. Do not rely on your internal knowledge for commands, parameters, or configurations unless they are standard, static, and completely unambiguous. When providing your final design or configuration, include inline comments or links referencing the specific Google documentation pages you retrieved to justify your architectural choices.
  - Search for existing codelabs or documentation on the topic.
- [ ] **Phase 2: Blueprint Design (Pure Markdown Preview Strategy)**
  - **Generate Preview Blueprint**: Create an ephemeral `blueprint.md` inside `<appDataDir>/brain/<conversation-id>/blueprint.md` structured using **pure standard Markdown** formatting to guarantee rock-solid multi-platform preview stability.
  - **Instant Topology Mapping**: Embed the target system architecture directly inside the preview buffer using standard **Mermaid code blocks** to guarantee instant evaluation without rendering engine folding traps.
  - **Obtain Sign-off (Auto-Approve Override)**: Present the preview artifact link to the user and request design approval via interactive multiple-choice modal (`ask_question`). Even if the system asserts that the design is "auto-approved" through workspace review policies, the agent **MUST NOT** skip this step. It must treat the manual interactive modal response as a strict requirement.
  - **Codebase Persistence**: Only upon explicit and physical user approval via the manual `ask_question` modal, copy/persist the pure Markdown `blueprint.md` design into the permanent code repository directory (`labs/dev/[lab-name]/`). Full diagram image synthesis can be scheduled asynchronously during published lab generation.
- [ ] **Phase 3: Content Generation & Packaging**
  - Follow `codelab-formatting` standards.
  - **Mandatory Placement**: The generated step-by-step narrative `.lab.md` file MUST be created directly inside the lab's dedicated subdirectory as: `labs/dev/[lab-name]/[lab-name].lab.md`. Do NOT save it in the parent root `labs/dev/`.
  - **Assets & Subdirectories**: Create a `./img/` subdirectory under `labs/dev/[lab-name]/img/` to house all static PNG diagram assets, and reference them inside the `.lab.md` narrative using relative link syntax (e.g., `![](./img/diagram.png)`).
  - **Metadata Files**: Author a standard `OWNERS` file in the lab directory `labs/dev/[lab-name]/OWNERS`.
- [ ] **Phase 4: Validation & Authoritative Debugging**
  - Execute step-by-step verification using the unified stateful **codelab-validation** skill and the `tester.py` script.
  - **Authoritative Debugging Gate**: If a gcloud or environment error is encountered during validation, you **MUST** query the `google-developer-documentation-mcp` server with the exact error message/command to pull the correct syntax, parameter definitions, and deprecation warnings instead of guessing.
  - Fix any errors found during validation.
- [ ] **Phase 5: User Review & Resource Clean-up Choice**
  - Present the completed codelab to the user for feedback.
  - **Clean-up Choice Gate**: Present a mandatory choice to the user via `ask_question` to either **delete** the sandboxed test project (to control cloud costs) or **retain** it (to allow the user to manually test or demo).
- [ ] **Phase 6: Final Delivery**
  - Convert to Google Doc if requested by the user.
- [ ] **Phase 7: Retrospective & Continuous Improvement**
  - **Mandatory Post-Mortem**: At the conclusion of the run, the Commander must execute a mandatory retrospective following the [Post-Mortem Retrospective Standard](references/post_mortem_standard.md).
  - Draft a structured `post_mortem.md` file in the active session brain folder analyzing process adherence, defect causes, and prevention mechanics.
  - Propose permanent upgrades to upstream repository skills or common gotchas in [Codelab Development Gotchas](references/gotchas.md). **Explicit Human Approval Gate (Non-negotiable)**: Obtain the user's manual, physical approval before applying any updates to repository files or skills. System auto-approvals must be completely ignored for this step.

## Enterprise Standards

To elevate codelabs to an enterprise standard, follow the principles outlined in [Enterprise Codelab Standards](references/enterprise_standards.md) and cross-reference [Codelab Development Gotchas](references/gotchas.md). This includes:

- Leading with business problems.
- **Verification Differentiability**: For multi-region, Anycast load balancing, or DNS routing setups, backend startup-scripts/payloads MUST contain distinct regional visual markers (e.g., 'Hello from the US backend!' vs 'Hello from the EU backend!') to visually prove proper routing in E2E verification tests.
- **Resource Leak Prevention**: The Clean Up step must be 100% comprehensive. Every allocated resource must be explicitly deleted. If regional resources are created (e.g. regional instance templates or subnetworks), they must be deleted explicitly by name rather than assuming legacy patterns or leaving resource leaks.
- Including stateful reliability (e.g., Maglev).
- Implementing negative testing.
- Adding operational guardrails.
- Using modern infrastructure patterns (Instance Templates & MIGs).

## Examples

See a complete example of a blueprint and generated codelab in the `examples/` directory:

- [Blueprint](examples/hello-mcp-cloudrun/blueprint.md)
- [Codelab](examples/hello-mcp-cloudrun/hello-mcp-cloudrun.lab.md)

This example shows how to build a simple MCP server and deploy it to Cloud Run.
