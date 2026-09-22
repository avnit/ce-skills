---
name: gcp-pci-compliance
description: >-
  Specialized architectural review skill for Google Cloud Platform (GCP) payment processing and financial
  workloads under the Payment Card Industry Data Security Standard (PCI DSS 4.0). Audits Cardholder Data
  Environment (CDE) segmentation, enforces scope minimization strategies (tokenization, hosted payment fields),
  verifies Google Cloud PCI DSS Level 1 Service Provider in-scope services, and systematically reviews architecture
  against PCI DSS 4.0 requirements. Checks Cloud Armor WAF deployment (Req 6.4.2), PAN encryption and tokenization
  via Cloud KMS/HSM (Req 3), SAD storage elimination (CVV post-auth prohibition), TLS 1.2+ ciphers (Req 4),
  Zero Trust MFA access via Identity-Aware Proxy (Req 7/8), and mandatory 1-year audit log retention (Req 10).
  Use when: auditing architectures for PCI DSS compliance, reviewing cardholder data environments (CDE),
  evaluating payment gateways or tokenization on GCP, or preparing PCI DSS gap analysis reports.
---

# Skill: Google Cloud PCI DSS 4.0 Architecture Compliance Reviewer

This skill provides an authoritative, specialized architectural review for payment applications and financial workloads storing, processing, or transmitting **Cardholder Data (CHD)** or **Sensitive Authentication Data (SAD)** on Google Cloud Platform under **PCI DSS v4.0**.

It structures evaluation around the two fundamental tenets of cloud payment architecture:
1. **Scope Minimization & Isolation**: Architecting to shrink or isolate the Cardholder Data Environment (CDE) boundary through tokenization, hosted fields, and strict VPC perimeter segmentation.
2. **PCI DSS 4.0 Technical Requirements Compliance**: Auditing Google Cloud services and configurations against Requirements 1 through 12.

---

## Workflow Overview

```
Phase 0: Scope Intake & SAQ Level Identification
   │  ├── Determine Merchant/Service Provider level & target SAQ (SAQ A, SAQ A-EP, SAQ D)
   │  └── Define Cardholder Data Environment (CDE) boundary
   ▼
Phase 1: Payment Flow & Architecture Ingestion
   │  ├── Trace the life of a credit card transaction from user ingress to settlement
   │  └── Enumerate all GCP compute, storage, networking, database, and logging components
   ▼
Phase 2: Google Cloud PCI DSS Level 1 Verification
   │  ├── Validate all in-scope services against Google Cloud's Level 1 Service Provider AoC
   │  └── Flag any unapproved third-party software, unmanaged VM appliances, or preview APIs
   ▼
Phase 3: PCI DSS 4.0 Technical Requirements Audit
   │  ├── Req 1 & 2: Network Security & Boundary (CDE VPC isolation, Cloud Armor WAF)
   │  ├── Req 3: Account Data Protection (No SAD storage, PAN encryption with Cloud HSM, Tokenization)
   │  ├── Req 4: Transmission Security (TLS 1.2+ with PFS ciphers on Cloud Load Balancing)
   │  ├── Req 6: Secure Systems (Artifact Registry vulnerability scanning, VM patching)
   │  ├── Req 7 & 8: Access Control & IAM (MFA required for CDE, IAP zero trust, no SA keys)
   │  └── Req 10 & 11: Audit Logging & Monitoring (1-year log retention, VPC Flow Logs, SCC)
   ▼
Phase 4: Synthesis & PCI DSS Audit Report Generation
   └── Generate actionable report using templates/pci-review-report-template.md
```

---

## Phase 0: Scope Intake & SAQ Classification

If not specified, prompt the user via `ask_question` to determine:
- **Payment Handling Method**:
  - *Option 1 (SAQ A)*: Fully outsourced / hosted fields (Stripe/Adyen iframe). Zero card data touches GCP servers.
  - *Option 2 (SAQ A-EP)*: Merchant website generates payment page and transmits card data via direct API calls to payment processor.
  - *Option 3 (SAQ D / Level 1 Service Provider)*: Direct ingestion, storage, or tokenization of Primary Account Numbers (PAN).

---

## Phase 1: Payment Flow & Architecture Component Ingestion

1. **Map Ingress & Application Tier**:
   - Cloud Load Balancing, Cloud Armor WAF, GKE, Cloud Run, Compute Engine.
2. **Map Database & Cryptographic Tier**:
   - Cloud SQL, AlloyDB, Spanner, Firestore, Cloud KMS / Cloud HSM, Secret Manager.
3. **Trace Data Elements**:
   - Primary Account Number (PAN)
   - Sensitive Authentication Data (SAD): Card Verification Value (CVV/CVC), PIN, full track data.
   - Tokenized representation / customer metadata.

---

## Phase 2: Google Cloud PCI DSS Level 1 Verification

Cross-reference services against:
- Reference: [pci-dss-4-checklist.md](references/pci-dss-4-checklist.md)
- Official Documentation: `https://cloud.google.com/security/compliance/pci-dss`
- Artifact Repository: Google Cloud Attestation of Compliance (AoC) via [Compliance Reports Manager](https://cloud.google.com/compliance/reports-manager).

---

## Phase 3: PCI DSS 4.0 Technical Requirements Audit

### 1. Req 1 & 2: Network Security Controls
- **CDE Isolation**: CDE must reside in an isolated VPC or standalone GCP project, segmented from general corporate networks.
- **Cloud Armor WAF**: Mandatory for Requirement 6.4.2 on public-facing web applications.
- **Zero Public IPs**: Databases and backend APIs must be private-only via Private Service Connect.

### 2. Req 3 & 4: Account Data Protection & Cryptography
- > [!CAUTION]
  > **Strict PCI Prohibition**: **NEVER store Sensitive Authentication Data (SAD / CVV / PIN)** after authorization, even if encrypted. Storing post-authorization CVV is an automatic, non-negotiable audit failure.
- **PAN Encryption**: If PAN is stored, enforce AES-256 via **Cloud HSM** (FIPS 140-2 Level 3 validated).
- **Tokenization**: Employ Sensitive Data Protection (Cloud DLP) Format-Preserving Encryption (FPE) to replace PANs with surrogate tokens before storing in analytics or general databases.
- **Transmission**: Enforce TLS 1.2+ with modern cipher suites; block legacy TLS 1.0/1.1.

### 3. Req 7 & 8: Access Control & MFA
- Enforce Multi-Factor Authentication (MFA) on all administrative access into the CDE.
- Gated terminal access via **Identity-Aware Proxy (IAP)**; eliminate direct public SSH/RDP.
- Disable service account key downloads via organization policy.

### 4. Req 10 & 11: Audit Trails & Threat Detection
- Enable Cloud Audit Logs (Admin Activity + Data Access logs for CDE data stores).
- Retain audit logs for at least **1 year** (at least **3 months immediately available**).
- Enable **Security Command Center (SCC)** and **VPC Flow Logs** for traffic anomaly detection.

---

## Phase 4: Output Synthesis & Report Generation

Generate a structured audit report based on [pci-review-report-template.md](templates/pci-review-report-template.md).

Include:
- Clear Verdict (🟢 **Compliant**, 🟡 **Conditional**, 🔴 **Non-Compliant**).
- CDE Scope Reduction recommendations.
- PCI DSS 4.0 Requirements evaluation grid.
- Prioritized remediation plan (Immediate Blockers vs. Hardening).
