---
name: customer-test-plan
description: >-
  Guides the creation of a unified, non-duplicative Validation Test Plan (test_plan.md) that leverages the active codelab-validation engine (tester.py) to execute and verify the solution design.
---

# Customer Test Plan (Stage 5)

This skill defines the methodology for authoring the **Test Plan** (`test_plan.md`). To completely eliminate duplicated effort and establish rigid validation governance, a pre-sales Consulting Engineering Test Plan **MUST NOT** duplicate deployment logic into custom shell scripts.

Instead, it acts as a **Structured Test Harness Manifest** that links directly to the generated **DevSite Codelab** (`.lab.md` file) and leverages our unified **`codelab-validation`** execution engine (`tester.py`) to automate sandbox provisioning, resource deployments, and E2E verification natively.

## Workflow

- [ ] Step 1: Extract the target DevSite Codelab file pathway generated in Phase 6 (e.g. `labs/dev/customer-a-storage/customer-a-storage.lab.md`).
- [ ] Step 2: Define the exact E2E verification parameters, success assertions, and prerequisite states inside `test_plan.md`.
- [ ] Step 3: Document the unified validation execution command referencing `tester.py` to allow the Consulting Engineer or test-runner to run the entire E2E lifecycle dynamically.
- [ ] Step 4: Save the finalized Test Plan directly to `meeting/<customer_name>/test_plan.md`.

## Analysis Prompt

Use the unified discovery and solutions architect system prompt defined in [discovery_analyst.md](file:///prompts/discovery_analyst.md) passing the target flag: `--format test_plan`.

---

## 🛡️ Full Architectural Validation Parity & Active Verification (SYN-02)

When authoring `test_plan.md`, you **MUST strictly enforce full architectural validation parity**:
1. **No Skipped Layers or Mock Checks**: The test plan must actively validate the complete architectural design topology specified in `design_blueprint.md`. If the blueprint defines GKE clusters, custom VPC networks, node pools, PSC endpoints, or AlloyDB instances, `test_plan.md` MUST include explicit bash commands and configuration steps to provision and verify those actual resources.
2. **Active Verification Test Harnesses**: Do not rely on passive checks or assumptions. Incorporate active verification scripts or test harnesses (such as synthetic workload generation, active connectivity probing, or real payload execution) to prove that the architecture functions end-to-end under realistic operating conditions.

---

## Test Plan & Harness Manifest Template

Every Test Plan generated for a customer MUST conform to this unified integration standard:

````markdown
# Validation Test Plan & Harness Manifest: [Customer Name] - [Project Name]

This Test Plan acts as the structured validation harness manifest. It binds our technical design directly to the hands-on **DevSite Codelab** and utilizes our unified **Codelab Validation Engine** (`tester.py`) to orchestrate E2E sandbox testing.

---

## 1. Target Validation Assets

- **Reference Design**: `[design_blueprint.md](design_blueprint.md)`
- **Execution Codelab**: `[customer-a-storage.lab.md](../../labs/dev/customer-a-storage/customer-a-storage.lab.md)`
- **Verification Engine**: `[codelab-validation/tester.py](../../.agents/skills/codelab-validation/scripts/tester.py)`

---

## 2. How to Execute Unified E2E Validation

To execute the E2E validation tests, run our centralized, stateful `tester.py` execution engine targeting our generated test plan or codelab:

```bash
# Run the unified stateful validation engine
python3 .agents/skills/codelab-validation/scripts/tester.py \
    meeting/customer_a/test_plan.md \
    --artifact-dir meeting/customer_a/validation_artifacts \
    --skip-cleanup
```
````

### What the Validation Engine Automates:

1. **Interactive Scoping**: Reads the codelab or test plan steps, parses variables (e.g., Project ID, region), and prompts for confirmation.
2. **Sandbox Provisioning**: Connects to the pre-sales environment, links billing, and disables restrictive organization policies using `disable_org_policies.sh <project_id>`.
3. **Dynamic Provisioning**: Allocates VPC Private Service Access (PSA), creates GCS HNS buckets recursively, and deploys the GKE cluster nodes.
4. **Stateful Dynamic Claims**: Provisions GKE Filestore Enterprise (RWX) and Hyperdisk (RWO) volumes and mounts them inside microservice Pods.
5. **Functional E2E Assertions**: Sync-writes test payloads inside pods and triggers managed Storage Transfer Service (STS) batch ingress jobs, asserting file delivery.
6. **Automated Environmental Teardown**: Triggers project resource deletion upon validation success (unless `--skip-cleanup` is specified) to ensure zero ongoing cost leakage.

```
---

## Gotchas & Operational Standards

- **Single Source of Truth**: By routing testing through `tester.py` targeting the `.lab.md` or `test_plan.md` file, any bug discovered during validation is immediately fixed inside the source file itself. This ensures that both the customer tutorial and the automated testing scripts remain 100% correct and identical.
```
