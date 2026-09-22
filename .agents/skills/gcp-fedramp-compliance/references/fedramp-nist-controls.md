# FedRAMP High & Moderate Architecture Controls on Google Cloud (NIST SP 800-53 Rev 5)

## Overview

The Federal Risk and Authorization Management Program (FedRAMP) standardizes security assessment, authorization, and continuous monitoring for cloud computing solutions across the U.S. Federal Government.

Google Cloud maintains Authorizations to Operate (ATO) at both:
- **FedRAMP Moderate**: Impact level for systems where the loss of confidentiality, integrity, and availability would have a serious adverse effect. Covers 325 NIST controls.
- **FedRAMP High**: Impact level for systems holding sensitive federal data where loss would have severe or catastrophic adverse effects. Covers 421 NIST controls.

Official Google Cloud FedRAMP Documentation: [https://cloud.google.com/security/compliance/fedramp](https://cloud.google.com/security/compliance/fedramp)

---

## 1. Assured Workloads: The FedRAMP Enforcer

> [!IMPORTANT]
> **Cardinal Federal Rule**: Federal workloads on Google Cloud must be provisioned inside an **Assured Workloads** environment configured with the **FedRAMP Moderate** or **FedRAMP High** regime.
> 
> Assured Workloads automatically applies organization policy constraints that:
> 1. Restrict all resource creation strictly to FedRAMP-authorized Google Cloud regions (e.g. `us-central1`, `us-east4`, `us-west1`).
> 2. Disallow the deployment of non-FedRAMP-authorized services.
> 3. Enforce **Access Approval** and **Access Transparency** to ensure that any emergency Google personnel access is restricted to screened US Persons.

---

## 2. NIST SP 800-53 Rev 5 Technical Controls Mapping to Google Cloud

### AC (Access Control) & IA (Identification and Authentication)
- **CAC / PIV Authentication**: Enforce Smart Card (CAC/PIV) or FIDO2 hardware security keys for all console and administrative access via Cloud Identity / Google Workspace IdP federation.
- **Workload Identity**: Map Kubernetes pods and Cloud Run services to Google Service Accounts; eliminate static service account JSON key files.
- **Least Privilege (AC-6)**: Utilize fine-grained custom IAM roles and Predefined roles with resource-level conditions; completely eliminate primitive `Owner`, `Editor`, and `Viewer` roles.

### SC (System and Communications Protection)
- **FIPS 140-2 / 140-3 Cryptography (SC-13)**:
  - Utilize **Cloud HSM** (FIPS 140-2 Level 3 validated) for Customer-Managed Encryption Keys (CMEK).
  - Enforce FIPS-compliant cipher suites and TLS 1.2+ on all ingress and egress points.
- **Boundary Protection (SC-7)**:
  - Deploy **VPC Service Controls (VPC-SC)** perimeters around all federal data projects to prevent data exfiltration.
  - Deploy **Cloud Armor** WAF on all public entry points.
  - Enforce private IPs for all databases and internal compute; egress through Cloud NAT or Secure Web Proxy.

### AU (Audit and Accountability)
- **Centralized Audit Trail (AU-2, AU-3, AU-6)**:
  - Enable all Cloud Audit Logs (Admin Activity + Data Access logs: `DATA_READ`, `DATA_WRITE`).
  - Export audit logs to an isolated, dedicated compliance GCP project.
  - Enforce immutability and retention (typically 3 to 7 years) using Cloud Storage **Bucket Lock (Object Retention)** in compliance mode.

### SI (System and Information Integrity)
- **Vulnerability & Threat Management (SI-2, SI-4)**:
  - Enable **Security Command Center (SCC) Premium / Enterprise** for automated threat detection, misconfiguration audits, and compliance scanning.
  - Automatically scan container images for CVEs in **Artifact Registry**.
  - Enforce automated OS patching on VMs with Google Cloud VM Manager (OS Config).

### Access Transparency & Access Approval
- **Staff Access Controls**:
  - Configure **Access Approval** so that any request by Google engineers to access customer data requires explicit customer sign-off.
  - Maintain an audit trail of all Google staff access actions via **Access Transparency** logs.
