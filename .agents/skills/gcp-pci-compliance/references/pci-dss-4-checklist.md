# PCI DSS 4.0 Architecture Checklist on Google Cloud

## Overview

The Payment Card Industry Data Security Standard (PCI DSS) v4.0 applies to all organizations that store, process, or transmit Cardholder Data (CHD) and/or Sensitive Authentication Data (SAD).

Google Cloud maintains an annual **PCI DSS Level 1 Service Provider** certification. Google's Attestation of Compliance (AoC) and Shared Responsibility Matrix are accessible via the [Compliance Reports Manager](https://cloud.google.com/compliance/reports-manager).

---

## 1. Cardholder Data Environment (CDE) Scope Minimization

> [!IMPORTANT]
> **Cardinal Principle**: The primary goal of cloud payment architecture is **Scope Reduction**.
> 1. Use **hosted payment fields / iframes / redirection** (e.g. Stripe Elements, Adyen Drop-in) so card numbers never traverse the cloud application servers (qualifying for **SAQ A**).
> 2. If API-based transmission is required (qualifying for **SAQ A-EP**), isolate API servers in a dedicated VPC with no database storage of PAN.
> 3. If Primary Account Numbers (PAN) must be stored (qualifying for **SAQ D**), strictly tokenize using **Cloud KMS / Cloud HSM** or **Sensitive Data Protection (Cloud DLP)** tokenization, and isolate the CDE in a separate GCP project and VPC.

---

## 2. Technical Mapping of PCI DSS 4.0 Requirements to Google Cloud

### Requirement 1: Install and Maintain Network Security Controls
- Deploy **VPC Firewalls** with strict default-deny ingress and egress rules.
- Deploy **Cloud Armor** WAF with OWASP Top 10 rule sets and rate limiting on all public payment ingress points (Req 6.4.2).
- Use **Private Service Connect** or internal load balancers to communicate between application tiers and databases.

### Requirement 2: Apply Secure Configurations to All System Components
- Harden VM base images using CIS Benchmarks (GCP provides CIS-hardened OS images).
- Disable unnecessary ports, services, and legacy protocols.
- Never use default administrative credentials.

### Requirement 3: Protect Stored Account Data
- **Never store Sensitive Authentication Data (SAD)** post-authorization (CVV/CVC, full magnetic stripe data, PIN).
- If PAN is stored, render it unreadable everywhere using:
  - Strong AES-256 encryption with **Customer-Managed Encryption Keys (CMEK)** via **Cloud HSM** (FIPS 140-2 Level 3).
  - Truncation (first 6 and last 4 digits only).
  - Format-Preserving Encryption (FPE) tokenization via Sensitive Data Protection.
- Separate cryptographic keys from encrypted data (Cloud KMS IAM boundaries).

### Requirement 4: Protect Cardholder Data with Strong Cryptography During Transmission
- Enforce **TLS 1.2 or TLS 1.3** on Cloud Load Balancing SSL policies.
- Disable weak ciphers (RC4, 3DES, CBC).
- For hybrid on-premises connectivity, use Cloud Interconnect with MACsec or Cloud VPN with IPsec (IKEv2).

### Requirement 6: Develop and Maintain Secure Systems and Software
- Scan container images for vulnerabilities in **Artifact Registry** using Vulnerability Scanning (Container Analysis).
- Enforce automated patching regimes for Compute Engine VMs using OS Config (VM Manager).
- Deploy web application firewall (**Cloud Armor**) in front of all public-facing web applications.

### Requirement 7 & 8: Restrict Access & Identify Users (IAM)
- Enforce **Multi-Factor Authentication (MFA)** for all administrative access into the CDE.
- Enforce Zero Trust access via **Identity-Aware Proxy (IAP)**; eliminate direct SSH/RDP with public IPs.
- Practice least-privilege IAM; eliminate basic roles (`Owner`, `Editor`).
- Enforce Workload Identity; block service account key downloads.

### Requirement 10: Log and Monitor All Access to System Components & CHD
- Enable **Cloud Audit Logs** (including Data Access logs for data stores touching CHD).
- Centralize logs into a dedicated security audit GCP project.
- Retain audit logs for at least **1 year**, with at least **3 months immediately available** for analysis.
- Use **Security Command Center (SCC) Premium** for automated threat detection and compliance monitoring.

### Requirement 11: Test Security of Systems and Networks Regularly
- Enable **VPC Flow Logs** for network inspection and anomaly detection.
- Deploy intrusion detection systems (IDS) via Google Cloud IDS or third-party partner appliances.
- Conduct quarterly external vulnerability scans by an Approved Scanning Vendor (ASV) and annual penetration testing.
