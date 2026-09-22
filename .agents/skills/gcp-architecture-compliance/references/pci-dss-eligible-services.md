# Google Cloud PCI DSS Eligible Services & Architecture Compliance Guide

## Overview

The Payment Card Industry Data Security Standard (PCI DSS, currently version 4.0) applies to all entities that store, process, or transmit cardholder data (CHD) and/or sensitive authentication data (SAD).

Google Cloud undergoes an annual third-party audit to certify that its infrastructure and a broad set of services comply with **PCI DSS Level 1 Service Provider** standards. Google provides an **Attestation of Compliance (AoC)** and a **Shared Responsibility Matrix** available via the [Compliance Reports Manager](https://cloud.google.com/compliance/reports-manager).

Official Google Cloud PCI DSS Guidance: [https://cloud.google.com/security/compliance/pci-dss](https://cloud.google.com/security/compliance/pci-dss)

---

## 1. Scope Reduction Principle (Golden Rule of PCI Architecture)

> [!IMPORTANT]
> **Cardinal Architecture Rule**: The primary architectural objective in PCI DSS is **Scope Minimization**. Avoid bringing Google Cloud workloads into full CDE (Cardholder Data Environment) scope whenever possible by using **tokenization** and **hosted payment fields** (e.g., iframe/redirection via certified payment gateways).
>
> If CHD must be stored or processed in GCP, strictly segment the CDE using isolated VPCs, VPC Service Controls, and dedicated IAM projects.

---

## 2. In-Scope Google Cloud Services for PCI DSS

Google Cloud certifies most core services under its annual Level 1 audit, including:

### Compute & Containers
- Compute Engine
- Google Kubernetes Engine (GKE)
- Cloud Run & Cloud Functions
- App Engine

### Storage & Data Warehousing
- Cloud Storage
- Cloud SQL (MySQL, PostgreSQL, SQL Server)
- Cloud Spanner, Cloud Bigtable, Firestore
- BigQuery & BigLake

### Networking & Security
- Virtual Private Cloud (VPC) & Cloud Load Balancing
- Cloud Armor (WAF & DDoS - mandatory for Requirement 6.4.2)
- Cloud KMS / Cloud HSM (meets Requirement 3 cryptographic requirements)
- Secret Manager
- Cloud IAM & Identity-Aware Proxy (IAP)
- VPC Service Controls (CDE perimeter boundary)
- Security Command Center (SCC)

### Operations & Monitoring
- Cloud Logging & Cloud Monitoring (Requirement 10 audit trails)
- Artifact Registry (Container scanning for Requirement 11/6)

---

## 3. High-Risk / Ineligible Components for PCI DSS

| Risk Area | Architectural Anti-Pattern | Required Mitigation |
| :--- | :--- | :--- |
| **Direct Card Storage** | Storing Primary Account Numbers (PAN) unencrypted in standard database tables or flat files | Use Cloud KMS / Sensitive Data Protection (DLP) tokenization, or offload to 3rd-party payment gateway |
| **Flat Network Topology** | Hosting web applications, APIs, and CDE databases in a single unsegmented VPC | Strict multi-project or VPC subnet isolation; CDE behind internal load balancers with no direct Internet ingress |
| **Missing WAF** | Public endpoints receiving payment data without a Web Application Firewall | Deploy **Cloud Armor** with OWASP Top 10 rules and WAF inspection on all public payment paths |
| **Weak Audit Logging** | Audit logs kept under 1 year or not tamper-resistant | Fulfill Requirement 10: Retain logs for at least 1 year (3 months immediately available) using locked Cloud Storage buckets |
| **Shared Bastions / SSH** | Direct SSH/RDP access using open public IP ports | Enforce Zero Trust access via **Identity-Aware Proxy (IAP)**; enforce MFA for all administrative access |

---

## 4. Key PCI DSS 4.0 Architectural Safeguards

- **Requirement 1 & 2**: Implement strict Firewall Rules and Cloud Armor WAF; disable all default configurations.
- **Requirement 3**: Protect stored account data. Never store Sensitive Authentication Data (SAD / CVV / PIN) post-authorization. Encrypt PAN with AES-256 via Cloud KMS.
- **Requirement 4**: Enforce TLS 1.2+ with modern ciphers on Cloud Load Balancer SSL policies for all transmission over open networks.
- **Requirement 6**: Secure development and container image vulnerability scanning via Artifact Registry.
- **Requirement 8**: Multi-Factor Authentication (MFA) required for all administrative access to CDE.
- **Requirement 10**: Log all access to cardholder data and maintain continuous monitoring with Cloud Logging and SCC.
