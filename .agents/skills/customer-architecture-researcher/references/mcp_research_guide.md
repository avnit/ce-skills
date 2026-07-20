# MCP Research & Verification Guide

This guide outlines the multi-source RAG research, authoritative citation sourcing, high-definition diagram generation, and online verification methodology required when generating customer architecture research reports.

---

## 1. Native WAF Discovery via `agent_waf_system` (`ask_question`)

When a Customer Engineering (CE) prompt or question lacks critical context (e.g., bandwidth requirements, existing cloud providers, security constraints, IP overlap constraints, or hybrid connectivity preference), you **MUST NOT** hallucinate or assume arbitrary requirements.

### Protocol:

1. Do not replicate custom WAF questionnaires. Instead, delegate directly to the native **`agent_waf_system`** skill (and its sub-skills `ce-adr-questionnaire-assistant` or the `/run-waf-audit` workflow).
2. Use `ask_question` as instructed by the native WAF skill to gather customer trade-off preferences (bandwidth, latency, SLA, cost vs. redundancy).
3. Document the customer's selected priorities directly in Section 1 (Executive Summary) and Section 4 (WAF Alignment) of the research report.

---

## 2. Mandatory File & Asset Saving Paths

To ensure clean workspace organization and prevent file clutter, all deliverables produced by this skill must be stored in a structured reference folder:

### Directory Structure:

```
references/<customer_name>/
├── research_report.md          # Main architectural research report
└── assets/                     # Subfolder for all images and resources
    ├── architecture_diagram.png # Rendered high-def 2D vector diagram
    ├── sequence_chart.png       # Rendered request flow diagram
    └── custom_resource.yaml     # Supplementary config files (if any)
```

_Note: If operating inside an active customer meeting context, `meeting/<customer_name>/` may be used as the root folder instead of `references/<customer_name>/`._

---

## 3. High-Definition Diagram Generation via `creating-gcp-diagrams`

**CRITICAL MANDATE: Every research report MUST include a high-definition flat 2D vector PNG architecture diagram.** You must execute the **`creating-gcp-diagrams`** skill to generate this asset.

### Category Icon Anchoring Table:

Select up to 3 local reference category icons from `.agents/skills/creating-gcp-diagrams/assets/category-icons/Category Icons/` to anchor the rendering style:

| Architectural Component  | Target Local Reference Asset Path                      |
| :----------------------- | :----------------------------------------------------- |
| **VPCs, Routers, VPNs**  | `Networking/PNG/Networking-512-color.png`              |
| **VMs, MIGs, Compute**   | `Compute/PNG/Compute-512-color.png`                    |
| **Security, IAP, Armor** | `Security Identity/PNG/SecurityIdentity-512-color.png` |
| **AlloyDB, Cloud SQL**   | `Databases/PNG/Databases-512-color.png`                |
| **GKE, Containers**      | `Containers/PNG/Containers-512-color.png`              |

### `generate_image` Execution Payload Example:

Call the `generate_image` tool directly with the selected local reference icon paths:

```json
{
  "Prompt": "Generate a professional flat 2D vector Google Cloud architecture diagram in official GCP style (#1A73E8 blue headers, #202124 dark text). Replicate the visual style of attached reference icons. Draw a Hub-and-Spoke multi-cloud network connecting remote AWS VPC over 4-tunnel HA VPN to GCP Hub VPC with Private Service Connect endpoint to GKE and AlloyDB in Spoke VPC.",
  "ImageName": "architecture_diagram",
  "AspectRatio": "16:9",
  "ImagePaths": [
    ".agents/skills/creating-gcp-diagrams/assets/category-icons/Category Icons/Networking/PNG/Networking-512-color.png",
    ".agents/skills/creating-gcp-diagrams/assets/category-icons/Category Icons/Security Identity/PNG/SecurityIdentity-512-color.png"
  ]
}
```

_Rule: Save the resulting image to `references/<customer_name>/assets/architecture_diagram.png` and embed it in Section 2 of the report._

