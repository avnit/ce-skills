# Template: Consulting Engineering Design Blueprint

Every Design Blueprint generated for a Google Cloud Consulting Engineering engagement must follow this standard 4-section framework to ensure consistency, clear boundaries, value metrics, and professional pre-sales scoping.

---

## 1. System Design & Reference Architecture (The "What & Why")

### A. Reference Architecture Diagram
*A logical end-to-end target state diagram using standard Google Cloud architecture archetypes.*

```mermaid
graph TD
    %% Reference Architecture Logic
```

### B. Service Selection & Decision Matrix
*Architectural justification for the chosen GCP products and services, detailing trade-offs and competitive differentiators.*

| Selected GCP Product | Alternatives Evaluated | Decision Rationale & Trade-offs |
| :--- | :--- | :--- |
| | | |

### C. Data Value Pattern Flowchart
*Visual mapping of ingestion, storage, processing/transformations, and output consumption channels.*

```mermaid
graph LR
    %% Pipeline Sequence Flow
```

---

## 2. Proof of Concept (PoC) & MVP Guidance (The "How to Verify")

### A. Tightly Scoped PoC Roadmap
*A checklist-driven timeline defining minimum success criteria to validate technical capabilities without over-engineering.*

- **Sprint 1 (Milestone 1)**: 
  - [ ] Task A
- **Sprint 2 (Milestone 2)**: 
  - [ ] Task B

### B. Advisory Templates & Boilerplate Code (VCS Mode 3 stubs)
*High-level configuration templates (e.g., Kubernetes manifests, Terraform HCL stubs, or basic API connectors) to serve as starter kits. The customer's engineering teams will own, adapt, and maintain them.*

```yaml
# Kubernetes configs or Terraform stubs
```

### C. Capacity Sizing & Cost Modeling
*Value-realization sizing formulas (Expected CPUs, RAM, Storage, IOPS, scaling tiers) and expected cost projections linked to the Google Cloud Pricing Calculator.*

*   **Compute Capacity Sizing**: 
*   **Storage Capacity Sizing**: 
*   **GCP Price Estimates**: [Link to GCP Calculator]

---

## 3. Pre-Sales Security & Data Foundations (The Guardrails)

### A. Security & Identity Foundations
*IAM folder hierarchy, SSO bindings, private network scopes (VPCs, Private Service Access), and VPC Service Controls (VPC-SC) boundaries.*

### B. Data Protection Guardrails
*Preserving sandbox environment isolation from sensitive production data. Recommending synthetic data generators or obfuscation policies.*

---

## 4. Legal Disclaimers & Delivery Hand-off (Crucial CE Boundaries)

### Standard "As-Is" Disclaimer
> [!IMPORTANT]
> This document and any attached configuration stubs, stubs, or code blocks are provided purely for advisory and evaluation purposes. Google provides these materials **"as-is"** without any warranties, long-term service level agreements (SLAs), or production support commitments.

### "Hands-Off" Keyboard Boundary
> [!WARNING]
> The customer's internal developers and engineers retain 100% ownership of code execution, merging, deployments, and production readiness. The Consulting Engineer serves strictly in an advisory role and will never execute deployments directly in the customer's networks or environment.

### Partner / Professional Services (PSO) Path
*Direct transition milestones to transition this pre-sales reference architecture into a formal Professional Services (PSO) Statement of Work or engage a System Integration (SI) partner.*
