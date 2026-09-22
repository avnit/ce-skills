---
name: gcp-hipaa-compliance
description: >-
  Specialized architectural review skill for Google Cloud Platform (GCP) healthcare solutions handling
  Protected Health Information (PHI) under HIPAA and HITECH. Verifies 100% eligibility of proposed GCP
  services under Google Cloud's Business Associate Agreement (BAA), detects ineligible Preview/Alpha or
  third-party components, and audits adherence to HIPAA Security Rule Technical Safeguards (§ 164.312).
  Specifically enforces mandatory Data Access audit logging (DATA_READ/DATA_WRITE), private network
  perimeters (VPC Service Controls, Private Service Connect, zero public IPs on databases), Customer-Managed
  Encryption Keys (CMEK), Assured Workloads HIPAA regime, and Safe Harbor de-identification pipelines using
  Cloud Healthcare API and Sensitive Data Protection (Cloud DLP).
  Use when: reviewing an architecture for HIPAA compliance, verifying HIPAA BAA eligibility for GCP products,
  auditing healthcare architectures for PHI protection, or preparing HIPAA compliance gap reports for customers.
---

# Skill: Google Cloud HIPAA Architecture Compliance Reviewer

This skill provides a deep-dive, specialized architectural review for workloads storing, processing, or transmitting **Protected Health Information (ePHI)** on Google Cloud Platform under the **Health Insurance Portability and Accountability Act (HIPAA)**.

It evaluates designs across two core levels:
1. **Google Cloud BAA Eligibility**: Enforces that all services are Generally Available (GA) and covered under Google's formal Business Associate Agreement.
2. **HIPAA Security Rule Technical Safeguards (§ 164.312)**: Audits implementation of Access Control, Audit Controls, Integrity, Transmission Security, and Data De-identification.

---

## Workflow Overview

```
Phase 0: Healthcare Workload Scoping
   │  ├── Determine Workload Type (Clinical app, EHR integration, Analytics/Lakehouse, AI/ML, Medical Imaging)
   │  └── Confirm BAA Status & Target GCP Organization
   ▼
Phase 1: Architecture & Data Flow Component Ingestion
   │  ├── Map all GCP services, APIs, databases, pipelines, and AI models
   │  └── Identify any 3rd-party marketplace software, external APIs, or SaaS dependencies
   ▼
Phase 2: Google BAA Service Eligibility Verification
   │  ├── Check each product against HIPAA BAA eligible list
   │  └── Flag any pre-GA (Alpha/Beta/Preview) features or un-covered third-party marketplace tools
   ▼
Phase 3: HIPAA § 164.312 Technical Safeguards Audit
   │  ├── § 164.312(a)(1) Access Control (IAM least privilege, Workload Identity, Break-glass)
   │  ├── § 164.312(b) Audit Controls (CRITICAL: Data Access audit logs DATA_READ/DATA_WRITE)
   │  ├── § 164.312(c)(1) Integrity (Object versioning, PITR, checksums)
   │  ├── § 164.312(d) Person/Entity Authentication (MFA, BeyondCorp, CAS mTLS)
   │  ├── § 164.312(e)(1) Transmission Security (TLS 1.2+, Private Service Connect, VPC-SC)
   │  └── Healthcare Data Governance (Cloud Healthcare API FHIR/DICOM, Cloud DLP Safe Harbor)
   ▼
Phase 4: Synthesis & HIPAA Audit Report Generation
   └── Generate actionable report using templates/hipaa-review-report-template.md
```

---

## Phase 0: Healthcare Workload Scoping

If the user has not provided complete architecture context, use `ask_question` to determine:
- **Workload Profile**: Clinical application, Patient portal, Health data lakehouse (BigQuery), Vertex AI medical diagnostics, or FHIR/HL7 integration.
- **BAA Execution**: Has the organization executed Google Cloud's BAA? Is **Assured Workloads (HIPAA)** enabled?

---

## Phase 1: Architecture & Data Flow Ingestion