---

## 4. MCP-Driven Citation Sourcing (`google-developer-knowledge`)

**CRITICAL MANDATE: Never synthesize, guess, or construct `cloud.google.com` links from memory.** You must actively use the lazy-loaded `google-developer-knowledge` MCP server to search for and retrieve the BEST authoritative reference URLs.

### Key Tools:

- **`call_mcp_tool` (Server: `google-developer-knowledge`, Tool: `search_documents`)**: Search for public whitepapers, architectural guides, and API documentation (e.g., query `"Cross-cloud network interconnect AWS Azure GCP"` or `"Private Service Connect hybrid DNS"`).
- **`call_mcp_tool` (Server: `google-developer-knowledge`, Tool: `get_documents`)**: Retrieve full text of documentation pages to extract precise CLI flags, IAM roles, and configuration limits.
- **Sourcing Rule**: Copy exact URLs returned by `search_documents` into your report's citation section.

---

## 5. Internal Engineering Research (`moma`)

For deep technical patterns, internal architectural design decisions, best practices, and internal guidance, query Moma.

### Key Tools:

- **`call_mcp_tool` (Server: `moma`, Tool: `search`)**: Perform internal searches across Google engineering documentation and design specs (e.g., query `"multi-cloud cross-cloud networking architecture patterns"` or `"WAF hybrid connectivity best practices"`).
- **`call_mcp_tool` (Server: `moma`, Tool: `internal_content_lookup`)**: Read specific internal engineering documents or design references discovered during search.

---

## 6. Active Online Link Validation Protocol

Every documentation citation and resource link included in the report **MUST be actively validated online by the agent** before delivering the document to the user.

### Execution Command:

Run the bundled verification CLI with the `--online` flag:

```bash
python3 .agents/skills/customer-architecture-researcher/scripts/validate_citations.py <path_to_report.md> --online
```

### Automated Remediation Loop:

1. If `validate_citations.py --online` returns `SUCCESS`, proceed with delivering the artifact to the user.
2. If `validate_citations.py --online` reports `FAILED` (e.g. 404 Not Found or dead link):
   - **DO NOT deliver the report with broken links.**
   - Immediately query `google-developer-knowledge` via `call_mcp_tool` using the citation title or topic as the query string.
   - Extract a working, authoritative URL from the MCP tool output.
   - Replace the broken URL in the report file using `replace_file_content`.
   - Re-run `validate_citations.py --online` until 100% of links pass validation.

---

## 7. Well-Architected Framework (WAF) Verification

To ensure enterprise-grade quality, audit the proposed design against the 5 pillars of the Google Cloud Well-Architected Framework (WAF) using the native `agent_waf_system` skill:

1. **Operational Excellence**: IaC deployment, telemetry, CI/CD, and audit logging.
2. **Security, Privacy & Compliance**: Least-privilege IAM, VPC Service Controls, encryption in transit/at rest.
3. **Reliability**: Fault isolation, regional redundancy (MIGs, HA VPN with dynamic BGP routing), disaster recovery.
4. **Cost Optimization**: Right-sizing, network egress optimization, Private Service Connect vs Peering cost tradeoffs.
5. **Performance Efficiency**: Latency optimization, bandwidth sizing, packet inspection throughput.

---

## 8. Pre-GA / Preview Feature Alerting

Enterprise architectures must distinguish between production-ready General Availability (GA) capabilities and experimental or preview features.

### Protocol:

1. For every product, API, or networking feature proposed (e.g., Cross-Cloud Interconnect, specific PSC capabilities, Cloud Armor features), check its launch stage during research via MCP tools.
2. If any feature is in **Alpha**, **Beta**, **Preview**, or **Pre-GA**:
   - Highlight it in the **Pre-GA / Preview Feature Alert** callout box at the top of the report.
   - Document any required whitelisting, org policy overrides, or special CLI flags required to enable it.
3. If all proposed features are GA, explicitly state that in the alert callout box to give the customer confidence.
