---
name: gcp-architecture-compliance
description: >-
  Audits Google Cloud Platform (GCP) architectures, diagrams, specs, and Terraform/IaC files for compliance
  against major regulatory frameworks including HIPAA, PCI DSS, FedRAMP (High/Moderate), SOC 2, ISO 27001,
  and HITRUST. Verifies that every proposed GCP product is officially eligible and covered under the relevant
  agreement (e.g., Google Cloud HIPAA BAA, FedRAMP boundary, PCI DSS AoC), detects unapproved third-party or
  preview services, flags configuration anti-patterns under the Shared Responsibility Model (such as disabled
  Data Access audit logs, public database IPs, or unencrypted endpoints), and generates an actionable compliance
  gap report with approved replacement services and remediation steps.
  Use when: reviewing an architecture for HIPAA compliance, verifying if GCP products are HIPAA-eligible,
  auditing architectures for PCI DSS or FedRAMP, checking compliance of a cloud design or Terraform plan,
  or preparing architecture compliance reports for customer reviews.
---

# Skill: GCP Architecture Compliance Validator

This skill enables Customer Engineers (CEs) and Cloud Architects to systematically validate any proposed or existing Google Cloud architecture against industry and regulatory compliance frameworks (such as **HIPAA**, **PCI DSS**, **FedRAMP**, **SOC 2**, **ISO 27001**, and **HITRUST**).

It evaluates architectures across two critical layers:
1. **Service Eligibility**: Enforces that all selected GCP products are officially covered under the governing framework agreement (e.g., Google Cloud HIPAA Business Associate Agreement, FedRAMP ATO boundary, PCI DSS Level 1 AoC).
2. **Architectural & Security Configuration Safeguards**: Audits technical controls under the **Shared Responsibility Model** (including Cloud Audit Logging, encryption at rest/in transit, VPC Service Controls, private endpoints, and IAM least privilege).

---

## Workflow Overview

```
Phase 0: Interactive Scoping & Intake (ask_question if framework/architecture is unspecified)
   │  ├── Identify Target Compliance Framework (HIPAA, PCI DSS, FedRAMP, etc.)
   │  └── Ingest Architecture Specification (Text description, Terraform/IaC, Diagram, or File)
   ▼
Phase 1: Architectural Component & Service Extraction
   │  ├── Enumerate all GCP services, APIs, databases, compute, networking, and analytics
   │  └── Identify any 3rd-party marketplace, SaaS, or hybrid integrations
   ▼
Phase 2: Service Eligibility & Boundary Verification
   │  ├── Cross-reference extracted services against framework eligible lists in references/
   │  └── Verify live Google Cloud compliance documentation for newly released or preview features
   ▼
Phase 3: Shared Responsibility & Configuration Safeguard Audit
   │  ├── Data Protection & Cryptography (CMEK, TLS 1.2+)
   │  ├── Network Isolation & Perimeter Defense (VPC-SC, Private Service Connect, Cloud Armor)
   │  ├── Identity & Access Management (Least privilege, Workload Identity, MFA)
   │  └── Audit Logging (Data Access audit logs for DATA_READ / DATA_WRITE)
   ▼
Phase 4: Synthesis & Compliance Assessment Report
   └── Generate actionable report using templates/architecture-compliance-report-template.md
```

---

## Phase 0: Interactive Scoping & Intake

If the user has not explicitly specified both the **target compliance framework** and the **architecture details**, interactively prompt them using `ask_question`:

```json
{
  "questions": [
    {
      "question": "Which compliance framework should this GCP architecture be audited against?",
      "options": [
        "(Recommended) HIPAA (Health Insurance Portability and Accountability Act - BAA)",
        "PCI DSS 4.0 (Payment Card Industry Data Security Standard - Level 1)",
        "FedRAMP High / Moderate (Federal Risk and Authorization Management Program)",
        "SOC 2 Type II (Security, Availability, Confidentiality, Privacy)",
        "ISO/IEC 27001:2022 (Information Security Management System)",
        "Multiple Frameworks (Comprehensive Multi-Regulatory Audit)"
      ],
      "is_multi_select": false
    },
    {
      "question": "How will you provide the architecture for compliance review?",
      "options": [
        "(Recommended) Provide / Paste Architecture description or list of GCP services",
        "Point to Terraform / IaC files or repo in the workspace",
        "Upload or provide an architecture diagram image",
        "Review an existing architecture proposal or document"
      ],
      "is_multi_select": false
    }
  ]
}
```

If the user prompt already states the framework (e.g., *"Is this architecture HIPAA compliant?"*) and provides the services/architecture, proceed immediately to Phase 1.

