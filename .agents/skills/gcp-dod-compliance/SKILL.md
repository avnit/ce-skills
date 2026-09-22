---
name: gcp-dod-compliance
description: >-
  Specialized architectural review skill for Department of Defense (DoD), defense industrial base (DIB),
  and military mission workloads on Google Cloud Platform (GCP) subject to the DoD Cloud Computing Security
  Requirements Guide (CC SRG) for Impact Levels 2, 4, and 5 (IL2, IL4, IL5). Audits boundary compliance against
  DISA Provisional Authorizations (PA), mandates Google Cloud Assured Workloads (DoD IL4 / DoD IL5 regimes),
  enforces CONUS data residency, restricts operations access to US Persons/Citizens, verifies DISA Cloud Access
  Point (CAP/BCAP) hybrid connectivity, mandates FIPS 140-2 Level 3 hardware cryptography (Cloud HSM CMEK),
  enforces CAC/PKI authentication, and reviews audit logging integration with DoD Cybersecurity Service Providers (CSSP).
  Use when: auditing architectures for DoD compliance, reviewing DoD IL2, IL4, or IL5 systems on GCP,
  evaluating Controlled Unclassified Information (CUI) or National Security Systems (NSS) on Google Cloud,
  or preparing DoD Authorization to Connect (ATC) and Authorization to Operate (ATO) packages.
---

# Skill: Google Cloud DoD CC SRG Architecture Compliance Reviewer (IL2, IL4, IL5)

This skill provides an authoritative, specialized architectural review for Department of Defense (DoD), combatant commands, military services, defense agencies, and defense industrial base (DIB) partners building mission systems on Google Cloud Platform under the **DoD Cloud Computing Security Requirements Guide (CC SRG)**.

It focuses on three distinct mission tiers:
1. **DoD Impact Level 2 (IL2)**: Non-Controlled Unclassified Information (Non-CUI) and publicly releasable defense data.
2. **DoD Impact Level 4 (IL4)**: Controlled Unclassified Information (CUI), For Official Use Only (FOUO), defense health data (ePHI), and mission-critical unclassified systems.
3. **DoD Impact Level 5 (IL5)**: Higher-sensitivity CUI, National Security Systems (NSS) unclassified data, and mission-essential warfighter solutions.

---

## Workflow Overview

```
Phase 0: DoD Impact Level Scoping
   │  ├── Determine Target Impact Level: DoD IL2 vs. DoD IL4 vs. DoD IL5
   │  └── Confirm Assured Workloads DoD Folder & CONUS Location Enforcement
   ▼
Phase 1: Mission Architecture & Data Flow Ingestion
   │  ├── Map all GCP resources, VPC boundaries, databases, APIs, and AI/ML pipelines
   │  └── Identify any 3rd-party marketplace software, non-CONUS regions, or external SaaS dependencies
   ▼
Phase 2: DISA Provisional Authorization (PA) Services Audit
   │  ├── Cross-reference every proposed product against DISA PA scope for target IL
   │  └── Reject unapproved preview/beta services or unaccredited marketplace software
   ▼
Phase 3: DoD CC SRG Technical Controls Audit
   │  ├── Network & Perimeter: DISA CAP / BCAP interconnect, VPC-SC, private IPs
   │  ├── Cryptography: Cloud HSM FIPS 140-2 Level 3 CMEK, TLS 1.2+ Suite B ciphers
   │  ├── ICAM: DoD CAC / PKI authentication, Workload Identity, SA key generation banned
   │  ├── Personnel: Screened US Persons (IL4) / US Citizens (IL5), Access Approval & Transparency
   │  └── Audit & CSSP: Data Access logs (DATA_READ/WRITE), real-time streaming to DoD CSSP SIEM
   ▼
Phase 4: Synthesis & DoD SRG Compliance Report Generation
   └── Generate actionable report using templates/dod-review-report-template.md
```

---

## Phase 0: DoD Impact Level Scoping

If not specified, prompt the user via `ask_question`:
- **Target DoD Categorization**:
  - *DoD IL2*: Non-CUI / Public defense data (Commercial GCP regions).
  - *DoD IL4*: CUI, FOUO, PII, PHI in defense context, mission-critical systems (Assured Workloads IL4 regime mandatory).
  - *DoD IL5*: High-sensitivity CUI, NSS unclassified, mission-critical defense operations (Assured Workloads IL5 regime mandatory).
