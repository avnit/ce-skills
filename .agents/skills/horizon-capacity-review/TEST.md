# Test Manual Verification Guide: `horizon-capacity-review`

This document provides a step-by-step verification plan for testing and executing the `horizon-capacity-review` skill during review and submission cycles.

## Prerequisites & Setup

Ensure the developer / CE workspace has access to the skill rules and local validator tool:

```bash
# Build the local validation script binary with inline payload_json support
blaze build //experimental/users/<username>/skills/horizon-capacity-review/scripts:demand_validator
```

## Scenario 1: Shapeless Demand Intake & HITL Submission

### Step 1: Prompt the Agent

Issue the following natural language task in chat inside Cider/Jetski:

> _"I am a CE reviewing an organic compute demand for customer `external/987654321` in `us-central1`. They requested 480 vCPUs starting in Q3 2026. Please draft the proposal, run validation, and prepare for human verification."_

### Step 2: Verify Auto-Fill & Pre-Validation

- **Check**: Ensure the agent defaults to shapeless and computes `1920 GB RAM` (`1:4` ratio).
- **Check**: Verify the agent executes `demand_validator.py` (`--payload_json='...'`) on the generated JSON proposal and flags any missing justifications before calling any tools.

### Step 3: Verify Interactive `ask_question` Modal

- **Check**: Verify the agent invokes `ask_question` displaying:
  - Title: `Verify and Approve Horizon Capacity Demand Submission`
  - Summary Markdown table with all dimensions (`external/987654321`, `us-central1`, `480 vCPUs / 1920 GB RAM`).
  - Options: `[Confirm & Submit]`, `[Modify Request]`, `[Cancel]`.

### Step 4: Confirm Submission

Select `[Confirm & Submit]` in the modal.

- **Check**: The agent invokes `CreateCapacityDemand` / `SubmitCapacityDemand` using valid integer enum (`state: 1` or `state: 4`).
- **Check**: The agent outputs the clickable portal confirmation link: `https://horizon-staging.corp.google.com/customers/external/987654321/projects/123456789012/review?requestId=...`.

---

## Scenario 2: Shaped GPU Demand & HITL Modification Loop

### Step 1: Prompt the Agent

> _"Prepare a Horizon capacity request (formerly Cloud CA) for `external/12345` for 8x H100 GPUs (`a3-megagpu-8g`) in `us-central1` for strategic training."_

### Step 2: Verify `ask_question` Modal

- **Check**: The agent validates the proposal for `planning_sku: a3-megagpu-8g-h100` and presents the `ask_question` confirmation modal.

### Step 3: Test `[Modify Request]` Loop

Select `[Modify Request]` in the modal and respond: _"Change location to `us-east4` and set ramp start to Q4 2026."_

- **Check**: The agent modifies the JSON payload without losing user overrides (`Zero Override Rule`).
- **Check**: The agent re-runs `demand_validator.py` (`--payload_json`).
- **Check**: The agent triggers a **second** `ask_question` confirmation modal containing the newly updated table before submitting.
