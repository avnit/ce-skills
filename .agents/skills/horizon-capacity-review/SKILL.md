---
name: horizon-capacity-review
description: >-
  Reviews, validates, and submits Google Cloud capacity demands (formerly Cloud CA / QIR / CCA) using the Horizon DemandManager API on behalf of Customer Engineers (CEs) and Account Teams inside Cider/Jetski. Enforces mandatory human-in-the-loop (HITL) interactive confirmation via the `ask_question` tool before executing irreversible create, update, or submit operations. Use when reviewing customer capacity assessments (CCAs), auto-filling demand gaps, verifying GPU/TPU or hyperdisk inventory requirements, checking shaped vs. shapeless configurations, running pre-submission validation scripts via `run_command`, or submitting formal Horizon capacity plans. Don't use for routine quota adjustments in Cloud Console that don't require physical capacity reservation, general code generation (use ai-coder), or ad-hoc Spanner database queries.
---

# Horizon Capacity Review & Submission (`Jetski/Cider Edition`)

This skill defines the authoritative workflow for Customer Engineers (CEs), TAMs, and Account Teams using Gemini Coder / Jetski inside Cider to review, validate, and submit capacity requests in Horizon (`go/horizon`, replacing `go/cloud-ca`).

## Workflow Overview

Follow this exact four-phase procedure for every capacity review and submission task:

1. **Intake & Contextualization**: Read linked Buganizer tickets and fetch existing demands to establish baseline parameters.
2. **Auto-Fill & Pre-Validation**: Run offline validation via `run_command` and auto-fill gap fields without overriding explicit CE inputs (`Zero Override Rule`).
3. **Interactive HITL Confirmation**: Invoke the `ask_question` tool to present a verified summary table on multiple-choice options before mutating external state.
4. **Execution & UI Verification**: Execute the mutation and return a canonical review URL for the Horizon portal.

---

## 1. Intake & Contextualization

Before drafting or updating a capacity demand, establish complete context:

- **Read Linked Bugs**: If a Buganizer ticket ID is provided (or referenced in historical QIRs), first check ticket status and summarize recent comments. A demand review is incomplete without the linked bug context (`Why`: CEs need to verify underlying business justifications before approving hardware reservations).
- **Identify Request Nature**: Disambiguate whether the user needs an organic growth quota bump or an **Inorganic/Strategic Capacity Assessment (CCA)** for specialized hardware (e.g., A100/H100/v5p TPUs, Hyperdisk). Consult [cca_to_horizon_mapping.md](references/cca_to_horizon_mapping.md) for legacy definitions.
- **Fetch Similar Demands**: Run `stubby call cloud.capacity.horizon.platform.services.demandmanager.DemandManager/ListCapacityDemand` (via `run_command`) or use local read tools to locate historical precedents for the same customer/project:
  - Filter by `CAPACITY_DEMAND_STATE_ACKNOWLEDGED`, `SUBMITTED`, or `UNDER_ASSESSMENT`.
  - _Note on Enums_: Read queries (`ListCapacityDemand`) require **string enum names** in AIP-160 filter syntax (`customer_information.sub_region="NORTHAM"`). See [api_guide.md](references/api_guide.md) for full filter structure.

---

## 2. Auto-Fill & Pre-Validation

### Zero Override Rule

Do not override any fields explicitly specified by the CE or customer (e.g., regions, CPU/GPU counts, ramp start dates). Explicit user inputs take absolute precedence (`Why`: overriding CE parameters violates external customer SLA agreements). Use historical demands from Step 1 only to populate un-specified gap fields (metadata, secondary preferences, flexibility options).

### Shaped vs. Shapeless Defaulting

- **Shapeless by Default**: Unless the CE explicitly requests a concrete machine shape (e.g., `n2-standard-48` or `a2-highgpu-8g`), default to a **shapeless** demand.
- **RAM Calculation**: For shapeless requests, compute total memory (GB) from CPU cores using the ratios in `//depot/google3/cloud/capacity/horizon/shared/configdata/config/prod/resource_metadata.textproto` (`1:4` vCPU-to-RAM standard ratio). See [workload_templates.md](references/workload_templates.md) for ratio lookups.
- **Shaped Hardware**: For specialized compute (GPUs, TPUs, bare metal), inspect [workload_templates.md](references/workload_templates.md) to verify required attributes (`planning_sku`, chip counts, interconnect definitions).

