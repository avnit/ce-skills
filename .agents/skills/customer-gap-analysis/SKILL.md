---
name: customer-gap-analysis
description: >-
  Use when analyzing discovery calls, meeting notes, or transcripts to identify gaps in customer knowledge and operational capability. Focuses on identifying what the customer does not know or lacks operational experience in, building a severity matrix, and providing structured recommendations mapped to GCP solutions and enablement.
---

# Customer Knowledge Gap Analysis (Stage 2)

This skill outlines the methodology for analyzing customer discovery calls to identify knowledge gaps, operational blind spots, and training deficits, and mapping those to Google Cloud solutions and enablement programs.

## Workflow

- [ ] Step 1: Review the discovery call notes or transcript, prioritizing the areas where the customer expresses uncertainty, lack of experience, or concerns.
- [ ] Step 2: Extract the customer's **Current Capability** (what they currently understand or do) and the **Target Capability Required** for successful cloud migration/adoption.
- [ ] Step 3: Fill out the **Gap Analysis Matrix**, scoring each gap based on severity (High, Medium, Low).
- [ ] Step 4: Map solutions, technical mitigations, and enablement resources (training, quickstarts, best practice documentation) to these gaps.
- [ ] Step 5: Save the finalized Knowledge Gap Analysis Report directly to `meeting/<customer_name>/gap_analysis.md`.

## Analysis Prompt

Use the unified discovery and solutions architect system prompt defined in [discovery_analyst.md](../../../prompts/discovery_analyst.md) passing the target flag: `--format gap_analysis`.

---

## Knowledge Gap Analysis Report Template

Use this exact structure to output the analysis to the user:

```markdown
# Customer Knowledge Gap Analysis: [Customer Name]

## 1. Executive Summary

[1-2 paragraphs outlining the customer's business goals, discovery session context, and high-level summary of the most critical knowledge and operational gaps identified].

## 2. Knowledge Gap Domains

### 🏗️ Architecture & Infrastructure Operationalization

- **Customer Current Capability**: [Current understanding of GCP architectures, sizing, persistent storage, VPC structures]
- **Target Capability Required**: [What they need to understand to successfully deploy and run the target architecture]

### 🔒 Security, Governance & Identity Lifecycle

- **Customer Current Capability**: [Current security understanding, managed STS, Workload Identity, secrets lifecycle]
- **Target Capability Required**:

### 🚀 Developer Velocity & CI/CD Pipelines

- **Customer Current Capability**: [Current pipeline patterns, automated validation, GCS layout strategies]
- **Target Capability Required**:

---

## 3. Gap Analysis & Severity Matrix

| Knowledge / Operational Domain | Customer Current Capability                                                  | Target Capability Required                            | Gap Severity (High/Med/Low) | Recommended Enablement or GCP Solution                                          |
| :----------------------------- | :--------------------------------------------------------------------------- | :---------------------------------------------------- | :-------------------------- | :------------------------------------------------------------------------------ |
| e.g., GKE Shared Storage       | Understads basic NFS/EFS but lacks experience with GKE Filestore CSI driver. | Managing regional HA Filestore storage mounts in GKE. | High                        | GKE storage classes training & Google Cloud Architecture Framework storage docs |
|                                |                                                                              |                                                       |                             |                                                                                 |

---

## 4. Recommended Improvements & Action Roadmap

### 🚨 P0: Critical Enablement & Solutions (Must Address First)

#### 1. [Title of Recommendation]

- **Why**: [Operational risk of not addressing this knowledge gap]
- **GCP Enablement & Tooling**: [Specific training resources, managed GCP services, or best practice whitepapers]
- **Implementation Highlights**: [Brief technical enablement/setup overview]

### 📈 P1: Enhancements & Secondary Enablement

#### 1. [Title of Recommendation]

...

### 📚 P2: Long-Term / Optional Enablement

#### 1. [Title of Recommendation]

...

---

## 5. Technical Objections & Risk Mitigation

- **Identified Objection**: [e.g., Multi-region synchronization cost or complexity]
- **GCP Mitigation**: [How GCP services and best practices mitigate the risk or simplify operations]
```
