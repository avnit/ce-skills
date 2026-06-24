---
description: Orchestrate developer environment onboarding tasks including automated generation of mandatory Google Cloud provisioning configuration credentials and dynamic engineering persona bindings
---

# Workflow: Developer Environment Onboarding

Steer the onboarding execution lifecycle to prepare the active workspace environment for seamless Google Cloud sandboxing, solution authoring, and verification tasks. Currently focused on capturing mandatory operational parameters to populate the `gcp_config.txt` credential file automatically, binding the active developer's specific **Google Cloud Systems Engineer Persona** to steer downstream artifact focus dynamically, and configuring localized Model Context Protocol (MCP) documentation server credentials.

## Lifecycle Steering Workflow

### Phase 1: Interactive Onboarding Parameters Intake

1. Consult the `gcp_config.txt` template layout requirements (`folder_id`, `billing_account`, and optional `cloudtop_host`) alongside the Systems Engineering Persona definitions and the Developer Knowledge API server instruction metadata.
2. Invoke the **`ask_question`** tool to present an interactive input intake modal for the user to supply their specific values. Present clear instructions across five structural intake questions:
   - **Question 1 (Systems Engineer Persona Binding)**:
     - `question`: "Select your primary Google Cloud Systems Engineer role/objective to steer future artifact focus dynamically:"
     - `options`:
       - "(Recommended) Practice CE (Focuses on deep specialized technical domains like Networking, Infrastructure, Security, Data, and AI. Artifacts prioritize deep technical design, precise topology diagrams, exact CLI flags, and granular configurations)."
       - "Platform CE (Focuses on overall customer business objectives, cross-product landing zones, and platform design systems. Artifacts prioritize holistic system architectures, enterprise governance guardrails, and strategic outcomes)."
       - "Outcome CE (Focuses on rapid customer ramping, immediate time-to-value, unblocking priority plays, and migration executions. Artifacts prioritize low-latency execution speed-runs, copy-pasteable delivery mechanics, and immediate visual micro-validations)."
     - `is_multi_select`: false
   - **Question 2 (Target Folder ID)**:
     - `question`: "Please provide your target Google Cloud Folder ID (used to provision sandbox test projects) using the text write-in box below:"
     - `options`:
       - "Use custom write-in field below to supply Folder ID"
       - "Reuse sample template: 123456789012"
     - `is_multi_select`: false
   - **Question 3 (Target Billing Account ID)**:
     - `question`: "Please provide your target Google Cloud Billing Account ID (e.g. 010101-A1A1A1-B2B2B2) using the text write-in box below:"
     - `options`:
       - "Use custom write-in field below to supply Billing Account ID"
       - "Reuse sample template: 010101-A1A1A1-B2B2B2"
     - `is_multi_select`: false
   - **Question 4 (Cloudtop Hostname)**:
     - `question`: "Please provide your dedicated Cloudtop workstation hostname using the text write-in box below (optional):"
     - `options`:
       - "Use custom write-in field below to supply Cloudtop Hostname"
       - "Reuse sample template: generic-dev-cloudtop.c.googlers.com"
       - "Skip / Leave empty"
     - `is_multi_select`: false
   - **Question 5 (Developer Knowledge Quota Project ID)**:
     - `question`: "Select or provide your target Google Cloud Project ID enabled for Developer Knowledge API access (used for MCP documentation search quota):"
     - `options`:
       - "(Recommended) Keep shared repository baseline default: codelab-creator-central"
       - "Use custom write-in field below to supply personal Developer Knowledge Project ID"
       - "Consult quickstart setup guide instructions first"
     - `is_multi_select`: false

### Phase 2: Automated Workspace File Generation