---

## Phase 1: Architectural Component & Service Extraction

1. **Parse Architecture Inputs**:
   - Extract all mentioned Google Cloud products and services (e.g., *Cloud Run, BigQuery, Cloud SQL, Cloud Storage, Vertex AI, Pub/Sub, Cloud Functions, GKE, Looker, etc.*).
   - Extract data stores and types of data ingested (PHI, PII, Cardholder Data, CUI, general enterprise data).
   - Identify network topologies: Public vs. Private IPs, Load Balancers, Cloud Armor WAF, VPN/Interconnect, VPC Service Controls perimeters.
   - Flag any **third-party SaaS, marketplace tools, external APIs**, or **unmanaged compute agents**.

2. **Categorize Components by Service Layer**:
   - Compute & Orchestration (GKE, Cloud Run, Compute Engine, Batch)
   - Storage & Databases (Cloud Storage, Cloud SQL, AlloyDB, BigQuery, Spanner, Firestore)
   - Networking & Perimeter (VPC, Cloud Armor, Cloud Load Balancing, Cloud NAT, PSC)
   - Security & Identity (Cloud IAM, Cloud KMS, Secret Manager, SCC, IAP)
   - Analytics, AI & Integration (Vertex AI, Dataflow, Dataproc, Pub/Sub, Sensitive Data Protection)

---

## Phase 2: Service Eligibility & Boundary Verification

Cross-reference each extracted GCP product against the framework's official eligibility list using the local reference guides:
- **HIPAA**: [hipaa-eligible-services.md](references/hipaa-eligible-services.md)
- **PCI DSS**: [pci-dss-eligible-services.md](references/pci-dss-eligible-services.md)
- **FedRAMP**: [fedramp-eligible-services.md](references/fedramp-eligible-services.md)
- **Master Overview**: [compliance-frameworks-overview.md](references/compliance-frameworks-overview.md)

### Verification Rules:
1. **Generally Available (GA) vs. Preview / Alpha**:
   - Pre-GA (Alpha, Beta, Preview) products are **NOT covered** under Google Cloud's HIPAA BAA, FedRAMP ATO, or standard compliance attestations.
   - Any service in Preview handling regulated data must be marked as **Ineligible / Non-Compliant**.
2. **Third-Party Marketplace Products**:
   - Google Cloud's BAA and compliance certificates cover **Google-first-party services only**.
   - Third-party virtual appliances or marketplace software (e.g., Snowflake on GCP, Confluent, third-party database images) require a direct BAA or compliance agreement between the customer and the vendor.
3. **External Connectors & Web Extensions**:
   - Vertex AI search extensions or RAG connectors that query non-compliant external internet sources violate data boundary constraints if regulated data is transmitted.
4. **Live Verification**:
   - If a proposed service is newly released or ambiguous, verify current eligibility using official documentation:
     - HIPAA: `https://cloud.google.com/security/compliance/hipaa`
     - PCI DSS: `https://cloud.google.com/security/compliance/pci-dss`
     - FedRAMP: `https://cloud.google.com/security/compliance/fedramp`

---

## Phase 3: Shared Responsibility & Configuration Safeguard Audit

Even if 100% of services are eligible, check for critical architecture and configuration anti-patterns across the **7 Foundational Safeguards**:

### 1. Governing Agreement & Boundary Enforcement
- Is the formal agreement (e.g. HIPAA BAA) required prior to workload deployment?
- Is **Assured Workloads** configured to enforce organization policies (e.g., location restrictions, CMEK enforcement, blocking non-compliant services)?

### 2. Encryption at Rest & In Transit
- **At Rest**: Is default AES-256 sufficient, or is **Customer-Managed Encryption Keys (CMEK)** via Cloud KMS / Cloud HSM required for regulatory isolation?
- **In Transit**: Is TLS 1.2+ strictly enforced? Are weak ciphers disabled on Cloud Load Balancing SSL policies? Are internal microservice calls encrypted (mTLS / internal HTTPS)?

### 3. Network Perimeter & Ingress/Egress Isolation
- **Private Endpoints Only**: Do all databases (Cloud SQL, AlloyDB, Bigtable) and backend compute run on Private IPs with zero public IPv4 addresses?
- **VPC Service Controls**: Is a perimeter deployed around sensitive data stores (Cloud Storage, BigQuery) to prevent data exfiltration?
- **WAF & Ingress Defense**: Is **Cloud Armor** deployed on public HTTP(S) entry points to mitigate OWASP Top 10 vulnerabilities and DDoS?

