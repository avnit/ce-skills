# Human-In-The-Loop (HITL) Interactive Protocol

## Why HITL is Mandatory in Horizon Capacity Management

Capacity reservations in Google Cloud (`go/horizon`) directly influence regional stockouts, data center buildout timelines, and physical hardware allocations (GPUs, TPUs, Hyperdisks, GCE vCPUs).

Because ~80% of inorganic or strategic requests require specialized engineering review and allocation (`go/cloud-ca` / `go/ccnp-ops`), an agent working on behalf of a Customer Engineer (CE) or Account Team must **never** autonomously submit, create, or modify a capacity proposal without explicit verification from the human user.

## `ask_question` Tool Specification

Right before invoking `CreateCapacityDemand`, `UpdateCapacityDemand`, or `SubmitCapacityDemand`, the agent MUST invoke the `ask_question` tool with a well-formatted proposal summary and choice selection.

### Tool Call Configuration

```json
{
  "questions": [
    {
      "question": "Verify and Approve Horizon Capacity Demand Submission",
      "options": [
        "(Recommended) [Confirm & Submit] All dimensions, SKU, RAM ratio, and justifications verified. Proceed with submission.",
        "[Modify Request] I want to adjust specific fields (e.g., SKU, cores, ramp schedule, location) before submitting.",
        "[Cancel] Do not create or submit this demand at this time."
      ],
      "is_multi_select": false
    }
  ]
}
```

### Pre-Question Presentation Sheet

Before calling `ask_question`, output a Markdown table or bullet list in the chat summarizing the core proposal parameters so the CE can inspect every dimension:

```markdown
### 📋 Proposed Horizon Capacity Demand Setup

| Attribute                 | Value                                  | Source / Rationale                                              |
| :------------------------ | :------------------------------------- | :-------------------------------------------------------------- |
| **Customer ID / Project** | `external/12345` (`prj-my-prod`)       | Explicit CE input                                               |
| **Target Location**       | `us-central1`                          | Explicit CE input                                               |
| **Shapeless / Shaped**    | **Shapeless** (`n2-standard`)          | Defaulted (`Zero Override Rule`)                                |
| **CPU Cores / RAM**       | `480 vCPUs` / `1920 GB RAM`            | RAM calculated via 1:4 ratio from `resource_metadata.textproto` |
| **Ramp Start / Target**   | `2026-Q3` -> `2026-Q4`                 | Historical demand precedent                                     |
| **Justification**         | Inorganic expansion for AI inferencing | Linked Buganizer `#36912345`                                    |
| **Validation Status**     | ✅ PASSED (`demand_validator.py`)      | Offline schema & enum verification                              |
```

## Handling User Responses

### Scenario A: CE selects `[Confirm & Submit]`

1. Execute the RPC using the serialized integer enum payload (`state: 1` for `DRAFT` or `state: 4` for `SUBMITTED`).
2. Verify the return payload contains a valid `request_id`.
3. Render the confirmation card with the clickable Horizon portal link:
   `https://horizon-staging.corp.google.com/customers/external/{customer_id}/projects/{project_number}/review?requestId={request_id}`

### Scenario B: CE selects `[Modify Request]`

1. Prompt the CE or process their write-in feedback indicating which field to alter (e.g., _"Change location to us-east4 and boost RAM to 2048 GB"_).
2. Apply the requested updates to the JSON structure.
3. Re-run `demand_validator.py` on the modified payload.
4. Re-invoke the `ask_question` tool with the newly updated proposal table. Do **not** skip the second confirmation.

### Scenario C: CE selects `[Cancel]`

1. Output: _"Capacity demand creation cancelled by user request. No external changes made."_
2. Terminate the workflow cleanly.
