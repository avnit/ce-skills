---
name: customer-design-blueprint
description: >-
  Guides the creation of enterprise-standard Design Blueprints (design_blueprint.md) based on the Google Cloud Architecture Framework, explaining why and how, with premium styled Mermaid diagrams.
---

# Customer Design Blueprint (Stage 3)

This skill defines the methodology for architecting and writing the **Design Blueprint** (`design_blueprint.md`), our proposed technical solution for the customer following standard Google Cloud Consulting Engineering best practices.

## Workflow

- [ ] Step 1: Analyze the extracted requirements (`artifact_blueprint.md`) and knowledge gaps (`gap_analysis.md`).
- [ ] Step 2: Query the **google-developer-documentation-mcp** server (`search_documents` or `answer_query`) targeting the **Google Cloud Architecture Framework** to validate chosen services.
- [ ] Step 3: Draft the four core pillars of the Design Blueprint using the standard CE template.
- [ ] Step 4: Describe the visual layout of the Reference Architecture and Data Value Pattern so the downstream image generation skill can accurately render them into PNGs.
- [ ] Step 5: Save the blueprint directly to `meeting/<customer_name>/design_blueprint.md`.

## Analysis Prompt

Use the unified discovery and solutions architect system prompt defined in [discovery_analyst.md](file:///prompts/discovery_analyst.md) passing the target flag: `--format design_blueprint`.

---

## Design Blueprint Framework & Template

Every Design Blueprint generated for a customer MUST conform to the following structure:

```markdown
# Design Blueprint: [Customer Name] - [Project Name]

## 1. System Design & Reference Architecture (The "What & Why")

### A. Reference Architecture Diagram

[Provide a clear visual mapping of the end-to-end target state using standard Google Cloud architecture archetypes.]

![Reference Architecture Diagram](assets/design_diagram.png)
```

### B. Service Selection & Decision Matrix

[Provide clear architectural justification for the chosen GCP services over alternative options, contrasting with competitors or other GCP offerings.]

| Chosen GCP Service         | Alternative Considered    | Decision Rationale & Trade-offs                                                                                                                 |
| :------------------------- | :------------------------ | :---------------------------------------------------------------------------------------------------------------------------------------------- |
| e.g., Filestore Enterprise | Filestore Basic / AWS EFS | Filestore Enterprise provides regional synchronous replication and 99.99% SLA, required for Tier-1 microservices, whereas Basic is single-zone. |

### C. Data Value Pattern Flowchart

[Visualize ingestion paths, storage systems, transformations, and final output consumers.]

![Data Pipeline Flow](assets/data_pipeline.png)

---

## 2. Proof of Concept (PoC) & MVP Guidance (The "How to Verify")

### A. Tightly Scoped PoC Roadmap

[A checklist-driven plan defining the minimum criteria needed to achieve a "technical win" without over-engineering, divided into sprints.]

- **Sprint 1 (Days 1-5): Foundation & Connections**
  - [ ] Connect networking perimeters and create private IP ranges.
- **Sprint 2 (Days 6-10): Core Deployment & Dynamic CSI Validation**
  - [ ] Provision cluster and assert dynamic dynamic storage mounts.
- **Sprint 3 (Days 11-14): Managed Ingestion & E2E Verification**
  - [ ] Trigger managed STS transfer jobs and assert data flow integrity.

### B. Advisory Templates & Boilerplate Code (VCS Mode 3)

> [!NOTE]
> These stubs represent high-level configuration snippets (YAML manifests, basic Terraform stubs, or generic Python connectors) to serve as starter kits. The customer's teams will take ownership and adapt them.

```yaml
# Provide precise Kubernetes YAML, Terraform HCL, or CLI scripts here
```

### C. Capacity Sizing & Cost Modeling

[Detail expected sizing formulas (CPUs, RAM, Storage, IOPS) and cost projections linked to the Google Cloud Pricing Calculator.]

- **Compute Sizing**: `Num Nodes = Total Pod Memory / Node Available Memory`
- **Storage Capacity & IOPS**: Sized for `1 TiB` Filestore Enterprise minimum capacity.
- **Estimated Cost Projection**: Mapped directly under Google Cloud Pricing Calculator.

---

## 3. Pre-Sales Security & Data Foundations (The Guardrails)

### A. Security/Identity Foundations

- **Identity Management**: Managed SSO & IAM group hierarchy outlining least-privilege bindings.
- **Network Protection**: VPC Service Controls (VPC-SC) outline to secure project assets against data exfiltration.

### B. Data Protection Guardrails

- **Sandbox Isolation**: Ensure the pre-sales sandbox is completely isolated from sensitive production data.
- **Synthetic Data Recommendation**: Recommend synthetic generators (e.g., Dataflow Data Generator) or masking policies to keep testing hermetic.

---

## 4. Legal Disclaimers & Delivery Hand-off (Crucial CE Boundaries)

### Standard "As-Is" Disclaimer

> [!IMPORTANT]
> This document and any attached stubs/scripts are provided strictly for advisory and evaluation purposes. Google provides these assets **"as-is"** without warranties, long-term SLA commitments, or production support.

### "Hands-Off" Keyboard Boundary

> [!WARNING]
> The customer’s internal engineering team retains 100% ownership of configuration execution, deployment, and production merges. The Consulting Engineer acts solely in an advisory capacity and will never execute code directly in the customer's environment.

### Partner / PSO Enablement Path

- **Next Steps**: Plan to transition the CE reference architecture into a detailed Professional Services (PSO) Statement of Work (SOW) or engage a certified System Integrator (SI) partner.

```

```
