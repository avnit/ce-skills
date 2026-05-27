---
description: Orchestrate the end-to-end generation, validation, and delivery of a Google Cloud Codelab from a user prompt
---

Consult the **codelab-creation** skill to steer the multi-phase orchestrator process for building a high-quality, production-ready tutorial.

Required parameters from the user:
1. Topic / Initial Request Prompt (e.g., "Application Load Balancer with proxy-only subnets")

Overall Orchestration Lifecycle:
1. **Phase 0: Pre-Flight Authentication & ADC Verification**
   - Consult and enforce the global auth validation standard: [gcloud_auth.md](file:///.agents/rules/gcloud_auth.md).
2. **Phase 0.5: Meta-Planning & Strategy Gate**
   - **Mandatory Strategy Plan**: Before presenting any intake questions or using search/research tools, the agent **MUST** generate a high-level strategy plan `implementation_plan.md` inside `<appDataDir>/brain/<conversation-id>/`.
   - **Mandatory Human Gate**: The agent MUST explicitly pause execution and request user approval of the proposed plan before proceeding to scope selection or codebase actions.
3. **Phase 1: Research, Scope Intake & Upfront Alignment**
   - Consult the **[architect.md](prompts/architect.md)** persona guidelines.
   - Invoke the **`ask_question`** tool to present three interactive intake questions to the user:
     - **Question 1: Execution Scope**
       - `question`: "Select the desired execution scope for this Codelab run:"
       - `options`: 
         - "(Recommended) Full End-to-End (E2E) Verification (Generate, Provision GCP, Validate & Review)"
         - "Generate Codelab Artifacts Only (Blueprint & Markdown content without deployment testing)"
     - **Question 2: Target Persona & Complexity Level**
       - `question`: "Select the target user persona and technical complexity level:"
       - `options`:
         - "(Recommended) Practice CE: Target Cloud Architect / Enterprise Operator at Level 300/400"
         - "Platform CE: Target Cloud Architect / Enterprise Operator at Level 200/300"
         - "Outcome CE: Target Developer / Fast Learner at Level 100"
     - **Question 3: Delivery Format**
       - `question`: "Select the preferred configuration and delivery format:"
       - `options`:
         - "(Recommended) Pure gcloud CLI"
         - "Terraform IaC"
     - **Question 4: Sandbox Infrastructure Lifecycle**
       - `question`: "Select sandbox infrastructure lifecycle policy after test validation:"
       - `options`:
         - "(Recommended) Automatically delete all provisioned resources to prevent cloud waste"
         - "Retain active sandbox resources for manual testing and experimentation"
   - **Mandatory Intake Gate**: Under no circumstances should the agent proceed to research, blueprint design, or task initialization until the user has explicitly responded to these interactive questions.
   - **Dynamic Task List Initialization**: Based on the selected scope option, immediately initialize the mandatory unindented HTML table tracking file (`task.md`) mapping out the targeted steps:
     - **Artifacts Only Checklist**: Steps for Upfront Alignment, Blueprint Authoring, and Narrative Markdown Generation.
     - **Full E2E Checklist**: Steps for Upfront Alignment, Blueprint Authoring, Narrative Generation, Sandboxed GCP Project Provisioning, Hermetic Testing Validation, and Quality Review.
   - Query centralized RAG lessons learned via the **codelab-memory** skill.
 4. **Phase 2: Technical Blueprint Design**
   - **CRITICAL RULE - PREVIEW-FIRST BLUEPRINTING**: Do not author plain markdown files directly into the target repo folder initially. Instead, instruct the Architect persona to generate an **ephemeral preview blueprint** inside the conversation tracking folder (`<appDataDir>/brain/<conversation-id>/blueprint.md`).
   - Structure the preview blueprint using **pure standard Markdown formatting** (standard headings `#`, `##`, bullet lists) to ensure flawless IDE rendering tab evaluation and stability.
   - **Low-Latency Topology Mapping**: Embed the architecture diagram directly into the pure Markdown layout using native **Mermaid code blocks** (`mermaid` syntax) to guarantee instant visual rendering without background image synthesis latencies.
   - Dynamically update the active step status in `task.md` to `RUNNING`.
   - **Grounded Critic Audit Loop**: Before presenting the blueprint to the user, spawn the `arch-critic` subagent asynchronously. The critic will query official Google Cloud Well-Architected framework benchmarks and technical constraints using the `google-developer-documentation-mcp` API (e.g., `search_documents`, `answer_query`), and dynamically coordinate remediations with the `cloud-architect` via the file-system-backed mailbox broker.
   - **Critic Resolution Gate**: The loop will run programmatically in the background until the `arch-critic` issues an `APPROVED` mailbox envelope. Every design objection and official Google documentation citation link is archived for complete human audit transparency.
   - **Mandatory Design Sign-off Gate**: Pause execution and invoke the interactive `ask_question` tool to present a modal asking for approval of the preview blueprint design (e.g., options: "Approve and persist blueprint", "Request changes"). Under no circumstances should the agent proceed or write the blueprint to the repository before the user has explicitly approved it through this modal.
   - **Repository Persistence**: Only after receiving explicit user confirmation via the `ask_question` modal, copy/write the finalized contents of `blueprint.md` into the persistent repository directory (`labs/dev/[lab-name]/blueprint.md`), update `task.md` to mark blueprinting complete, and transition to Phase 3.
5. **Phase 3: Narrative Content Generation & Packaging**
   - Delegate drafting tasks to the **[writer.md](prompts/writer.md)** persona guidelines.
   - **Mandatory Subfolder Placement**: You MUST save the narrative step-by-step `.lab.md` tutorial inside its dedicated repository subdirectory: `labs/dev/[lab-name]/[lab-name].lab.md`. Do NOT write it directly to `labs/dev/`.
   - **Assets & Subdirectories**: Create a `./img/` subdirectory under `labs/dev/[lab-name]/img/` and save/copy all PNG architecture diagrams there, referencing them in the markdown via relative link paths (e.g., `![](./img/diagram.png)`).
   - **Metadata Files**: Create a standard `OWNERS` metadata file inside `labs/dev/[lab-name]/OWNERS`.
   - Ensure output structure rigorously applies the formatting checklists defined in the **codelab-formatting** skill.
   - Update `task.md` to mark narrative generation complete. If the "Artifacts Only" scope was selected, conclude execution here and mark overall status as `COMPLETED`.
6. **Phase 4: Hermetic Verification (Full E2E Scope Only)**
   - Provision a pristine sandboxed test environment delegating initialization tasks to the **create-project** workflow and **gcp-provisioning** skill.
   - Verify terminal execution reproducibility statefully by executing the unified **codelab-validation** stateful tester script. **CRITICAL**: You MUST pass the active workspace artifact path down using the `--artifact-dir` command flag to route ephemeral status updates directly into live rendered HTML `task.md` preview buffers. If the user selected "Retain active sandbox resources" in Question 4, you MUST also append the `--skip-cleanup` command flag to the tester execution call.
   - Reflect runtime execution outputs inside the `task.md` output block containers.
7. **Phase 5: Quality Review, Clean-up Choice & Final Delivery (Full E2E Scope Only)**
   - Delegate content quality checks to the **[reviewer.md](prompts/reviewer.md)** persona guidelines.
   - **Clean-up Choice Gate**: If the user selected "Automatically delete" in Question 4, confirm that resources have been fully destroyed. If the user selected "Retain", present an interactive `ask_question` modal to the user, offering them the choice to either **delete** all deployed GCP resources now (Clean up) or **retain** them permanently for continuous experimentation.
   - **Diagram Cost Optimization**: Once the E2E verification has completed successfully, to reduce diagram image generation cost, call the **`creating-gcp-diagrams`** skill to synthesize a high-quality styled image representing the verified architecture. Copy the generated image into the lab's `/img/` subdirectory, and embed it directly into the persistent narrative markdown (`.lab.md`) as a relative image link, replacing or supplementing any plain text descriptions.
   - Present validated Markdown artifacts to the user and mark final execution state as `COMPLETED` in `task.md`.

## 8. Orchestrator Runner Integration & HITL Checkpoints

To programmatically automate this natural-language workflow while maintaining absolute human control, we utilize the **Central Orchestrator Event Loop** script:

👉 **Orchestrator Automation Runner**: [.agents/scripts/orchestrator.py](file:///.agents/scripts/orchestrator.py)

### How Human-in-the-Loop (HITL) Gates are Enforced in Code:

1.  **Phase 0.5 Strategy Sign-Off**: 
    *   *SOP Rule*: "The agent MUST explicitly pause execution and request user approval of the proposed plan."
    *   *Code Hook*: `orchestrator.py` writes the `implementation_plan.md` to the Blackboard, prints a CLI warning, pauses the process execution thread, and blocks until the user hits `[Enter]` (or responds via `ask_question` modal) to proceed or type `abort`.
2.  **Phase 1 Parameter Scope Selection**:
    *   *SOP Rule*: "Invoke the ask_question tool to present interactive intake questions."
    *   *Code Hook*: The script accepts command-line parameters (e.g. `--skip-cleanup`). If omitted in headless mode, it automatically triggers interactive prompt selections to bind variables before running project creation.
3.  **Phase 2 Blueprint Sign-Off**:
    *   *SOP Rule*: "Pause execution and invoke the interactive ask_question tool to present a modal asking for approval of the preview blueprint."
    *   *Code Hook*: The script generates `blueprint.md`, prints the file location, and blocks until the user explicitly provides approval in the console or modal before deploying any VPC or firewall resources.
4.  **Stateful Error Escalation (Bug Blocks)**:
    *   *SOP Rule*: "If the failure persists or is unrecoverable, stop execution."
    *   *Code Hook*: If `tester.py` encounters a failure, `orchestrator.py` intercepts it, logs the error to a structured local bug file `bug_BUGNNN.json`, sets `status: "BLOCKED_HUMAN_REQUIRED"`, prints the stack trace to the terminal, and halts.
    *   *The Resume*: Once the user manually patches the bug in-place and sets the status to `RESOLVED` in the JSON file, hitting `[Enter]` re-engages the runner, which resumes validation exactly at the failed step!