Extract all components from the user's prompt, Terraform, or diagram:
1. **Data Ingestion Tier**: Cloud Storage, Cloud Healthcare API (FHIR / HL7v2 / DICOM), Pub/Sub, Transfer Appliance.
2. **Compute & Processing**: Cloud Run, GKE (Autopilot/Standard), Cloud Functions, Compute Engine, Dataflow.
3. **Storage & Data Lake**: Cloud SQL (MySQL, PostgreSQL, SQL Server), AlloyDB, BigQuery, Spanner, Bigtable, Cloud Storage.
4. **Analytics & AI**: Vertex AI (Custom Training, Prediction endpoints, Gemini API within project boundary), Looker.
5. **Perimeter & Security**: Cloud KMS, Secret Manager, Cloud Armor, VPC Service Controls, Private Service Connect.
6. **Third-Party Integrations**: Highlight any non-Google SaaS, Marketplace VMs, or public web connectors.

---

## Phase 2: Google BAA Service Eligibility Verification

Evaluate every service against the authoritative reference guide:
- Reference: [hipaa-technical-safeguards.md](references/hipaa-technical-safeguards.md)
- Official Live URL: `https://cloud.google.com/security/compliance/hipaa`

### Strict Evaluation Rules:
1. **Pre-GA Exclusion**: Any feature in **Alpha, Beta, or Public Preview** is **strictly ineligible** to store or process ePHI under Google's BAA.
2. **Third-Party Marketplace Software**: Google's BAA covers Google-first-party services only. Third-party database or security appliances require an independent BAA executed directly between the customer and that vendor.
3. **Vertex AI Search & Extensions**: Restrict AI/RAG architectures to internal VPC-SC bounded BigQuery/Cloud Storage. Querying unvetted external web sources with PHI violates data boundaries.

---

## Phase 3: HIPAA Security Rule (§ 164.312) Audit

Audit the 5 core technical safeguards:

### 1. § 164.312(a)(1) Access Control
- Eliminate primitive IAM roles (`Owner`, `Editor`).
- Enforce **Workload Identity** on GKE and Cloud Run; forbid service account JSON key file downloads.
- Document and configure emergency access ("break-glass") service accounts.

### 2. § 164.312(b) Audit Controls (Critical GCP Vulnerability)
- > [!CAUTION]
  > **High Severity Anti-Pattern**: In Google Cloud, **Data Access audit logs** (`DATA_READ`, `DATA_WRITE`, `ADMIN_READ`) are **DISABLED BY DEFAULT** for almost all services (except BigQuery). Failing to explicitly enable them on Cloud Storage, Cloud SQL, AlloyDB, and Cloud Healthcare API is an automatic HIPAA violation.
- Confirm audit log export sinks to a locked Cloud Storage bucket with **Bucket Lock (Object Retention)** set to compliance mode for at least 6 years.

### 3. § 164.312(c)(1) Integrity
- Enforce Cloud Storage Object Versioning.
- Require automated daily backups and point-in-time recovery (PITR) for all databases.

### 4. § 164.312(e)(1) Transmission Security & Boundary Defense
- **Zero Public Exposure**: Cloud SQL, AlloyDB, and GKE nodes must have private IPs only (Private Service Connect / Private Google Access).
- **VPC Service Controls**: Perimeter must encircle Cloud Storage, BigQuery, and Vertex AI.
- **TLS 1.2+**: Enforce modern SSL policies with ECDHE ciphers on external Cloud Load Balancers.

### 5. Healthcare Data Governance & De-identification
- Implement **Sensitive Data Protection (Cloud DLP)** to mask or tokenize PHI before loading into analytics or ML.
- Use **Cloud Healthcare API** de-identification profiles conforming to HIPAA Safe Harbor (stripping 18 identifier types) for medical imaging (DICOM) or clinical records (FHIR).

---

## Phase 4: Output Synthesis & Report Generation

Generate a comprehensive review artifact using [hipaa-review-report-template.md](templates/hipaa-review-report-template.md).

Provide:
1. Clear Verdict (🟢 **Compliant**, 🟡 **Conditional**, 🔴 **Non-Compliant**).
2. Service Eligibility Matrix with approved alternatives for any flagged services.
3. § 164.312 Technical Safeguards Checklist.
4. Concrete Remediation Steps prioritized by urgency (Blockers vs. Hardening).
