# HIPAA Security Rule Technical Safeguards (§ 164.312) on Google Cloud

## Overview

The Health Insurance Portability and Accountability Act (HIPAA) Security Rule establishes national standards to protect individuals' electronic Protected Health Information (ePHI) created, received, used, or maintained by a covered entity or business associate.

This reference provides a mapping between **HIPAA Security Rule § 164.312 Technical Safeguards** and Google Cloud architectural implementations.

---

## 1. § 164.312(a)(1) Access Control

A covered entity or business associate must implement technical policies and procedures for electronic information systems that maintain ePHI to allow access only to those persons or software programs that have been granted access rights.

| HIPAA Specification | Requirement Level | Google Cloud Technical Implementation |
| :--- | :--- | :--- |
| **Unique User Identification** (§ 164.312(a)(2)(i)) | **Required** | • Enforce Google Cloud Identity / Workspace corporate user accounts.<br>• Ban shared generic accounts (`admin@company.com`).<br>• Enforce Multi-Factor Authentication (MFA) on all admin accounts.<br>• Leverage GKE Workload Identity / Cloud Run Service Accounts rather than static API keys. |
| **Emergency Access Procedure ("Break-Glass")** (§ 164.312(a)(2)(ii)) | **Required** | • Pre-stage dedicated break-glass service accounts with elevated permissions stored in Secret Manager.<br>• Alert instantly on break-glass invocation via Cloud Monitoring & Security Command Center (SCC). |
| **Automatic Logoff** (§ 164.312(a)(2)(iii)) | **Addressable** | • Configure session timeouts on Google Cloud Console and web apps via Identity-Aware Proxy (IAP) session lifetime controls (e.g., 15-30 minutes). |
| **Encryption and Decryption** (§ 164.312(a)(2)(iv)) | **Addressable** | • All data at rest is encrypted by default with AES-256.<br>• For customer control and key revocation, enforce **Customer-Managed Encryption Keys (CMEK)** via Cloud KMS or Cloud HSM. |

---

## 2. § 164.312(b) Audit Controls (Critical GCP Vulnerability Area)

Implement hardware, software, and/or procedural mechanisms that record and examine activity in information systems that contain or use electronic protected health information.

> [!CAUTION]
> **CRITICAL GCP DEFAULT CONFIGURATION ALERT**:
> In Google Cloud, **Admin Activity** audit logs are enabled by default and cannot be disabled.
> However, **Data Access audit logs** (`DATA_READ`, `DATA_WRITE`, `ADMIN_READ`) are **DISABLED BY DEFAULT** for almost all services (except BigQuery).
> 
> **Failing to explicitly enable Data Access audit logs on Cloud Storage, Cloud SQL, AlloyDB, and Cloud Healthcare API constitutes an automatic failure of HIPAA § 164.312(b).**

### Required Logging Configuration:
1. **Enable Data Access Logs**:
   In IAM & Admin > Audit Logs, enable `DATA_READ`, `DATA_WRITE`, and `ADMIN_READ` for:
   - `storage.googleapis.com` (Cloud Storage)
   - `cloudsql.googleapis.com` (Cloud SQL)
   - `bigquery.googleapis.com` (BigQuery)
   - `healthcare.googleapis.com` (Cloud Healthcare API)
   - `secretmanager.googleapis.com` (Secret Manager)
   - `cloudkms.googleapis.com` (Cloud KMS)
2. **Log Immobility & Retention (6+ Years)**:
   - Export Cloud Logging sinks to a dedicated, restricted security audit project.
   - Store in a Cloud Storage bucket configured with **Bucket Lock (Retention Policy)** set to compliance mode for 6 or 7 years (per state/federal requirement) to prevent premature deletion.

---

## 3. § 164.312(c)(1) Integrity

Implement policies and procedures to protect electronic protected health information from improper alteration or destruction.

| HIPAA Specification | Requirement Level | Google Cloud Technical Implementation |
| :--- | :--- | :--- |
| **Mechanism to Authenticate ePHI** (§ 164.312(c)(2)) | **Addressable** | • Cloud Storage Object Versioning and Object Retention (Bucket Lock).<br>• MD5 / CRC32c automatic checksum verification on all Cloud Storage uploads and downloads.<br>• Database point-in-time recovery (PITR) and automated daily snapshots on Cloud SQL / AlloyDB. |

---

## 4. § 164.312(d) Person or Entity Authentication

Implement procedures to verify that a person or entity seeking access to electronic protected health information is the one claimed.

- **Human Users**: Cloud Identity SAML / OIDC federation with enterprise IdP (Okta, Azure AD, Ping), hardware security keys (FIDO2 / WebAuthn), and context-aware device policies via BeyondCorp Enterprise.
- **Service-to-Service**: Mutual TLS (mTLS) with Certificate Authority Service (CAS), Workload Identity Federation, and OAuth 2.0 access tokens with 1-hour lifetimes.

---

## 5. § 164.312(e)(1) Transmission Security

Implement technical security measures to guard against unauthorized access to electronic protected health information that is being transmitted over an electronic communications network.

| HIPAA Specification | Requirement Level | Google Cloud Technical Implementation |
| :--- | :--- | :--- |
| **Integrity Controls** (§ 164.312(e)(2)(i)) | **Addressable** | • TLS 1.2 or TLS 1.3 enforced on Cloud Load Balancing SSL Policies (disable TLS 1.0, 1.1, and CBC ciphers).<br>• Cloud VPN with IPsec (IKEv2) or Cloud Interconnect with MACsec for on-premises hybrid traffic. |
| **Encryption** (§ 164.312(e)(2)(ii)) | **Addressable** | • Zero Public IPs on database and application worker tiers.<br>• Use **Private Service Connect (PSC)** or Private Google Access for accessing Google APIs privately.<br>• Deploy **VPC Service Controls (VPC-SC)** perimeter around all data lake and analytics projects containing ePHI. |

---

## 6. Healthcare-Specific Data Governance & De-Identification

- **Cloud Healthcare API**: Provides managed FHIR, HL7v2, and DICOM stores with built-in de-identification profiles conforming to HIPAA Safe Harbor (stripping the 18 identifier classes) or Expert Determination.
- **Sensitive Data Protection (Cloud DLP)**: Continuous inspection of unstructured data, medical notes, and logs to redact or pseudonymize accidental PHI before data leaves the secure enclave.
- **Assured Workloads (HIPAA Regime)**: Automatically configures organization policy constraints preventing non-BAA service usage and enforcing US location boundaries.
