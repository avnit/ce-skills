# DoD Cloud Computing Security Requirements Guide (SRG) on Google Cloud: IL2, IL4 & IL5

## Overview

The Defense Information Systems Agency (DISA) publishes the **DoD Cloud Computing Security Requirements Guide (CC SRG)**, defining the baseline security requirements for cloud services hosting Department of Defense (DoD) information, mission applications, and data.

Google Cloud holds DISA **Provisional Authorizations (PA)** across three critical Impact Levels:
- **Impact Level 2 (IL2)**: Non-Controlled Unclassified Information (Non-CUI).
- **Impact Level 4 (IL4)**: Controlled Unclassified Information (CUI) & Mission Critical Unclassified Data.
- **Impact Level 5 (IL5)**: National Security Systems (NSS) Unclassified Data & Higher-Sensitivity CUI.

Official Google Cloud DoD Guidance: [https://cloud.google.com/security/compliance/dod](https://cloud.google.com/security/compliance/dod)

---

## 1. DoD Impact Level Comparison Matrix

| Impact Level | Data Classification | FedRAMP Baseline Equivalent | Location & Physical Separation Requirements | Google Cloud Delivery Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **DoD IL2** | • Publicly releasable DoD data<br>• Non-CUI / Non-critical unclassified info | FedRAMP Moderate | Standard commercial Google Cloud US multi-tenant regions. | Commercial Google Cloud with standard organization policies. |
| **DoD IL4** | • Controlled Unclassified Information (CUI)<br>• Personally Identifiable Information (PII)<br>• Protected Health Information (PHI)<br>• Non-NSS Mission-Critical systems | FedRAMP High + DoD IL4 Overlays | • US Soil Only (CONUS).<br>• Logical isolation & crypto-segmentation.<br>• Screened US Persons for operations & support. | **Google Cloud Assured Workloads** configured with **DoD Impact Level 4 (IL4)** regime. |
| **DoD IL5** | • National Security Systems (NSS) Unclassified data<br>• Higher-sensitivity CUI<br>• Defense critical infrastructure | FedRAMP High + DoD IL5 Overlays | • US Soil Only (CONUS).<br>• Enhanced logical/physical isolation.<br>• Screened US Citizens for all support/operations.<br>• Dedicated cryptographic hardware (Cloud HSM). | **Google Cloud Assured Workloads** configured with **DoD Impact Level 5 (IL5)** regime. |

---

## 2. Assured Workloads: Mandatory for IL4 and IL5

> [!IMPORTANT]
> **Mandatory Architecture Requirement for IL4 & IL5**:
> Any architecture handling DoD IL4 or IL5 data **must** be deployed within a **Google Cloud Assured Workloads** folder configured with the corresponding regime:
> - `DoD Impact Level 4`
> - `DoD Impact Level 5`
> 
> Assured Workloads automatically:
> 1. Enforces the **Resource Location Restriction** constraint, limiting resource provisioning strictly to authorized US CONUS regions (e.g. `us-central1`, `us-east4`, `us-west1`).
> 2. Blocks non-DISA-authorized services from provisioning.
> 3. Enforces **US Persons / US Citizens** support personnel access restrictions.
> 4. Restricts encryption keys to **Cloud HSM** (FIPS 140-2 Level 3 validated).

---

## 3. DoD SRG Technical Architecture Safeguards

### 1. Network Boundary & DISA Cloud Access Point (CAP)
- **IL2**: Public internet ingress allowed with Cloud Armor WAF and TLS 1.2+ encryption.
- **IL4 & IL5**: 
  - Direct connection to the **DISA Cloud Access Point (CAP)** (or approved Boundary Cloud Access Point - BCAP / Internet Cloud Access Point - ICAP) via **Dedicated Interconnect** or **Partner Interconnect**.
  - No direct, unvetted public internet ingress to internal mission systems.
  - Mandatory deployment of **VPC Service Controls (VPC-SC)** security perimeters around all managed data services (Cloud Storage, BigQuery, Vertex AI, Cloud SQL).

### 2. Cryptographic Security (Cloud HSM & FIPS 140)
- Enforce **Customer-Managed Encryption Keys (CMEK)** powered exclusively by **Cloud HSM** (FIPS 140-2 Level 3).
- Symmetric keys: AES-256 in GCM or CBC mode.
- Transmission: Enforce TLS 1.2+ with approved NSA Suite B / FIPS cipher suites; disable TLS 1.0, 1.1, and all non-PFS ciphers.

### 3. Identity, Credential & Access Management (ICAM)
- Enforce DoD CAC (Common Access Card) or PKI certificate-based authentication via Cloud Identity SAML / OIDC enterprise federation.
- Primitive IAM roles (`Owner`, `Editor`) are strictly prohibited.
- Enforce **GKE Workload Identity** and **Cloud Run Service Accounts**; disable all static service account JSON key generation via organization policy constraint `iam.disableServiceAccountKeyCreation`.

### 4. Audit Logging & DoD CSSP Integration
- Enable comprehensive **Cloud Audit Logs**:
  - Admin Activity (enabled by default)
  - Data Access logs (`DATA_READ`, `DATA_WRITE`, `ADMIN_READ`) on all services handling CUI/NSS data.
- Stream audit logs continuously via Cloud Logging sinks to:
  - An immutable, locked Cloud Storage bucket (**Bucket Lock** with multi-year compliance retention).
  - The designated DoD **Cybersecurity Service Provider (CSSP)** / Security Operations Center (SOC) SIEM.
- Continuous posture auditing using **Security Command Center (SCC) Enterprise**.