1. Initialize or update the live task tracking view board (`task.md`) to mark upfront intake complete and configuration authoring in progress.
2. **Author Systems Engineer Persona Rule**: Based on the selected persona option, immediately author the permanent agent behavior rule file (`.agents/rules/persona.md`) structured with standard YAML activation block formatting:

   ```markdown
   ---
   trigger: always_on
   description: Dynamically binds the active developer's Systems Engineering Persona to steer downstream architectural decisions, depth focus, and artifact structures.
   ---

   # Systems Engineering Persona Binding

   The user environment is operating under the following primary Customer Engineering role:

   ## Active Role Focus: [Practice CE / Platform CE / Outcome CE]

   - **Primary Objectives**: [Insert specific objective summary mapping chosen persona].
   - **Mapped Architectural Configurations (Mandatory Prompts Binding)**:
     - **Practice CE Mappings**:
       - Target Audience: `Cloud Architect / Enterprise Operator`
       - Technical Level Depth: `Level 300 (Advanced Stateful & Resiliency Patterns)` or `Level 400 (Expert Deep Dive)`
       - Delivery Tooling Preference: `Hybrid Setup (Terraform networking, gcloud workloads)` or `Pure gcloud CLI`
       - Execution Realism: Highly scaled, production HA networks, terminal-first, with negative security testing.
     - **Platform CE Mappings**:
       - Target Audience: `Cloud Architect / Enterprise Operator`
       - Technical Level Depth: `Level 200 (Intermediate Functional Walkthrough)` or `Level 300 (Advanced)`
       - Delivery Tooling Preference: `Terraform IaC (Optimized for declarative GitOps)`
       - Execution Realism: Broad landing zones, strategic IAM governance, and declarative state management.
     - **Outcome CE Mappings**:
       - Target Audience: `Developer / Fast Learner`
       - Technical Level Depth: `Level 100 (Foundational Quick-Start)`
       - Delivery Tooling Preference: `Pure gcloud CLI (Optimized for rapid console validation)`
       - Execution Realism: Simple network setup, minimal VM footprints, copy-paste speed-runs, and rapid visual UI confirmations.
   ```

3. **Author Credential Configuration**: Author the final `gcp_config.txt` file directly into the workspace root directory populated cleanly in standard `key=value` formatting:
   ```text
   folder_id=INPUT_FOLDER_ID
   billing_account=INPUT_BILLING_ACCOUNT
   cloudtop_host=INPUT_CLOUDTOP_HOST
   ```
4. **Update MCP Server Quota Headers**: Read the workspace `.gemini/mcp_config.json` configuration file. If the user supplies a custom write-in project ID during intake, parse the structural JSON and update the `google-developer-documentation-mcp` server section to pre-inject their personal namespace into the HTTP payload headers:
   ```json
   "headers": {
     "X-goog-user-project": "CUSTOM_KNOWLEDGE_PROJECT_ID"
   }
   ```
   If the user selects the recommended repository baseline default, keep `"codelab-creator-central"` gracefully intact.
5. **Inject Google Workspace MCP Server**: Verify if the `"workspace"` server configuration block is present in `.gemini/mcp_config.json`. If missing, insert the following configuration under `"mcpServers"`:
   ```json
   "workspace": {
     "$typeName": "exa.cascade_plugins_pb.CascadePluginCommandTemplate",
     "command": "/google/bin/releases/codemind-mcp-servers/workspace_server.par",
     "args": [],
     "env": {}
   }
   ```
   Write the updated configuration object cleanly back to `.gemini/mcp_config.json` with standard 2-space formatting.
6. **Compile and Verify OneDoc CLI Tool**: Search for an active Google3 CITC workspace under `/google/src/cloud/<user>/` and run `blaze build //geo/gestalt/experimental/onedoc` to natively compile the standalone `onedoc.par` binary.
7. **Sync and Onboard Workspace Sidecar Daemons**: Execute the repository sidecar sync utility `bash .agents/scripts/sync_sidecars.sh` to securely copy all version-controlled sidecars and background watcher scripts into the local active Jetski environment, spinning up background daemons automatically.
8. **Verify and Pre-warm Mermaid CLI Validator Dependencies**: Verify that Node.js, `npm`, and `npx` are active in the environment, and pre-warm the `@mermaid-js/mermaid-cli` compiler caching via `npx -y @mermaid-js/mermaid-cli --help`. This pre-downloads Puppeteer's headless Chrome binaries to ensure instant diagram syntax validation during subsequent runs.
9. Present a friendly terminal confirmation block to the user verifying successful file creation, OneDoc compilation, sidecar synchronization, Mermaid CLI pre-warming, and updates, and mark the overall task flow as `COMPLETED` in `task.md`.
