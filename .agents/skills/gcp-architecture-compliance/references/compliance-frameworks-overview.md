# Google Cloud Compliance Frameworks Master Reference

## Quick Comparison Matrix

This table summarizes key compliance frameworks, the governing agreement or audit artifact on Google Cloud, whether Assured Workloads is available, and primary architectural control focus.

| Framework | Governing Document / Artifact | Assured Workloads Regime? | Primary Regulated Data | Key Architectural Controls |
| :--- | :--- | :--- | :--- | :--- |
| **HIPAA** | Business Associate Agreement (BAA) | Yes (`HIPAA`) | Protected Health Information (PHI) | Signed BAA, Data Access Audit Logs, CMEK, VPC-SC, Private IPs, Cloud DLP |
| **PCI DSS 4.0** | Attestation of Compliance (AoC), Shared Responsibility Matrix | Yes (`PCI-DSS`) | Cardholder Data (CHD), Sensitive Auth Data (SAD) | Scope reduction, Tokenization, Cloud Armor WAF, isolated CDE VPC, TLS 1.2+, MFA |
| **FedRAMP** | FedRAMP High / Moderate ATO | Yes (`FedRAMP High`, `FedRAMP Moderate`) | Federal Information, CUI | Assured Workloads, US data residency, FIPS 140-2 Level 3 (Cloud HSM), Access Transparency |
| **SOC 2 Type II** | SOC 2 Report (Security, Availability, Confidentiality, Privacy) | Baseline | Customer Data across all cloud services | IAM least privilege, Cloud Audit Logs, Disaster Recovery, encryption at rest/transit |
| **ISO/IEC 27001** | ISO/IEC 27001:2022 Certificate | Baseline | Information Security Management System (ISMS) | Asset classification, change management, continuous vulnerability scanning |
| **HITRUST CSF** | HITRUST Letter of Certification | Aligns with HIPAA regime | Healthcare & Highly Regulated Data | Prescriptive security controls mapped to NIST, ISO, HIPAA |
| **GDPR** | Data Processing Addendum (DPA) | Yes (EU Regions / Sovereignty controls) | Personal Data of EU Data Subjects | EU Data Residency, Cloud KMS / External Key Manager (EKM), Data subject rights processes |

---

## Where to Retrieve Official Artifacts

1. **Compliance Reports Manager**:
   - URL: [https://cloud.google.com/compliance/reports-manager](https://cloud.google.com/compliance/reports-manager)
   - Use: Access Google's SOC 1/2/3 reports, ISO certificates, PCI DSS AoCs, FedRAMP packages, and HITRUST certifications under NDA.

2. **Google Cloud Compliance Offerings Directory**:
   - URL: [https://cloud.google.com/security/compliance/offerings](https://cloud.google.com/security/compliance/offerings)
   - Comprehensive searchable directory of all country, regional, and industry certifications.

3. **Google Cloud Assured Workloads**:
   - URL: [https://cloud.google.com/assured-workloads](https://cloud.google.com/assured-workloads)
   - Automated boundary and organizational policy enforcement for HIPAA, FedRAMP, CJIS, IL4/IL5, EU Sovereignty, and PCI-DSS.