### Run Local Pre-Validation via `run_command`

Before preparing the request for human confirmation, run the offline Python validator on your JSON payload string (`--payload_json`) using `run_command` in Cider:

```bash
blaze run //experimental/users/shacharb/skills/horizon-capacity-review/scripts:demand_validator -- --payload_json='{"customer_id": "external/12345", "location": "us-central1", "state": 1, "resources": [{"cpu_cores": 480, "ram_gb": 1920, "ramp_schedule": [{"start_date": "2026-Q3"}]}]}'
```

_(Alternatively, write the JSON to `scratch/proposal.json` and pass `--demand_json_path=scratch/proposal.json`)._

If the binary reports validation errors or enum mismatches, resolve them cleanly before prompting the CE.

---

## 3. Interactive HITL Confirmation (CE Verification)

**CRITICAL SAFETY REQUIREMENT**: Horizon capacity submissions trigger live inventory reservations (`F1`/`BwE` allocations and regional data center buildouts across `go/ccnp-ops`). Submitting unverified or premature requests locks up physical compute and risks immediate rejection by Cloud Capacity Operations.

Before calling `CreateCapacityDemand`, `UpdateCapacityDemand`, or `SubmitCapacityDemand`, you **MUST** call the `ask_question` tool to solicit explicit confirmation from the CE.

- **Pre-Question Presentation**: First display a clean Markdown summary table containing every proposed dimension (`Customer ID`, `Location`, `Shapeless/Shaped`, `Cores/RAM`, `Ramp Schedule`, `Bug Justification`).
- **`ask_question` Configuration**: Configure the options array (`[Confirm & Submit]`, `[Modify Request]`, `[Cancel]`) exactly as mandated in [hitl_protocol.md](references/hitl_protocol.md).
- **Response Handling**:
  - If `[Confirm & Submit]` is selected: Proceed to Section 4.
  - If `[Modify Request]` is selected: Gather the CE's requested parameter edits, update the JSON structure, re-run `demand_validator`, and trigger a fresh `ask_question` confirmation dialog.
  - If `[Cancel]` is selected: Abort cleanly without mutating any state.

---

## 4. Execution & UI Verification

### Payload Serialization

- When constructing `CreateCapacityDemand` or `UpdateCapacityDemand` mutation payloads, always encode enums as **integer** values (e.g., `"state": 1` for `DRAFT`). See [api_guide.md](references/api_guide.md) for full enum-to-integer mapping tables.
- You may only invoke `UpdateCapacityDemand` on existing demands that are currently in `CAPACITY_DEMAND_STATE_DRAFT` (`int: 1`). Never attempt to update requests that are `SUBMITTED` (`int: 4`) or `ACKNOWLEDGED` (`int: 3`).

### Provide Actionable UI Confirmation

Upon successful creation or submission, output a clear confirmation card along with the canonical Horizon review URL so the CE can inspect the request right in the web portal:

```markdown
✅ **Capacity Demand Submitted Successfully**

- **Demand ID**: `{request_id}`
- **Status**: `SUBMITTED`
- **Primary SKU / Shape**: `{sku_or_shape}`
- **Total Cores / RAM**: `{cores} vCPUs / {ram} GB`
- **Target Location**: `{location}`
- **Review in Horizon Portal**: [Inspect Demand #{request_id}](https://horizon-staging.corp.google.com/customers/external/{customer_id}/projects/{project_number}/review?requestId={request_id})
```

_(Note: If `project_number` is internal or invalid, omit the URL and show only `request_id` and summary)._

---

## References & Helper Scripts

- [HITL Interactive Protocol](references/hitl_protocol.md): `ask_question` option definitions, pre-question Markdown tables, and loop handling.
- [Horizon API & RPC Guide](references/api_guide.md): `DemandManager` RPC methods, integer vs. string enum rules, and transient retry logic.
- [CCA to Horizon Mapping](references/cca_to_horizon_mapping.md): Historical `go/cloud-ca` (CCA) concepts, QIR distinction, and entity migration.
- [Workload Templates & RAM Ratios](references/workload_templates.md): Guidance for shaped vs. shapeless memory calculations and `seamless` FPS data references.
- [Example Shapeless Proposal](examples/shapeless_demand.json): Clean reference payload for a standard organic growth demand.
- [Example Shaped GPU Proposal](examples/shaped_gpu_demand.json): Clean reference payload for an A100/H100 inorganic capacity demand.
