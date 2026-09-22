# Google Cloud DoD Cloud Computing SRG Architecture Audit Report (IL2, IL4, IL5)

**DoD Component / Mission Partner:** {Command / Branch / Defense Agency Name}  
**System / Application Name:** {System Name}  
**Target DoD Impact Level:** {DoD IL2 / DoD IL4 / DoD IL5}  
**Review Date:** {Date}  
**Lead CE / Reviewer:** {Reviewer Name}  

---

## 1. Executive Summary & Verdict

| Audit Domain | Status | Key Findings |
| :--- | :---: | :--- |
| **Overall DoD SRG Verdict** | **{COMPLIANT / CONDITIONAL / NON-COMPLIANT}** | {High-level determination of DoD boundary readiness} |
| **DISA PA In-Scope Services** | **{X / Y Services Authorized}** | {Status of services authorized under DISA PA} |
| **Assured Workloads (IL4/IL5)** | **{PASS / ATTENTION / FAIL}** | {Status of DoD regime, CONUS region restrictions} |
| **DISA CAP / Boundary Defense** | **{PASS / ATTENTION / FAIL}** | {Interconnect to DISA CAP, VPC-SC, private IPs} |
| **Cryptographic Posture (FIPS 140-2 L3)** | **{PASS / ATTENTION / FAIL}** | {Cloud HSM CMEK enforcement and TLS 1.2+ Suite B} |
| **ICAM / CAC Authentication** | **{PASS / ATTENTION / FAIL}** | {DoD CAC/PKI MFA, Workload Identity, no SA keys} |
| **CSSP / Audit Logging** | **{PASS / ATTENTION / FAIL}** | {Data Access logs, SIEM export to DoD CSSP} |

### Verdict Definitions:
- 🟢 **COMPLIANT**: Workload resides within Assured Workloads (IL4/IL5), utilizes DISA PA-authorized services, and implements all DoD CC SRG technical controls (including Cloud HSM and DISA CAP integration).
- 🟡 **CONDITIONAL**: Services are authorized, but operational configurations (e.g. Cloud HSM key generation, CSSP log sink routing, or VPC-SC perimeter) must be configured prior to final Authorization to Connect (ATC).
- 🔴 **NON-COMPLIANT**: Workload violates CONUS location constraints, uses unauthorized commercial services, lacks FIPS 140-2 Level 3 hardware crypto, or connects directly to public internet without DISA CAP boundary for IL4/IL5.

---

## 2. DISA Provisional Authorization (PA) Services Matrix

| Architectural Tier | GCP Service | DISA PA Level (IL2/IL4/IL5) | Assured Workloads Enforced? | Replacement Guidance if Unauthorized |
| :--- | :--- | :---: | :---: | :--- |
| **Compute** | {Compute Engine / GKE} | IL2 / IL4 / IL5 | Yes | CONUS regions only |
| **Database** | {Cloud SQL / BigQuery} | IL2 / IL4 / IL5 | Yes | Private IP, Cloud HSM CMEK required |
| **Storage** | {Cloud Storage} | IL2 / IL4 / IL5 | Yes | UBLA, Bucket Lock compliance retention |
| **Networking** | {Cloud Interconnect} | IL2 / IL4 / IL5 | Yes | Connection to DISA CAP |
| **Analytics / AI** | {Vertex AI} | Core PA Services | Yes | Project boundary; no unapproved connectors |
| **Third-Party / Marketplace**| {Partner Tool} | ❌ | High Risk | Requires separate DISA PA / reciprocity |

---

## 3. DoD CC SRG Technical Requirements Checklist

### 3.1 Assured Workloads & Sovereign Isolation
- [ ] Assured Workloads folder created with target DoD regime (`DoD Impact Level 4` or `DoD Impact Level 5`).
- [ ] CONUS Location Restriction enforced (`us-central1`, `us-east4`, `us-west1`).
- [ ] US Persons (IL4) / US Citizens (IL5) support personnel constraints enforced.
- [ ] Access Approval and Access Transparency active for all Google operator actions.

### 3.2 Network Perimeter & DISA CAP Connectivity
- [ ] Dedicated/Partner Interconnect configured to connect to DISA Cloud Access Point (CAP / BCAP / ICAP) for IL4/IL5.
- [ ] Zero public IPv4 addresses assigned to internal database and compute instances.
- [ ] VPC Service Controls (VPC-SC) perimeter established around all managed data projects.
- [ ] Cloud Armor WAF deployed on authorized public ingress points (IL2/IL4).

### 3.3 Cryptography & FIPS 140-2 Level 3
- [ ] Customer-Managed Encryption Keys (CMEK) generated via **Cloud HSM** (FIPS 140-2 Level 3).
- [ ] TLS 1.2+ with approved FIPS ciphers enforced on all internal and external communication.
- [ ] Automated cryptographic key rotation policy defined in Cloud KMS.

### 3.4 Identity, Credential & Access Management (ICAM)
- [ ] DoD Common Access Card (CAC) / PKI hardware token MFA enforced via Cloud Identity.
- [ ] Workload Identity enforced for GKE and Cloud Run.
- [ ] Organization policy constraint `iam.disableServiceAccountKeyCreation` enforced.
- [ ] Primitive IAM roles (`Owner`, `Editor`) completely disabled.

### 3.5 Audit Logging & DoD CSSP Integration
- [ ] Data Access audit logs (`DATA_READ`, `DATA_WRITE`, `ADMIN_READ`) explicitly enabled on all services.
- [ ] Log sinks configured to stream real-time events to the designated DoD CSSP / SIEM.
- [ ] Immutable audit log archive maintained in Cloud Storage with Bucket Lock.
- [ ] Security Command Center (SCC) Enterprise enabled for threat detection and compliance.

---

## 4. Prioritized Remediation Action Plan

### Critical Blockers (ATC / ATO Denials)
1. **{Blocker 1}**: {Remediation description and technical instructions}
2. **{Blocker 2}**: {Remediation description and technical instructions}

### DoD Architecture Hardening
1. **{Recommendation 1}**: {Hardening configuration}
2. **{Recommendation 2}**: {Hardening configuration}

---

## 5. Official References & Artifacts
- Google Cloud DoD Offerings: [https://cloud.google.com/security/compliance/dod](https://cloud.google.com/security/compliance/dod)
- DISA Cloud Computing Security Requirements Guide: [https://cyber.mil/devsecops/cloud-computing-srg/](https://cyber.mil/devsecops/cloud-computing-srg/)
- Google Cloud Assured Workloads for DoD: [https://cloud.google.com/assured-workloads](https://cloud.google.com/assured-workloads)
