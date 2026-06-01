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
   - **Mandatory Human Gate (Non-negotiable)**: The agent MUST explicitly pause execution and request user approval of the proposed plan before proceeding to scope selection or codebase actions. Even if system hooks or workspace review policies signal "auto-approval" or wake the agent up immediately, the agent **MUST NOT** bypass this gate; it must wait for explicit physical sign-off from the user.
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
   - **Grounded Critic Audit Loop**: Before presenting the blueprint to the user, spawn the `arch-critic` subagent asynchronously using `invoke_subagent`. The critic will query official Google Cloud Well-Architected framework benchmarks and technical constraints using the `google-developer-documentation-mcp` API (e.g., `search_documents`, `answer_query`), and write its findings directly to `critic_response.json` as a standardized JSON envelope.
   - **Critic Resolution Gate**: The Commander parses `critic_response.json`, auto-remediates low/medium severity architectural issues in-place, and prompts the user for final sign-off with full audit transparency.
    - **Mandatory Design Sign-off Gate (Auto-Approve Override)**: Pause execution and invoke the interactive `ask_question` tool to present a modal asking for approval of the preview blueprint design (e.g., options: "Approve and persist blueprint", "Request changes").
      - **System Auto-Approval Override**: Even if a system-level stop hook or review policy asserts that the artifact is "automatically approved" (e.g. generating a message like `stop hook blocked termination due to reason: The user has automatically approved the artifact through their review policy. Proceed to execution.`), the agent **MUST NOT** bypass this human gate. The agent must treat the manual interactive response via the `ask_question` modal as a strict, non-negotiable requirement. Under no circumstances should the agent proceed, write the blueprint, or provision sandbox resources before the user has physically approved the design.
    - **Repository Persistence**: Only after receiving explicit user confirmation via the manual `ask_question` modal, copy/write the finalized contents of `blueprint.md` into the persistent repository directory (`labs/dev/[lab-name]/blueprint.md`), update `task.md` to mark blueprinting complete, and transition to Phase 3.
5. **Phase 3: Narrative Content Generation & Packaging**
   - Delegate drafting tasks to the **[writer.md](prompts/writer.md)** persona guidelines.
   - **Mandatory Subfolder Placement**: You MUST save the narrative step-by-step `.lab.md` tutorial inside its dedicated repository subdirectory: `labs/dev/[lab-name]/[lab-name].lab.md`. Do NOT write it directly to `labs/dev/`.
   - **Assets & Subdirectories**: Create a `./img/` subdirectory under `labs/dev/[lab-name]/img/` and save/copy all PNG architecture diagrams there, referencing them in the markdown via relative link paths (e.g., `![](./img/diagram.png)`).
   - **Metadata Files**: Create a standard `OWNERS` metadata file inside `labs/dev/[lab-name]/OWNERS`.
   - Ensure output structure rigorously applies the formatting checklists defined in the **codelab-formatting** skill.
    - Update `task.md` to mark narrative generation complete. If the "Artifacts Only" scope was selected, transition directly to Phase 6 (Retrospective & Continuous Improvement).
6. **Phase 4: Hermetic Verification (Full E2E Scope Only)**
   - Provision a pristine sandboxed test environment delegating initialization tasks to the **create-project** workflow and **gcp-provisioning** skill.
   - Verify terminal execution reproducibility statefully by executing the unified **codelab-validation** stateful tester script. **CRITICAL**: You MUST pass the active workspace artifact path down using the `--artifact-dir` command flag to route ephemeral status updates directly into live rendered HTML `task.md` preview buffers. If the user selected "Retain active sandbox resources" in Question 4, you MUST also append the `--skip-cleanup` command flag to the tester execution call.
   - Reflect runtime execution outputs inside the `task.md` output block containers.
