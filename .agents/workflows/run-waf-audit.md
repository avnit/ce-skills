---
description: Orchestrate the end-to-end automated ingestion of a design blueprint, multi-pillar Google Cloud Well-Architected Framework (WAF) auditing, user gap clarification, and generation of a comprehensive WAF Audit & ADR report.
---

# Workflow: Run Google Cloud WAF Architecture Audit

This standalone workflow guides the Solutions Architect co-design plane to ingest an existing architecture design blueprint, conduct automated multi-pillar WAF compliance audits, prompt the human Customer Engineer (CE) with targeted clarifying questions on architecture gaps, and compile board-ready WAF Audit & ADR reports.

---

## 🚨 CRITICAL INTERACTION MANDATE

To maintain strict integration compatibility with the CE Workbench graphical dashboard interface, **plain text chat prompting is strictly prohibited**. All scoping path parameters, gap override justifications, and architectural validations MUST be collected exclusively using the native `ask_question` tool modal.

## 🔄 Operational Workflow Lifecycle

### Phase 0: Pre-Flight Authentication Verification

1. Consult and enforce the global auth validation standard: [gcloud_auth.md](../rules/gcloud_auth.md).
2. Execute the **gcloud-auth-verification** skill (`python3 .agents/skills/gcloud-auth-verification/scripts/verify_auth.py`).
3. If active account matches target environment, log active identity and proceed automatically.
4. If an account switch or user decision is required, invoke the `ask_question` tool modal to let the user select or confirm the active account.

### Phase 1: Blueprint Scoping Intake

1. Ask the human Customer Engineer (CE) to supply the scoping parameters via the `ask_question` modal UI:
   - Customer Name & Industry Vertical
   - Governing Compliance Frameworks (e.g., `PCI-DSS`, `HIPAA`, `FedRAMP`, `SOC2`, `None`)
   - Technology Domain Focus (`GKE`, `DATABASES`, `NETWORKING`, `COMPOSITE`)
   - Deployment Size (`ENTERPRISE_SCALE`, `MEDIUM_BUSINESS`, `SMALL_WORKLOAD`)
   - Primary Customer Priority (`SECURITY`, `RELIABILITY`, `PERFORMANCE`, `COST_OPTIMIZATION`, `OPERATIONAL_EXCELLENCE`)
   - Target Blueprint File Path (Free text path, e.g., `/path/to/design_blueprint.md`).

### Phase 2: Target Ingestion & Multi-Pillar WAF Audit

1. Read the target file at `Target Blueprint File Path` using the `view_file` tool to parse the overall architecture descriptions, components, databases, networks, and Mermaid diagram configurations.
2. Perform an automated audit mapping the components against the WAF pillars:
   - **Security**: Identity, boundary control, data protection, encryption at rest/in transit.
   - **Reliability**: Redundancy, high availability, backup & DR, RTO/RPO mapping.
   - **Performance**: Scaling models, latency optimizations, compute matching.
   - **Cost Optimization**: Autoscaling configurations, right-sizing, storage tiers.
   - **Operational Excellence**: Logging, monitoring, CI/CD automation pipelines.
3. Identify structural gaps or policy misalignments relative to the governing compliance framework and priority (e.g. single-zone GKE with zonal Filestore, unencrypted cloud storage buckets).

### Phase 3: Targeted Gap Clarification Modal Loop

1. Isolate the identified gaps and narrow them down to the **2-3 highest-priority WAF gaps**.
2. Loop through these 2-3 gaps strictly one-by-one and present a clarifying question to the human CE using the `ask_question` modal UI:
   - Question Title: Detail the specific WAF Gap & Pillar (e.g., `"[WAF Security Audit] Missing Envelope Encryption on Cloud Storage"`).
   - Select Options: Provide clear candidate remediation strategies with the WAF-recommended strategy listed first and prefixed with `(Recommended)`.
   - Instruct the CE that selecting a non-recommended option requires typing a business justification in the custom text write-in box.
3. Capture CE responses and save the consolidated state to `session_cache.json`.

### Phase 4: Narrative Synthesis & CISO Compliance Review

1. Assemble the audit findings, WAF scorecards, gap analyses, and CE justifications into a narrative structure.
2. Merge with `ADR_TEMPLATE.md` to compile a board-ready WAF compliance review document.
3. Invoke the **Security compliance reviewer peer sub-agent** (`ciso-reviewer-agent`) to audit the recommendations:
   - Verify that custom justifications inside `<ce_input>` tags are technically sound.
   - Check mapped regulations against standard requirements.
4. If passed, stage the final report. If failed, trigger a clarifying loopback modal request to the CE.

### Phase 5: Staging & Delivery

1. Write the final comprehensive report directly to the sibling directory of the target blueprint at `meeting/<customer_name>/waf_audit_report.md`.
2. The report MUST stage:
   - **Executive WAF Scorecard**: Circular pillar compliance rates (0-100%).
   - **Detailed Gap Matrix**: Clear severity levels (Critical, High, Medium, Low).
   - **Remediation Actions**: Detailed step-by-step blueprint corrections.
   - **Upgraded Topology**: Multi-pillar, beautifully styled Mermaid architecture diagram pre-rendered to `meeting/<customer_name>/assets/waf_audit_diagram.png` and embedded.
3. Present the summary in the chat, including direct workspace file links to the staged report.