- **Assured Workloads Status**: Is the workload initialized within an Assured Workloads folder with the target DoD regime?

---

## Phase 1: Mission Architecture Ingestion

Extract and classify all system components:
1. **Compute & Containers**: Compute Engine, Google Kubernetes Engine (GKE), Cloud Run, Cloud Functions.
2. **Databases & Data Storage**: Cloud SQL, AlloyDB, BigQuery, Spanner, Cloud Storage.
3. **Hybrid Connectivity & Boundaries**: Dedicated Interconnect / Partner Interconnect to DISA CAP, VPC Service Controls, Cloud Armor.
4. **Security & Cryptography**: Assured Workloads, Cloud HSM, Cloud KMS, Secret Manager, Cloud IAM, Security Command Center.
5. **AI & Mission Analytics**: Vertex AI (core platform), Dataflow, Dataproc, Pub/Sub.

---

## Phase 2: DISA Provisional Authorization (PA) Services Audit

Verify every product against:
- Reference: [dod-srg-levels.md](references/dod-srg-levels.md)
- Official Documentation: `https://cloud.google.com/security/compliance/dod`
- DISA DoD CC SRG Portal: `https://cyber.mil/devsecops/cloud-computing-srg/`

### Strict Evaluation Rules:
1. **Mandatory Assured Workloads (IL4/IL5)**: Unmanaged commercial projects are strictly prohibited for IL4/IL5 data.
2. **CONUS Soil Only**: All resources must be provisioned in approved US continental regions (`us-central1`, `us-east4`, `us-west1`).
3. **No Unaccredited Marketplace / Third-Party Software**: Any third-party software deployed on VMs or GKE must hold independent DISA authorization or reciprocity.
4. **No Alpha/Beta/Preview Services**: Only Generally Available (GA) services covered by DISA PA are permitted.

---

## Phase 3: DoD CC SRG Technical Controls Audit

Audit the 5 foundational mission safeguards:

### 1. Network Perimeter & DISA CAP Connectivity
- For IL4 & IL5, interconnect directly with the **DISA Cloud Access Point (CAP / BCAP / ICAP)**.
- Deploy **VPC Service Controls (VPC-SC)** security perimeters around all managed data projects.
- Enforce private IPs only on all databases, GKE nodes, and compute instances; eliminate direct public IPv4 exposure.

### 2. Cryptographic Security & FIPS 140-2 Level 3
- Mandate **Customer-Managed Encryption Keys (CMEK)** generated exclusively within **Cloud HSM** (FIPS 140-2 Level 3 validated).
- Enforce TLS 1.2+ with approved FIPS ciphers on Cloud Load Balancing SSL policies.

### 3. Identity, Credential & Access Management (ICAM)
- Enforce DoD Common Access Card (CAC) / PKI hardware token MFA on all console and administrative sessions via Cloud Identity.
- Eliminate primitive IAM roles (`Owner`, `Editor`).
- Enforce **Workload Identity**; disable service account JSON key creation via organization policy `iam.disableServiceAccountKeyCreation`.

### 4. Personnel Security & Access Transparency
- Verify Assured Workloads constraints for **US Persons** (IL4) and **US Citizens** (IL5) Google support personnel.
- Enforce **Access Approval** for any Google operator access and monitor via **Access Transparency** logs.

### 5. Audit Logging & DoD CSSP Integration
- Enable comprehensive **Data Access audit logs** (`DATA_READ`, `DATA_WRITE`, `ADMIN_READ`).
- Export audit logs in real time to the designated **DoD Cybersecurity Service Provider (CSSP)** / SIEM.
- Enforce immutable archive storage using Cloud Storage **Bucket Lock (Object Retention)** in compliance mode.
- Enable **Security Command Center (SCC) Enterprise** for threat detection and posture management.

---

## Phase 4: Output Synthesis & Report Generation

Generate the review report using [dod-review-report-template.md](templates/dod-review-report-template.md).

Provide:
1. Clear Verdict (🟢 **Compliant**, 🟡 **Conditional**, 🔴 **Non-Compliant**).
2. DISA PA Services Matrix mapping services to IL2, IL4, and IL5.
3. DoD CC SRG Technical Controls Assessment.
4. Actionable Remediation Plan prioritized by ATC / ATO risk.
