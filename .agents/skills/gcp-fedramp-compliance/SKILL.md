---
name: gcp-fedramp-compliance
description: >-
  Specialized architectural review skill for U.S. Federal Government and public sector workloads on Google
  Cloud Platform (GCP) seeking FedRAMP High or FedRAMP Moderate Authorization to Operate (ATO). Enforces
  boundary compliance through Assured Workloads (FedRAMP regime), validates authorized GA services against
  Google's FedRAMP boundary, disallows non-compliant preview features or third-party marketplace tools,
  and systematically audits technical controls against NIST SP 800-53 Rev 5. Evaluates FIPS 140-2/3
  cryptography (Cloud HSM CMEK), US data residency, US Persons personnel access restrictions (Access Approval
  & Access Transparency), CAC/PIV authentication, VPC Service Controls perimeters, and comprehensive Cloud
  Audit Logging with immutable retention.
  Use when: auditing architectures for FedRAMP High or Moderate, reviewing federal agency solutions on GCP,
  evaluating NIST 800-53 cloud controls, or preparing FedRAMP System Security Plan (SSP) gap analysis.
---

# Skill: Google Cloud FedRAMP Architecture Compliance Reviewer

This skill provides a comprehensive, specialized architectural review for federal government agencies, systems integrators, and contractors deploying systems subject to **FedRAMP Moderate** or **FedRAMP High** on Google Cloud Platform.

It structures architectural verification around:
1. **Assured Workloads Boundary & Service Authorization**: Ensuring workloads run within Google Cloud Assured Workloads with FedRAMP-specific organization policy constraints (restricting resource locations to US regions, blocking unapproved services, and gating personnel access).
2. **NIST SP 800-53 Rev 5 Technical Controls Audit**: Verifying concrete GCP implementations of Access Control (AC), Identification & Authentication (IA), System and Communications Protection (SC), and Audit and Accountability (AU).

---

## Workflow Overview

```
Phase 0: Federal Impact Level Scoping
   │  ├── Determine Target Impact Level: FedRAMP Moderate (325 controls) vs. FedRAMP High (421 controls)
   │  └── Confirm Assured Workloads Organization & US Data Residency Constraints
   ▼
Phase 1: Architecture & System Component Extraction
   │  ├── Map all GCP resources, VPC boundaries, databases, APIs, and AI/ML pipelines
   │  └── Flag any 3rd-party marketplace software, non-US locations, or external SaaS dependencies
   ▼
Phase 2: FedRAMP Authorized Services Boundary Audit
   │  ├── Cross-reference every proposed product against Google Cloud's FedRAMP High/Moderate boundary
   │  └── Flag any pre-GA (Alpha/Beta/Preview) features or un-authorized third-party software
   ▼
Phase 3: NIST SP 800-53 Rev 5 Technical Controls Audit
   │  ├── AC & IA: CAC/PIV MFA, Workload Identity, session termination, least privilege
   │  ├── SC: Cloud HSM FIPS 140-2 Level 3 CMEK, TLS 1.2+ FIPS ciphers, VPC-SC, Cloud Armor WAF
   │  ├── AU: Mandatory Data Access audit logging (DATA_READ/DATA_WRITE), immutable storage
   │  ├── SI: Container vulnerability scanning (Artifact Registry), VM Manager patch compliance
   │  └── Personnel Access: Assured Workloads US Persons access, Access Approval & Transparency
   ▼
Phase 4: Synthesis & FedRAMP Compliance Report Generation
   └── Generate actionable report using templates/fedramp-review-report-template.md
```

---

## Phase 0: Federal Impact Level Scoping

If not specified, prompt the user via `ask_question`:
- **Target Categorization**:
  - *FedRAMP Moderate*: Standard federal information systems with moderate impact baseline.
  - *FedRAMP High*: Highly sensitive federal workloads, law enforcement, critical infrastructure, healthcare data in federal scope.
