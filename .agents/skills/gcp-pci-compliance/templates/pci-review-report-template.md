# Google Cloud PCI DSS 4.0 Architecture Review Report

**Workload / Payment Application:** {Application Name}  
**Merchant / Service Provider Level:** {Level 1 / 2 / 3 / 4}  
**Self-Assessment Scope:** {SAQ A / SAQ A-EP / SAQ D / Full RoC}  
**Review Date:** {Date}  
**Lead CE / Reviewer:** {Reviewer Name}  

---

## 1. Executive Summary & Verdict

| Review Dimension | Status | Key Evaluation Notes |
| :--- | :---: | :--- |
| **Overall PCI DSS Verdict** | **{COMPLIANT / CONDITIONAL / NON-COMPLIANT}** | {High-level summary of CDE readiness} |
| **Scope Minimization & Tokenization** | **{PASS / ATTENTION / FAIL}** | {Is CHD isolated/tokenized or stored raw?} |
| **Network & Perimeter Isolation (Req 1, 2)** | **{PASS / ATTENTION / FAIL}** | {CDE VPC segmentation, Cloud Armor WAF status} |
| **Cardholder Data Protection (Req 3, 4)** | **{PASS / ATTENTION / FAIL}** | {PAN encryption, SAD exclusion, TLS 1.2+ ciphers} |
| **Access Control & MFA (Req 7, 8)** | **{PASS / ATTENTION / FAIL}** | {IAP zero trust, MFA enforcement, no SA keys} |
| **Audit Logging & Monitoring (Req 10)** | **{PASS / ATTENTION / FAIL}** | {Log retention 1 yr, Data Access logs, SCC} |

### Verdict Definitions:
- 🟢 **COMPLIANT**: Architecture properly isolates or eliminates CDE scope, utilizes eligible Level 1 services, and implements all required PCI DSS 4.0 technical controls.
- 🟡 **CONDITIONAL**: In-scope services are eligible, but specific controls (e.g., Cloud Armor WAF rules, 1-year log retention, or MFA on bastion access) must be configured prior to QSA audit.
- 🔴 **NON-COMPLIANT**: Architecture contains critical PCI violations such as unencrypted PAN storage, retention of post-auth SAD (CVV), flat unsegmented networks, or public database IPs.

---

## 2. In-Scope Google Cloud Services Verification

| Component Layer | Proposed GCP Product | PCI DSS Level 1 Certified? | Architecture Role | Security Hardening Notes |
| :--- | :--- | :---: | :--- | :--- |
| **Ingress / WAF** | {Cloud Armor + External LB} | ✅ / ❌ | Entry point WAF | OWASP Top 10 rules enforced |
| **Application Tier** | {GKE / Cloud Run} | ✅ / ❌ | Payment API processing | Workload Identity, container scanning |
| **Database / Vault** | {Cloud SQL / Spanner} | ✅ / ❌ | Token / Payment metadata | Private IP only, CMEK encryption |
| **Key Management** | {Cloud KMS / Cloud HSM} | ✅ / ❌ | Crypto operations | FIPS 140-2 Level 3 HSM keys |
| **Tokenization** | {Cloud DLP / Sensitive Data Protection}| ✅ / ❌ | Format-preserving tokenization| De-identifies PAN before storage |

---

## 3. PCI DSS 4.0 Technical Requirements Checklist

### 3.1 Network Security & System Hardening (Req 1, 2)
- [ ] CDE is segmented into a dedicated VPC or separate GCP project.
- [ ] Cloud Armor WAF is deployed on all public payment ingress routes.
- [ ] Databases and compute backend have zero public IPv4 addresses.
- [ ] Restrictive ingress/egress firewall rules configured (default deny).

### 3.2 Protecting Account Data (Req 3, 4)
- [ ] No storage of Sensitive Authentication Data (SAD / CVV / PIN) post-authorization.
- [ ] PAN is rendered unreadable via Cloud KMS / Cloud HSM (AES-256) or tokenized.
- [ ] Cryptographic keys are separated with strict IAM boundary permissions.
- [ ] TLS 1.2 or TLS 1.3 enforced on Cloud Load Balancing SSL Policies.

### 3.3 Access Control & IAM (Req 7, 8)
- [ ] MFA required for all administrative access to CDE systems.
- [ ] Access to VMs gated via Identity-Aware Proxy (IAP); zero direct SSH on public IPs.
- [ ] Primitive IAM roles (`Owner`, `Editor`) eliminated in favor of least-privilege roles.
- [ ] Service Account key downloads disabled via organization policy.

### 3.4 Logging, Monitoring & Testing (Req 10, 11)
- [ ] Cloud Audit Logs (Admin Activity + Data Access) enabled for all CDE services.
- [ ] Audit logs retained for at least 1 year (at least 3 months immediately active).
- [ ] Security Command Center (SCC) enabled for real-time threat detection.
- [ ] Container image vulnerability scanning enabled in Artifact Registry.
- [ ] VPC Flow Logs enabled on CDE subnets for traffic inspection.

---

## 4. Prioritized Remediation Action Plan

### Critical Blockers (Audit Failures)
1. **{Blocker 1}**: {Remediation description and fix}
2. **{Blocker 2}**: {Remediation description and fix}

### Scope Reduction & Architecture Hardening
1. **{Recommendation 1}**: {Scope reduction strategy, e.g. hosted fields or tokenization}
2. **{Recommendation 2}**: {Hardening configuration}

---

## 5. Official References & Artifacts
- Google Cloud PCI DSS Overview: [https://cloud.google.com/security/compliance/pci-dss](https://cloud.google.com/security/compliance/pci-dss)
- Google Cloud Compliance Reports Manager: [https://cloud.google.com/compliance/reports-manager](https://cloud.google.com/compliance/reports-manager)
- PCI Security Standards Council: [https://www.pcisecuritystandards.org/](https://www.pcisecuritystandards.org/)
