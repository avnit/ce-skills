---
description: Orchestrate developer environment onboarding tasks including automated generation of mandatory Google Cloud provisioning configuration credentials and dynamic engineering persona bindings
---

# Workflow: Developer Environment Onboarding

Steer the onboarding execution lifecycle to prepare the active workspace environment for seamless Google Cloud sandboxing, solution authoring, and verification tasks. Currently focused on capturing mandatory operational parameters to populate the `gcp_config.txt` credential file automatically, as well as binding the active developer's specific **Google Cloud Systems Engineer Persona** to steer downstream artifact focus dynamically.

## Lifecycle Steering Workflow

### Phase 1: Interactive Onboarding Parameters Intake
1. Consult the `gcp_config.txt` template layout requirements (`folder_id`, `billing_account`, and optional `cloudtop_host`) alongside the Systems Engineering Persona definitions.
2. Invoke the **`ask_question`** tool to present an interactive input intake modal for the user to supply their specific values. Present clear instructions across four structural intake questions:
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
   - **Artifact Constraints**: Tailor all technical reports, blueprint guides, and execution scripts to prioritize the specific metrics, delivery style, and detail granularity defined by this role.
   ```
3. **Author Credential Configuration**: Author the final `gcp_config.txt` file directly into the workspace root directory populated cleanly in standard `key=value` formatting:
   ```text
   folder_id=INPUT_FOLDER_ID
   billing_account=INPUT_BILLING_ACCOUNT
   cloudtop_host=INPUT_CLOUDTOP_HOST
   ```
4. Present a friendly terminal confirmation block to the user verifying successful file creation, and mark the overall task flow as `COMPLETED` in `task.md`.
