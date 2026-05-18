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
    - Consult and enforce the global active auth and ADC validation standard: [gcloud_auth.md](file:///Users/shacharb/Downloads/ce-scale/.agents/rules/gcloud_auth.md).
- [ ] **Phase 1: Research & Goal Definition**
    - Understand the topic and target audience.
    - Search for existing codelabs or documentation on the topic.
- [ ] **Phase 2: Blueprint Design (Pure Markdown Preview Strategy)**
    - **Generate Preview Blueprint**: Create an ephemeral `blueprint.md` inside `<appDataDir>/brain/<conversation-id>/blueprint.md` structured using **pure standard Markdown** formatting to guarantee rock-solid multi-platform preview stability.
    - **Instant Topology Mapping**: Embed the target system architecture directly inside the preview buffer using standard **Mermaid code blocks** to guarantee instant evaluation without rendering engine folding traps.
    - **Obtain Sign-off**: Present the preview artifact link to the user and request design approval via interactive multiple-choice modal (`ask_question`).
    - **Codebase Persistence**: Only upon explicit approval, copy/persist the pure Markdown `blueprint.md` design into the permanent code repository directory (`labs/dev/[lab-name]/`). Full diagram image synthesis can be scheduled asynchronously during published lab generation.
- [ ] **Phase 3: Content Generation**
    - Follow `codelab-formatting` standards.
    - Write the content step-by-step.
- [ ] **Phase 4: Validation**
    - Use `codelab-testing` skill to extract and run commands.
    - Fix any errors found during validation.
- [ ] **Phase 5: User Review**
    - Present the completed codelab to the user for feedback.
- [ ] **Phase 6: Final Delivery**
    - Convert to Google Doc if requested by the user.

## Enterprise Standards

To elevate codelabs to an enterprise standard, follow the principles outlined in [Enterprise Codelab Standards](references/enterprise_standards.md). This includes:
- Leading with business problems.
- Including stateful reliability (e.g., Maglev).
- Implementing negative testing.
- Adding operational guardrails.
- Using modern infrastructure patterns (Instance Templates & MIGs).

## Examples

See a complete example of a blueprint and generated codelab in the `examples/` directory:

- [Blueprint](examples/hello-mcp-cloudrun/blueprint.md)
- [Codelab](examples/hello-mcp-cloudrun/hello-mcp-cloudrun.lab.md)

This example shows how to build a simple MCP server and deploy it to Cloud Run.
