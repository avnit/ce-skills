# Google Cloud HIPAA BAA Eligible Services & Architecture Compliance Guide

## Overview

Under the Health Insurance Portability and Accountability Act (HIPAA), covered entities and their business associates must enter into a **Business Associate Agreement (BAA)** with Google before storing, processing, or transmitting Protected Health Information (PHI) in Google Cloud.

> [!IMPORTANT]
> **Core Principle**: A product being "HIPAA-eligible" (included in Google Cloud's BAA) does **not** automatically make an architecture HIPAA-compliant. The customer remains responsible for configuring services securely under the **Shared Responsibility Model**.

Official Google Cloud HIPAA Guidance: [https://cloud.google.com/security/compliance/hipaa](https://cloud.google.com/security/compliance/hipaa)

---

## 1. HIPAA-Eligible Google Cloud Services (BAA Covered)

Google Cloud’s BAA covers the vast majority of GA (Generally Available) core services. The following services are covered under Google's BAA as of standard GA release:

### Compute & Containers
- **Compute Engine**: VMs, Persistent Disks, Local SSDs.
- **Google Kubernetes Engine (GKE)**: Standard and Autopilot clusters.
- **Cloud Run**: Serverless container execution.
- **Cloud Functions**: Serverless event-driven functions (1st and 2nd gen).
- **App Engine**: Standard and Flexible environments.
- **Batch**: Fully managed batch job execution.

### Storage & Databases
- **Cloud Storage**: Standard, Nearline, Coldline, Archive.
- **Cloud SQL**: MySQL, PostgreSQL, SQL Server instances.
- **AlloyDB for PostgreSQL**: Managed PostgreSQL-compatible database.
- **Cloud Spanner**: Globally distributed relational database.
- **Cloud Bigtable**: Managed NoSQL wide-column database.
- **Firestore / Datastore**: Serverless document database.
- **BigQuery**: Enterprise data warehouse and BigLake storage.
- **Memorystore**: In-memory Redis and Memcached.

### Networking & Security
- **Virtual Private Cloud (VPC)**: Subnets, Firewall Rules, VPC Peering.
- **Cloud Load Balancing**: Internal and External HTTP(S), TCP, SSL Proxy.
- **Cloud Armor**: Web Application Firewall (WAF) and DDoS defense.
- **Cloud Interconnect & Cloud VPN**: Hybrid connectivity.
- **Cloud NAT**: Egress translation.
- **Cloud DNS**: Managed authoritative and forwarding DNS.
- **Cloud KMS / Cloud HSM**: Key management, Customer-Managed Encryption Keys (CMEK).
- **Secret Manager**: Secure API keys and credential storage.
- **Cloud Identity and Access Management (IAM)**: Roles, service accounts.
- **Identity-Aware Proxy (IAP)**: Zero-trust context-aware application access.
- **VPC Service Controls (VPC-SC)**: Security perimeters preventing exfiltration.
- **Security Command Center (SCC)**: Threat detection and posture management.
- **Certificate Authority Service (CAS)**: Private CA management.

### Analytics, Streaming & Integration
- **Cloud Pub/Sub**: Message ingestion and streaming.
- **Cloud Dataflow**: Apache Beam stream and batch processing.
- **Cloud Dataproc**: Managed Apache Spark and Hadoop clusters.
- **Cloud Composer**: Managed Apache Airflow workflow orchestration.
- **Eventarc**: Event routing.
- **Cloud Tasks & Cloud Scheduler**: Job scheduling and task execution.
- **Looker (Google Cloud core)**: Governed BI and embedded analytics.
- **Sensitive Data Protection (formerly Cloud DLP)**: Automatic PHI inspection, masking, and tokenization.

### Healthcare & Life Sciences
- **Cloud Healthcare API**: FHIR, HL7v2, and DICOM stores with built-in de-identification.

### AI & Machine Learning
- **Vertex AI Core Platform**: Custom Model Training, Prediction endpoints, Feature Store, Pipelines.
- **Vertex AI Gemini API**: Direct API calls to Gemini models within Google Cloud project boundary (with data governance commitments).
- **Speech-to-Text, Text-to-Speech, Cloud Translation**: Audio and language models.
- **Document AI**: Document processing and OCR.
- **Cloud Vision**: Image processing and analysis.

---

## 2. Ineligible Services & Critical Red Flags (NOT HIPAA BAA Covered)

The following services or features are **NOT** eligible to store or process PHI, or carry severe restrictions:

| Category | Ineligible / High-Risk Component | Issue & Impact | Approved Replacement / Mitigation |
| :--- | :--- | :--- | :--- |
| **Pre-GA Services** | Any service or API in **Alpha / Preview / Experimental** | Pre-GA terms specifically exclude HIPAA BAA coverage | Must only use Generally Available (GA) services for PHI workloads. |
| **Marketplace 3rd Party** | Third-party VM images, SaaS, or Partner tools in GCP Marketplace | Google’s BAA only covers Google-first-party products; partner software is under the partner's own terms | Customer must execute a separate BAA directly with the third-party software vendor, or use Google-native alternatives. |
| **Public AI Plugins / Web Connectors** | Vertex AI Search / Extensions using unverified external connectors | Exfiltration risk to non-BAA external endpoints | Restrict RAG pipelines to private VPC-SC protected BigQuery/Cloud Storage with grounding over enterprise data only. |
| **Public Bucket / Open Network Access** | Cloud Storage with `allUsers` / `allAuthenticatedUsers` permissions | Critical PHI data breach risk | Enforce Uniform Bucket-Level Access (UBLA) + Public Access Prevention (PAP). |
| **Default Logging Configuration** | Default Cloud Audit Logging (Data Access logs disabled) | Fails HIPAA § 164.312(b) Audit Controls Requirement | Explicitly enable **Data Access audit logs** (ADMIN_READ, DATA_READ, DATA_WRITE) for all services handling PHI. |

---

## 3. Mandatory HIPAA Architectural Safeguards (The 7 Pillars)

Even when using 100% HIPAA-eligible services, the architecture must implement these 7 foundational controls:

### Pillar 1: Execute Google Cloud BAA
- A signed BAA must be in place between the organization and Google before any PHI touches the cloud.
- Configure Google Cloud **Assured Workloads** with the **HIPAA** compliance regime to automatically enforce organizational policies (e.g., restrict resource locations, enforce CMEK, disallow non-compliant services).

### Pillar 2: Data Encryption (Rest & Transit)
- **At Rest**: 
  - Google encrypts data at rest by default using AES-256.
  - For heightened compliance and cryptographic erasure, utilize **Customer-Managed Encryption Keys (CMEK)** with Cloud KMS or Cloud HSM.
- **In Transit**:
  - All data entering or leaving the VPC must be encrypted using TLS 1.2 or higher.
  - Disable weak ciphers on Cloud Load Balancing SSL Policies.
  - Enforce Internal HTTPS/mTLS between microservices.

### Pillar 3: Access Control & Identity (Least Privilege)
- Eliminate basic primitive roles (`Owner`, `Editor`, `Viewer`) in favor of predefined or custom IAM roles.
- Enforce Multi-Factor Authentication (MFA) on all user accounts via Google Workspace / Cloud Identity.
- Use dedicated Service Accounts per service tier with minimal permissions.
- Disable service account key downloads; leverage Workload Identity Federation for external access and GKE Workload Identity for Kubernetes pods.

### Pillar 4: Network Isolation & Perimeter Defense
- **No Public IPs**: Databases (Cloud SQL, AlloyDB, Bigtable) and VM compute workers must have private IPs only (Private Service Connect / Private IP).
- **VPC Service Controls**: Create a security perimeter around projects containing Cloud Storage, BigQuery, and Vertex AI to prevent data exfiltration.
- **Cloud Armor**: Enforce WAF policies, OWASP Top 10 rule sets, and rate limiting on all public entry points.
- **Private Google Access**: Ensure compute resources without external IPs access Google APIs privately.

### Pillar 5: Comprehensive Audit Logging & Retention
- **HIPAA § 164.312(b)** mandates recording and examining activity in systems that contain or use EPHI.
- **Data Access Logs**: Enable `DATA_READ`, `DATA_WRITE`, and `ADMIN_READ` for Cloud Storage, BigQuery, Cloud SQL, and Cloud Healthcare API.
- **Log Sinks & Retention**: Route audit logs to a dedicated, locked-down Cloud Storage bucket or BigQuery dataset with retention policies (at least 6-7 years per state/federal requirements) using Bucket Lock (Object Retention).
- Export security findings to Security Command Center (SCC) Premium.

### Pillar 6: PHI Discovery & De-identification
- Employ **Sensitive Data Protection (Cloud DLP)** to discover and redact accidental PHI in logs, free-text fields, and training datasets.
- For analytics/data lake architectures, use the **Cloud Healthcare API** de-identification pipeline to strip HIPAA 18 Safe Harbor identifiers before feeding BigQuery or ML models.

### Pillar 7: Backup, Disaster Recovery & High Availability
- Implement multi-region or dual-region Cloud Storage buckets for critical backups.
- Enable automated daily backups and point-in-time recovery (PITR) for Cloud SQL and AlloyDB.
- Maintain tested Disaster Recovery (DR) and business continuity runbooks.

---

## 4. Quick Architecture Verification Checklist for HIPAA

When evaluating an architecture proposal for HIPAA, check off:
- [ ] Are 100% of proposed GCP services on the BAA-eligible list?
- [ ] Are any third-party Marketplace or SaaS components identified, and do they have separate BAAs?
- [ ] Is Assured Workloads (HIPAA) recommended or enabled?
- [ ] Is Cloud Audit Logging configured to capture `DATA_READ` and `DATA_WRITE`?
- [ ] Are all database instances private with zero public IP exposure?
- [ ] Are Cloud Storage buckets protected by Uniform Bucket-Level Access and Public Access Prevention?
- [ ] Is Customer-Managed Encryption (CMEK) evaluated/implemented for high-risk data stores?
- [ ] Is a VPC Service Controls perimeter defined around the data layer?
- [ ] Is a de-identification strategy in place (Cloud DLP or Healthcare API) for downstream analytics/AI?
