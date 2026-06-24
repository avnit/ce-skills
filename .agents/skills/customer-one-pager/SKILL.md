---
name: customer-one-pager
description: >-
  Analyzes discovery call transcripts to create a comprehensive One-Pager summarizing the customer context, pain points, and the suggested design/plan.
---

# Customer One-Pager Generation

This skill outlines the methodology for creating a concise "One-Pager" summary from a customer discovery call transcript. The One-Pager captures the essential business and technical context and the proposed path forward.

## Agent Implementation Directives
Whenever executing this skill on behalf of the user:
1. **Task Tracking**: Agents **MUST** initialize and maintain a standardized HTML task tracking table (`task.md`) completely flush left without leading spaces. Update row progression states dynamically as execution steps resolve.
2. **Persistent Document Saving**: Agents **MUST** save the finalized One-Pager document directly to the repository filesystem under a dedicated customer folder inside the `meeting/` directory (e.g., using `write_to_file` with `IsArtifact: false` specifying a clear project path like `meeting/<customer_name>/one_pager.md`) rather than flat chat outputs.

---

## Workflow

Follow these steps when applying this skill:
- [ ] Step 1: Review the discovery call notes or transcript.
- [ ] Step 2: Extract key information:
    - Customer business goals and drivers.
    - Technical pain points and constraints.
    - Agreed or proposed solution direction.
- [ ] Step 3: Synthesize the information into the **One-Pager Template**.
- [ ] Step 3.5: Embed a design or architecture diagram if applicable and available.
- [ ] Step 4: Save the finalized One-Pager document directly into the target customer folder under `meeting/` and share the clickable file link with the user.

---

## Analysis Prompt

Use the unified discovery and solutions architect system prompt defined in [discovery_analyst.md](file:///prompts/discovery_analyst.md) passing the target flag: `--format one_pager`.

---

## One-Pager Template

Use this exact structure to output the analysis to the user:

```markdown
# Customer One-Pager: [Customer Name] - [Project Name]

## 1. Executive Summary
[A concise 3-4 sentence summary of the customer's situation, the core problem, and the proposed solution].

## 2. Context & Pain Points
- **Business Driver**: [Why are they doing this now? e.g., cost reduction, scaling issues]
- **Technical Challenges**:
    - [Point 1: e.g., Stuck CSI driver pods causing downtime]
    - [Point 2: e.g., Lack of automated GPU error handling]

## 3. Proposed Solution & Architecture
- **High-Level Design**: [Description of the suggested solution, e.g., Auto-healing script + Whitepaper guidance]
- **Key Components**:
    - **Component 1**: [e.g., GKE with GCSfuse]
    - **Component 2**: [e.g., Monitoring CronJob]

### 🖼️ Architecture Diagram (If Applicable)
![Architecture Diagram](absolute_path_to_image)

## 4. Action Plan & Next Steps
- **Immediate (P0)**: [e.g., Share action plan document for 3 PM call]
- **Short-Term (P1)**: [e.g., Implement sample auto-healing script]
- **Long-Term (P2)**: [e.g., Deliver whitepaper on GPU error handling]

## 5. Key Stakeholders & Owners
- **Customer Lead**: [Name/Role if known]
- **GCP Lead**: [Name/Role if known]
```

## Gotchas & Pitfalls to Avoid
- **Too much detail**: Keep it to one page (or equivalent scrolling length). Focus on high-level summary, not deep dive.
- **Missing the "So What?"**: Ensure the business value of the proposed solution is clear.
- **Vague next steps**: Ensure action items have clear owners and priorities if available.