- **Assured Workloads Deployment**: Is the workload created inside an Assured Workloads folder with the FedRAMP regime applied?

---

## Phase 1: Architecture & System Component Extraction

Extract and classify:
1. **Compute & Orchestration**: Compute Engine, Google Kubernetes Engine (GKE), Cloud Run, Cloud Functions.
2. **Data & Storage**: Cloud Storage, Cloud SQL, BigQuery, Spanner, Firestore.
3. **Networking & Ingress**: Virtual Private Cloud (VPC), Cloud Load Balancing, Cloud Armor, Cloud Interconnect, Cloud VPN.
4. **Security & Governance**: Assured Workloads, Cloud HSM, Cloud KMS, Secret Manager, Cloud IAM, VPC Service Controls, Security Command Center.
5. **Analytics & AI**: Dataflow, Dataproc, Pub/Sub, Vertex AI (core platform services).

---

## Phase 2: FedRAMP Authorized Services Verification

Check every product against:
- Reference: [fedramp-nist-controls.md](references/fedramp-nist-controls.md)
- Official Documentation: `https://cloud.google.com/security/compliance/fedramp`
- FedRAMP Marketplace: Search Google Cloud at `https://marketplace.fedramp.gov/`

### Strict Evaluation Rules:
1. **No Preview / Alpha Features**: Only Generally Available (GA) services authorized in Google's FedRAMP boundary can be deployed.
2. **US Region Requirement**: All resources must be provisioned strictly in US regions (`us-central1`, `us-east4`, `us-west1`, `us-east1`, `us-west2`, `us-west3`, `us-west4`).
3. **Third-Party Marketplace Software**: Third-party virtual appliances or SaaS in GCP Marketplace are not covered under Google's ATO and require independent FedRAMP authorizations.

---

## Phase 3: NIST SP 800-53 Rev 5 Technical Controls Audit

Audit the 5 foundational control families:

### 1. AC & IA (Access Control & Authentication)
- Enforce CAC / PIV or FIDO2 hardware key MFA on all administrative users via Cloud Identity / Google Workspace IdP federation.
- Disable primitive roles (`Owner`, `Editor`).
- Enforce **Workload Identity** on GKE and Cloud Run; block service account key downloads.

### 2. SC (System and Communications Protection)
- Enforce **Cloud HSM** (FIPS 140-2 Level 3 validated) for all Customer-Managed Encryption Keys (CMEK).
- Enforce TLS 1.2+ with approved FIPS ciphers on Cloud Load Balancing SSL policies.
- Establish **VPC Service Controls (VPC-SC)** security perimeters around all federal data projects.
- Enforce private IPs on all databases and compute nodes; no public IPv4 addresses.

### 3. AU (Audit and Accountability)
- Enable **Data Access audit logs** (`DATA_READ`, `DATA_WRITE`) across all services.
- Route logs via Cloud Logging sinks to a dedicated, restricted security audit project.
- Enforce immutability using Cloud Storage **Bucket Lock (Object Retention)** in compliance mode.

### 4. SI (System and Information Integrity)
- Enable **Security Command Center (SCC)** for automated posture management and threat detection.
- Enable automatic container image vulnerability scanning in **Artifact Registry**.
- Automate OS security patch management via Google Cloud VM Manager.

### 5. Personnel Security & Access Transparency
- Require **Access Approval** for any Google support personnel access.
- Audit all Google operator actions using **Access Transparency** logs.

---

## Phase 4: Output Synthesis & Report Generation

Generate the review report using [fedramp-review-report-template.md](templates/fedramp-review-report-template.md).

Provide:
1. Clear Verdict (🟢 **Compliant**, 🟡 **Conditional**, 🔴 **Non-Compliant**).
2. FedRAMP Authorized Services Verification Matrix.
3. NIST SP 800-53 Rev 5 Controls Assessment.
4. Actionable Remediation Plan prioritized by ATO risk.
