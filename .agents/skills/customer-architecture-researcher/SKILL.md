---
name: customer-architecture-researcher
description: >-
  Researches and architectures cloud and multi-cloud solutions for Customer Engineering (CE) inquiries.
  Use when a user asks for architectural research, cross-cloud networking design, hybrid topologies,
  or solution analysis (e.g., "Customer wants to build a multi-cloud architecture... What would cross-cloud
  networking look like... Build me a network diagram"). Guides interactive human data enrichment with
  ask_question, multi-source RAG research via Google Developer Knowledge MCP, Moma, and WAF verification,
  and outputs a comprehensive research paper report with diagrams, communication sequence charts, citations,
  and Pre-GA feature alerts.
---

# Customer Architecture Researcher (CE Solution Researcher)

This skill provides the procedural cheatsheet for researching, designing, and validating enterprise Google Cloud and multi-cloud architectures from Customer Engineering (CE) prompts.

## 📋 Execution Workflow

- [ ] **Step 1: Mandatory WAF Discovery via Native WAF Skill (`agent-waf-system`)**
  - **NEVER** assume customer priorities (e.g. jumping directly to VPN without asking about latency, bandwidth, SLA, and cost).
  - If the prompt does not explicitly state these requirements, invoke the native **`agent-waf-system`** skill (or delegate to its sub-skills `ce-adr-questionnaire-assistant` and `/run-waf-audit`) to conduct structured WAF discovery via `ask_question`.
- [ ] **Step 2: MCP-Driven RAG Research & Citation Sourcing**
  - **NEVER guess or synthesize citation URLs**. You **MUST** use MCP tools (`call_mcp_tool`) to search for authoritative, verified reference documentation.
  - Query **Google Developer Knowledge MCP** (`google-developer-knowledge`) for official public GCP documentation URLs.
  - Query **Moma** (`moma`) for internal engineering architecture patterns and design references.
  - See [MCP Research Guide](references/mcp_research_guide.md) for detailed tool queries and verification protocols.
- [ ] **Step 3: Audit Pre-GA / Preview Features**
  - Verify launch stages of all proposed features.
  - Explicitly call out any Alpha, Beta, or Preview features in the report's top alert block along with required enablement flags.
- [ ] **Step 4: Mandatory High-Def Diagram Generation (`creating-gcp-diagrams`)**
  - Build high-fidelity Mermaid drafts for architectural topology and communication sequence charts.
  - **Mandatory Diagram Execution**: You **MUST** execute the **`creating-gcp-diagrams`** skill to generate a high-definition flat 2D vector PNG architecture diagram anchored by local Google Cloud Category Icons.
  - Save the rendered PNG asset directly to `references/<customer_name>/assets/architecture_diagram.png` (or `meeting/<customer_name>/assets/architecture_diagram.png`) and embed it in Section 2 of the report.
- [ ] **Step 5: Save & Actively Validate Report in Target Reference Folder**
  - Generate the finalized research paper report using the structure in [report_template.md](assets/report_template.md).
  - **Mandatory File Saving Path**: Save the report to `references/<customer_name>/research_report.md` (or `meeting/<customer_name>/research_report.md`).
  - **Mandatory Asset Saving Path**: Save all generated images, diagrams, and supplementary resources to `references/<customer_name>/assets/`.
  - **Mandatory Active Online Link Validation**: You **MUST** run `validate_citations.py <path> --online` to verify liveness of all citation and resource links before delivering the report.

---

## 🚀 Quick Recipes & Commands

### 1. Mandatory Online Citation & Link Validation

Before delivering the report artifact, you **MUST** execute the bundled verification script with the `--online` flag to perform live HTTP requests:

```bash
python3 .agents/skills/customer-architecture-researcher/scripts/validate_citations.py <path_to_report.md> --online
```

_Rule: If any link fails online validation, immediately query `google-developer-knowledge` via MCP to retrieve a valid replacement link, update the document, and re-verify!_

### 2. Mandatory Directory & Asset Layout

Always structure the output folder cleanly:

```
references/<customer_name>/
├── research_report.md          # Primary research report artifact
└── assets/                     # All visual assets and supplementary resources
    ├── architecture_diagram.png # Rendered 2D vector PNG via creating-gcp-diagrams
    └── sequence_chart.png       # Rendered sequence flow diagram
```

---

## 💡 Gotchas & Pitfalls

- **Skipping `creating-gcp-diagrams` Execution**: A research report without a rendered high-definition PNG diagram is incomplete. You must invoke `creating-gcp-diagrams` and call `generate_image`.
- **Jumping to Solutions Without WAF Discovery**: Recommending HA VPN when the customer actually requires sub-10ms 100Gbps Dedicated Interconnect is a major architectural error. Always delegate to the native `agent-waf-system` skill in Step 1.
- **Hallucinating Documentation URLs**: Never guess or invent `cloud.google.com` link paths from LLM memory. You must actively use MCP search tools to obtain exact URLs and validate them online.
- **Skipping Online Validation**: Delivering dead or 404 links damages credibility. Always run `validate_citations.py` with `--online`.
- **Ignoring Preview/Pre-GA Status**: Enterprise customers require stability. Suggesting a Pre-GA feature without a prominent warning in the Executive Summary alert box is a critical failure.
- **Scattered Artifacts**: Do not dump report files in flat root directories. Always save inside a dedicated customer folder (`references/<customer_name>/`) with an `assets/` subdirectory.

---

## 📁 Reference Assets & Guidelines

- **[MCP Research & Verification Guide](references/mcp_research_guide.md)**: Deep dive on MCP search queries, diagram generation via `creating-gcp-diagrams`, and WAF validation using native `agent-waf-system`.
- **[Report Template](assets/report_template.md)**: Mandatory Markdown report layout including diagram scaffolds and citation formatting.