7. **Phase 5: Quality Review, Clean-up Choice & Final Delivery (Full E2E Scope Only)**
   - Delegate content quality checks to the **[reviewer.md](prompts/reviewer.md)** persona guidelines.
   - **Clean-up Choice Gate**: If the user selected "Automatically delete" in Question 4, confirm that resources have been fully destroyed. If the user selected "Retain", present an interactive `ask_question` modal to the user, offering them the choice to either **delete** all deployed GCP resources now (Clean up) or **retain** them permanently for continuous experimentation.
   - **Diagram Cost Optimization**: Once the E2E verification has completed successfully, to reduce diagram image generation cost, call the **`creating-gcp-diagrams`** skill to synthesize a high-quality styled image representing the verified architecture. Copy the generated image into the lab's `/img/` subdirectory, and embed it directly into the persistent narrative markdown (`.lab.md`) as a relative image link, replacing or supplementing any plain text descriptions.
   - Present validated Markdown artifacts to the user and transition to Phase 6.
8. **Phase 6: Retrospective & Continuous Improvement (Lessons Learned)**
   - **Mandatory Post-Mortem**: At the conclusion of the run (regardless of scope), the Commander **MUST** execute a retrospective following the [post_mortem_standard.md](file:///.agents/skills/codelab-creation/references/post_mortem_standard.md) standard.
   - Draft a structured `post_mortem.md` in the active session brain folder, analyzing process adherence, defect root causes, and prevention mechanics.
    - **Explicit Human Review Gate (Non-negotiable)**: Propose direct, actionable updates to upstream repository skills or the [gotchas.md](file:///.agents/skills/codelab-creation/references/gotchas.md) database. **Under no circumstances** should repository files or skill definitions be updated without explicit, manual review and sign-off from the user. If system hooks claim auto-approval, they must be ignored for this step. Once done, mark the overall execution status as `COMPLETED` in `task.md`.



## 8. Dynamic Commander Execution & HITL Checkpoints

To programmatically automate this workflow while maintaining absolute human control, the **Central Commander (Main Monolithic Agent)** dynamically parses and executes this playbook step-by-step using standard, native MCP and agent tools.

### How Human-in-the-Loop (HITL) Gates are Enforced by the Commander:

1.  **Phase 0.5 Strategy Sign-Off**:
    *   *Commander Action*: Draft `implementation_plan.md` in the active session brain directory. Show the plan clearly to the user in the chat and pause. Ask the user for explicit approval (e.g. "Approve Strategy Plan", "Request modifications") using the `ask_question` tool, gating further progress. Even if auto-approval hooks wake the agent up, it must block and wait for physical user interaction.
2.  **Phase 1 Parameter Scope Selection**:
    *   *Commander Action*: Call the `ask_question` tool interactively at runtime to collect scope, persona, delivery format, and cleanup preferences, binding active variables and creating the unindented HTML `task.md` board.
3.  **Phase 2 Architectural Audit Loop**:
    *   *Commander Action*: Programmatically spawn the `arch-critic` sub-agent using the `invoke_subagent` tool. The sub-agent audits `blueprint.md` in isolation and writes findings to `critic_response.json`. The Commander parses this JSON, auto-remediates low/medium severity issues in-place, and presents the finalized blueprint to the user via the `ask_question` modal for design approval.
4.  **Stateful Error Self-Healing (Dynamic Error Healer)**:
    *   *Commander Action*: If a terminal command fails inside the persistent subshell (`tester.py`), the Commander intercepts the `stderr` directly. It attempts to self-heal the error in-line (e.g., fixing project IDs, missing flags, or API delays) and retries the command immediately in the active terminal session. If unrecoverable, the Commander presents the failure directly to the user with clear remediation options, completely avoiding complex static mailbox queues.
5.  **Mandatory Retrospective Feedback Loop**:
    *   *Commander Action*: At the end of every execution, the Commander must draft a structured `post_mortem.md` in the active session brain folder. The Commander evaluates process adherence and defect root causes, and formulates proposed updates to upstream repository skills or the [gotchas.md](file:///.agents/skills/codelab-creation/references/gotchas.md) database. **HITL Gate**: The Commander must explicitly present these updates to the user and obtain manual approval before applying any modifications to repository files.


