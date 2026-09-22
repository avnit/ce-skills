# Google Cloud FedRAMP Eligible Services & Architecture Compliance Guide

## Overview

The Federal Risk and Authorization Management Program (**FedRAMP**) provides a standardized approach to security assessment, authorization, and continuous monitoring for cloud products and services used by U.S. Federal Government agencies and contractors.

Google Cloud maintains **FedRAMP High** and **FedRAMP Moderate** Authorizations to Operate (ATO) for a broad range of cloud services within its government-authorized boundary.

Official Google Cloud FedRAMP Guidance: [https://cloud.google.com/security/compliance/fedramp](https://cloud.google.com/security/compliance/fedramp)

---

## 1. Assured Workloads: The FedRAMP Enforcer

> [!IMPORTANT]
> **Primary Recommendation**: Federal government and public sector workloads should always be provisioned using **Google Cloud Assured Workloads** configured with the appropriate regime:
> - **FedRAMP Moderate**
> - **FedRAMP High**
> - **DoD Impact Level 4 (IL4) / IL5** (if defense sector)
> 
> Assured Workloads automatically enforces organizational policy constraints that restrict service usage exclusively to FedRAMP-authorized products, mandates US-only data locations, and restricts Google support personnel access to screened US persons.

---

## 2. FedRAMP Authorized Services (Boundary Coverage)

FedRAMP High / Moderate authorization covers major Google Cloud services including:

- **Compute & Core**: Compute Engine, Google Kubernetes Engine (GKE), Cloud Run, Cloud Functions.
- **Data & Storage**: Cloud Storage, Cloud SQL, BigQuery, Spanner, Firestore, Cloud Bigtable.
- **Networking**: VPC, Cloud Load Balancing, Cloud Interconnect, Cloud VPN, Cloud DNS, Cloud NAT, Cloud Armor.
- **Security & Identity**: Cloud KMS (FIPS 140-2 Level 3 validated with Cloud HSM), Secret Manager, Cloud IAM, Identity-Aware Proxy (IAP), VPC Service Controls, Security Command Center.
- **Analytics & ML**: Cloud Dataflow, Cloud Dataproc, Cloud Pub/Sub, Vertex AI (core services under Assured Workloads boundary).

---

## 3. High-Risk / Ineligible Components for FedRAMP

| High-Risk Item | Architectural Hazard | Mandatory Remediation |
| :--- | :--- | :--- |
| **Non-US Data Locations** | Storing federal data in global or non-US regions | Restrict resource creation to `us-central1`, `us-east4`, `us-west1`, etc. via Assured Workloads Resource Location Restriction policy |
| **Non-FIPS Cryptography** | Utilizing cryptographic modules that lack FIPS 140 validation | Enforce **Cloud HSM** (FIPS 140-2 Level 3) for CMEK keys; enforce TLS 1.2+ with approved FIPS cipher suites |
| **Unauthorized Services** | Attempting to deploy beta, preview, or third-party marketplace tools within the boundary | Assured Workloads automatically blocks unauthorized service creation; use only FedRAMP High/Moderate authorized GA services |
| **Unrestricted Support Access** | Allowing global Google technical support personnel access to systems | Enable **Access Transparency** and **Access Approval** to verify and approve any Google operator access |
