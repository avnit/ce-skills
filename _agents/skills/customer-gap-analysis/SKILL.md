---
name: customer-gap-analysis
description: >-
  Analyzes raw discovery calls, meeting notes, and transcripts to build a Gap Analysis Report for the customer. Focuses on comparing Current vs. Desired state, building a gap severity matrix, and providing structured, prioritized recommendations mapped to GCP solutions.
---

# Customer Gap Analysis Skill

This skill outlines the systematic methodology for analyzing customer discovery calls and workshops to identify gaps in architecture, security, processes, and reliability, and framing those gaps into prioritized recommendations mapping to Google Cloud solutions. 

## Workflow

Follow these steps when applying this skill:
- [ ] Step 1: Review the discovery call notes or transcript.
- [ ] Step 2: Extract the Customer's **Current State** (architecture, tooling, workflow) and **Desired State** (business goals, architecture targets).
- [ ] Step 3: Fill out the **Gap Analysis Matrix**, scoring each gap based on severity (High, Medium, Low).
- [ ] Step 4: Map solutions and architectural mitigations to these gaps using Google Cloud solutions.
- [ ] Step 5: Provide a prioritized recommendation roadmap (P0 critical, P1 enhancements, P2 long-term optimizations).
- [ ] Step 6: Present the Gap Analysis Report artifact to the user.

---

## Gap Analysis Report Template

Use this exact structure to output the analysis to the user:

```markdown
# Customer Gap Analysis: [Customer Name]

## 1. Executive Summary
[1-2 paragraphs outlining the customer's business goals, high-level context of the discovery session, and summary of the most critical gaps identified].

## 2. Current vs. Desired State

### 🏗️ Architecture & Infrastructure
- **Current State**: [Current tooling, cloud providers, setup architecture, scale]
- **Desired State**: [Target architecture, requirements, target KPIs]

### 🔒 Security & Compliance
- **Current State**: 
- **Desired State**: 

### 🚀 Developer Velocity & CI/CD
- **Current State**: 
- **Desired State**: 

---

## 3. Gap Analysis Matrix

| Capability / Domain | Current State | Desired State | Gap Severity (High/Med/Low) | Recommended GCP Solution |
| :--- | :--- | :--- | :--- | :--- |
| e.g. Distributed Tracing | No tracing. Standard logs on VMs. | End-to-end distributed tracing across multi-cloud. | High | Cloud Trace & OpenTelemetry |
| | | | | |

---

## 4. Recommended Improvements & Action Roadmap

### 🚨 P0: Critical Path Improvements (Must Fix First)
#### 1. [Title of Recommendation]
- **Why**: [Impact of the current gap and consequence of not fixing it]
- **GCP Tooling**: [e.g., Cloud Armor, AlloyDB, GKE Enterprise]
- **Implementation Highlights**: [Brief bulleted architecture / setup overview]

### 📈 P1: Enhancements & Secondary Optimizations
#### 1. [Title of Recommendation]
...

### 📚 P2: Long-Term / Optional Optimizations
#### 1. [Title of Recommendation]
...

---

## 5. Technical Objections & Risk Mitigation

- **Identified Objection**: [e.g., Lock-in concerns, operational complexity]
- **GCP Mitigation**: [How the suggested GCP tools and architecture mitigate the risk]
```

## Gotchas & Pitfalls to Avoid
- **Vague recommendations**: Never say "Move to Cloud Run". Explain how moving to Cloud Run solves their developer velocity issues and fits their stateless server framework.
- **Skipping Objections**: If the customer expresses concerns (e.g. multi-region costs, latency, multi-cloud compatibility), proactively address them in the Technical Objections section.
- **Ignoring Existing Investments**: If a customer runs Postgres on-premise and loves it, recommend AlloyDB or Cloud SQL for Postgres rather than pitching Spanner directly without context. 