### 4. Identity & Access Management (IAM)
- Are primitive roles (`Owner`, `Editor`, `Viewer`) eliminated in favor of least-privilege predefined or custom roles?
- Is Multi-Factor Authentication (MFA) and Context-Aware Access enforced for all users?
- Are Service Account keys disabled in favor of **Workload Identity** (GKE / Cloud Run / external federation)?

### 5. Audit Logging & Retention (Critical HIPAA/PCI Blocker)
- > [!CAUTION]
  > **High Severity Anti-Pattern**: In Google Cloud, **Data Access audit logs** (`DATA_READ`, `DATA_WRITE`, `ADMIN_READ`) are **DISABLED by default** for most services (except BigQuery). For HIPAA § 164.312(b) and PCI DSS Req 10 compliance, Data Access logs **must be explicitly enabled**.
- Are audit logs exported to a tamper-resistant, locked Cloud Storage bucket (with Bucket Lock) or BigQuery dataset with required retention periods (e.g., 6+ years for HIPAA, 1+ year for PCI DSS)?

### 6. Sensitive Data Discovery & De-identification
- Is **Sensitive Data Protection (Cloud DLP)** used to scan, mask, or tokenize sensitive identifiers before passing data to analytics or ML pipelines?
- For healthcare data, is the **Cloud Healthcare API** de-identification pipeline used?

### 7. Backup, Disaster Recovery & High Availability
- Are automated backups and point-in-time recovery (PITR) configured?
- Is multi-region or dual-region resilience in place for critical regulated data stores?

---

## Phase 4: Output Synthesis & Report Generation

Generate a structured compliance assessment report based on [architecture-compliance-report-template.md](templates/architecture-compliance-report-template.md).

The report must contain:
1. **Executive Summary & Verdict**:
   - 🟢 **COMPLIANT**: All services eligible and all required architectural controls architected.
   - 🟡 **CONDITIONAL**: All services eligible, but specific technical controls (e.g., Data Access logs, private IPs, CMEK) must be configured prior to production.
   - 🔴 **NON-COMPLIANT**: Ineligible services detected, or severe architectural anti-patterns (e.g., public database IPs, unmanaged 3rd-party data leaks).
2. **Service Eligibility Matrix**:
   - Table of every evaluated service, eligibility status (✅ / ❌), and recommended approved replacement for any non-compliant component.
3. **Architectural Safeguards Checklist**:
   - Evaluation of Cryptography, Network Isolation, IAM, Audit Logging, and Data Governance.
4. **Remediation Action Plan**:
   - Prioritized list of actionable changes (High Priority Blockers vs Medium Priority Hardening).
5. **Official Google Cloud References & Documentation Links**.

---

## Phase 5: Approved Service Substitutions (Remediation Cheat Sheet)

When non-compliant components are detected, suggest standard Google Cloud approved alternatives:

| Detected Ineligible / Risky Component | Approved Compliant Alternative | Rationale & Guidance |
| :--- | :--- | :--- |
| **Self-hosted database on public VM** | **Cloud SQL / AlloyDB with Private IP** | Managed BAA coverage, automated patching, private VPC peering. |
| **Third-Party unmanaged Kafka on VMs** | **Cloud Pub/Sub** or **Managed Service for Apache Kafka** | Fully covered under Google Cloud BAA, integrated IAM, encrypted by default. |
| **Direct Card/PHI storage in text fields** | **Sensitive Data Protection (DLP) Tokenization** | De-identifies and tokenizes sensitive data before storage, significantly reducing audit scope. |
| **Public IP on Compute/Database** | **Private Service Connect (PSC) / Cloud NAT / IAP** | Eliminates direct internet exposure while enabling controlled, audited connectivity. |
| **External non-BAA AI API** | **Vertex AI Gemini API** (within Google Cloud project) | Covered under enterprise data governance and Google Cloud BAA commitments. |
| **Unrestricted Cloud Storage Bucket** | **Uniform Bucket-Level Access + Public Access Prevention** | Enforces organizational IAM policy and prevents accidental public data exposure. |

---

## Success Criteria Checklist

When completing a compliance assessment, verify:
- [ ] Target compliance framework is clearly identified (HIPAA, PCI DSS, FedRAMP, etc.).
- [ ] Every proposed GCP product in the architecture has been evaluated for eligibility.
- [ ] Ineligible, preview, or 3rd-party marketplace services have been flagged with approved replacements.
- [ ] Shared Responsibility controls have been evaluated (specifically Data Access audit logging and private network boundaries).
- [ ] Clear verdict (Compliant / Conditional / Non-Compliant) is provided with an executive summary.
- [ ] Actionable remediation steps are documented using the standard report template.
