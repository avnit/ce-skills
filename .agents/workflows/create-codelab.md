---
description: Orchestrate the end-to-end generation, validation, and delivery of a Google Cloud Codelab from a user prompt
---

Consult the **codelab-creation** skill to steer the multi-phase orchestrator process for building a high-quality, production-ready tutorial.

Required parameters from the user:
1. Topic / Initial Request Prompt (e.g., "Application Load Balancer with proxy-only subnets")

Overall Orchestration Lifecycle:
1. **Phase 0: Pre-Flight Authentication & ADC Verification**
   - Consult and enforce the global auth validation standard: [gcloud_auth.md](file:///.agents/rules/gcloud_auth.md).
2. **Phase 1: Research, Scope Intake & Upfront Alignment**
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
   - **Mandatory Intake Gate**: Under no circumstances should the agent proceed to research, blueprint design, or task initialization until the user has explicitly responded to these interactive questions.
   - **Dynamic Task List Initialization**: Based on the selected scope option, immediately initialize the mandatory unindented HTML table tracking file (`task.md`) mapping out the targeted steps:
     - **Artifacts Only Checklist**: Steps for Upfront Alignment, Blueprint Authoring, and Narrative Markdown Generation.
     - **Full E2E Checklist**: Steps for Upfront Alignment, Blueprint Authoring, Narrative Generation, Sandboxed GCP Project Provisioning, Hermetic Testing Validation, and Quality Review.
   - Query centralized RAG lessons learned via the **codelab-memory** skill.
2. **Phase 2: Technical Blueprint Design**
   - **CRITICAL RULE - PREVIEW-FIRST BLUEPRINTING**: Do not author plain markdown files directly into the target repo folder initially. Instead, instruct the Architect persona to generate an **ephemeral preview blueprint** inside the conversation tracking folder (`<appDataDir>/brain/<conversation-id>/blueprint.md`).
   - Structure the preview blueprint using **pure standard Markdown formatting** (standard headings `#`, `##`, bullet lists) to ensure flawless IDE rendering tab evaluation and stability.
   - **Low-Latency Topology Mapping**: Embed the architecture diagram directly into the pure Markdown layout using native **Mermaid code blocks** (`mermaid` syntax) to guarantee instant visual rendering without background image synthesis latencies.
   - Dynamically update the active step status in `task.md` to `RUNNING`.
   - **Mandatory Design Sign-off Gate**: Pause execution and invoke the interactive `ask_question` tool to present a modal asking for approval of the preview blueprint design (e.g., options: "Approve and persist blueprint", "Request changes"). Under no circumstances should the agent proceed or write the blueprint to the repository before the user has explicitly approved it through this modal.
   - **Repository Persistence**: Only after receiving explicit user confirmation via the `ask_question` modal, copy/write the finalized contents of `blueprint.md` into the persistent repository directory (`labs/dev/[lab-name]/blueprint.md`), update `task.md` to mark blueprinting complete, and transition to Phase 3.
3. **Phase 3: Narrative Content Generation**
   - Delegate drafting tasks to the **[writer.md](prompts/writer.md)** persona guidelines.
   - Ensure output structure rigorously applies the formatting checklists defined in the **codelab-formatting** skill.
   - Update `task.md` to mark narrative generation complete. If the "Artifacts Only" scope was selected, conclude execution here and mark overall status as `COMPLETED`.
4. **Phase 4: Hermetic Verification (Full E2E Scope Only)**
   - Provision a pristine sandboxed test environment delegating initialization tasks to the **create-project** workflow and **gcp-provisioning** skill.
   - Verify terminal execution reproducibility sequentially delegating to the **codelab-testing** skill. **CRITICAL**: You MUST pass the active workspace artifact path down using the `--artifact-dir` command flag to route ephemeral status updates directly into live rendered web preview buffers.
   - Reflect runtime execution outputs inside the `task.md` output block containers.
5. **Phase 5: Quality Review, Clean-up Choice & Final Delivery (Full E2E Scope Only)**
   - Delegate content quality checks to the **[reviewer.md](prompts/reviewer.md)** persona guidelines.
   - **Clean-up Choice Gate**: Bounded by cost and retention requirements, the orchestrator MUST present an interactive `ask_question` modal to the user, offering them the choice to either **delete** all deployed GCP resources (Clean up) or **retain** them so they can manually test/play with the live deployment.
   - **Diagram Cost Optimization**: Once the E2E verification has completed successfully, to reduce diagram image generation cost, call the **`creating-gcp-diagrams`** skill to synthesize a high-quality styled image representing the verified architecture. Copy the generated image into the lab's `/img/` subdirectory, and embed it directly into the persistent narrative markdown (`.lab.md`) as a relative image link, replacing or supplementing any plain text descriptions.
   - Present validated Markdown artifacts to the user and mark final execution state as `COMPLETED` in `task.md`.

