# Workload Templates & RAM Calculation Guide

## Shapeless vs. Shaped Capacity Intake

Horizon supports two core intake modes when defining `ResourceDemand` slices for a customer:

### 1. Shapeless Intake (Default)

- **When to Use**: For standard organic compute growth, GKE autoscaling workloads, or general microservices where the customer needs guaranteed core capacity but does not require a specific hardware VM family locked to a physical node profile.
- **RAM Calculation Rule**: When a CE specifies only `cpu_cores` in a shapeless demand, you MUST automatically calculate total `ram_gb` by applying the service ratio from `resource_metadata.textproto` (`//depot/google3/cloud/capacity/horizon/shared/configdata/config/prod/resource_metadata.textproto`).
  - _Standard GCE Ratio_: Typically 1 vCPU : 4 GB RAM (`1:4`). E.g., `480 vCPUs` -> `1920 GB RAM`.

### 2. Shaped Intake (Specialized Hardware)

- **When to Use**: For specialized accelerator workloads (GPUs like A100/H100/L4, TPUs like v4/v5p/v6), High-Memory instances (`m2-ultramem`), or high-throughput Hyperdisk storage where specific rack constraints, interconnects (`TUBE C2C`), and machine profiles are non-negotiable.
- **Required Attributes**: When a machine shape (e.g., `a2-highgpu-8g` or `ct5p-hightpu-4t`) is provided, you MUST inspect the corresponding product definition under `//depot/google3/cloud/capacity/seamless/data/products/` and workload templates (`//depot/google3/cloud/capacity/horizon/shared/configdata/proto/workload_templates.proto`).
- **Metadata Validation**: Ensure exact `planning_sku`, GPU/TPU chip count, and interconnect parameters match the canonical FPS definition before passing the proposal to `demand_validator.py`.

## Template Lookup Paths across Environments

When resolving `WorkloadTemplate` profiles during validation or proposal creation, check the environment-specific configs:

| Environment           | Depot Path                                                                                     |
| :-------------------- | :--------------------------------------------------------------------------------------------- |
| **Prod**              | `//depot/google3/cloud/capacity/horizon/shared/configdata/config/prod/workload_templates/`     |
| **Nonprod / Staging** | `//depot/google3/cloud/capacity/horizon/shared/configdata/config/nonprod/workload_templates/`  |
| **Autopush**          | `//depot/google3/cloud/capacity/horizon/shared/configdata/config/autopush/workload_templates/` |

Always confirm with the CE via `ask_question` if the selected `planning_sku` deviates from the customer's historical request profile.
