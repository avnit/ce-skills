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

### Phase 2: Automated Execution via Onboarding Skill

1. Initialize or update the live task tracking view board (`task.md`) to mark upfront intake complete and configuration authoring in progress.
2. **Execute Automated Setup Script**: Pass the collected user responses directly into the deterministic onboarding automation script (`.agents/skills/onboarding/scripts/onboard.py`) using a single `run_command` call:
   ```bash
   python3 .agents/skills/onboarding/scripts/onboard.py \
     --persona "<Selected Persona Name>" \
     --folder-id "<Folder ID>" \
     --billing-account "<Billing Account ID>" \
     --cloudtop-host "<Cloudtop Hostname or empty string>" \
     --knowledge-project "<Knowledge Project ID>" \
     --piper-workspace "ce-skills"
   ```
   _Note: This script automatically handles generating `gcp_config.txt` (recording `piper_workspace`), binding `.agents/rules/persona.md`, injecting MCP server credentials into `.gemini/mcp_config.json`, checking or forcing creation of Piper CompanyDoc workspace, compiling OneDoc, synchronizing sidecars, and pre-warming Mermaid CLI cache in a matter of seconds!_
3. Present the script output and confirmation block to the user verifying successful workspace configuration, and mark the overall task flow as `COMPLETED` in `task.md`.
