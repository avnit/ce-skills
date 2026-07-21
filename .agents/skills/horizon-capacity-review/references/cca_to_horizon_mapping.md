# CCA to Horizon Mapping Guide

## Overview: `go/cloud-ca` vs. `go/horizon`

Historically, Customer Engineers (CEs) submitted Capacity Assessments via `go/cloud-ca` (Cloud Capacity Advisor / CCA). Horizon (`go/horizon`) is the unified Google Cloud platform that replaced `go/cloud-ca`. Horizon serves as the centralized interface for capacity request intake, feasibility assessment, reservation, and fulfillment grants (`DemandManager` / `DemandNetting`).

## Quota vs. Capacity Distinction

A critical concept for CEs: **Quota != Capacity**.

- **Quota** (`QIR` - Quota Increase Request): The maximum legal ceiling of a cloud resource a project can consume in Cloud Console. Having a quota of 10,000 A100 GPUs does **not** guarantee physically available rack hardware in `us-central1`.
- **Capacity** (`Horizon Demand` / `CCA`): Actual physical compute, memory, disk, and network hardware available at a specific metro/zone during a target time horizon.

When a customer needs routine small quota within existing safety limits, an auto-approved QIR suffices. However, for significant **inorganic growth**, specialized hardware (GPUs/TPUs like A100, H100, v5p, or Hyperdisk), or multi-quarter deals (`T0-T3 months`), CEs must file a formal **Horizon Capacity Demand** (`go/cloud-ca` redirect / `go/horizon`).

## Entity & Concept Migration Table

| Legacy (`go/cloud-ca` / CCA) | Horizon (`go/horizon` DemandManager)                | Description & Action                                                                          |
| :--------------------------- | :-------------------------------------------------- | :-------------------------------------------------------------------------------------------- |
| **CCA Request**              | `CapacityDemand`                                    | Primary composite proto entity tracking the customer's forecast and feasibility.              |
| **QIR Intake / Fit-Check**   | `ResourceDemand` / `PlaceholderDemand`              | Individual resource slice requests tied to a parent capacity demand.                          |
| **Draft CCA**                | `CAPACITY_DEMAND_STATE_DRAFT` (`int: 1`)            | Initial proposal state editable by CEs before formal review submission.                       |
| **CCA Submitted for Review** | `CAPACITY_DEMAND_STATE_UNDER_ASSESSMENT` (`int: 2`) | Capacity Planning / CCNP Ops team (`go/ccnp-ops`) actively evaluating feasibility.            |
| **CCA Approved / Feasible**  | `CAPACITY_DEMAND_STATE_ACKNOWLEDGED` (`int: 3`)     | Feasibility verified and capacity headroom reserved for customer onboarding.                  |
| **CCA Rejected / Stockout**  | `CAPACITY_DEMAND_STATE_REJECTED` (`int: 5`)         | Insufficient inventory or bandwidth enforcer (`BwE`) ceiling violation.                       |
| **Inorganic Justification**  | `justification` / `DemandPreferences`               | Mandatory detailed business context explaining why baseline organic growth is exceeded.       |
| **Shapeless Assessment**     | Shapeless (`planning_sku` + auto RAM)               | Preferred intake mode allowing flexible cluster scheduling without locking exact VM profiles. |

## Horizon Integration Arch & Boq Services

Horizon is built using Google's Boq server framework (`//depot/google3/cloud/capacity/horizon/...`) backed by Spanner (`horizon-db.sdl`), DAL (`demand_dal.proto`), and exported gRPC endpoints:

1.  **DemandManager Service**: `cloud/capacity/horizon/platform/services/demandmanager/`
    - RPC `CreateCapacityDemand`: Creates a `CapacityDemand` in `DRAFT` (state `1`).
    - RPC `UpdateCapacityDemand`: Modifies un-submitted (`DRAFT`) proposals.
    - RPC `SubmitCapacityDemand`: Promotes proposal to assessment queue (`UNDER_ASSESSMENT`).
    - RPC `GetCapacityDemand` / `ListCapacityDemand`: Queries existing request states.
2.  **InorganicSignalManager Service**: Tracks customer signals (`cloud/capacity/horizon/platform/services/inorganicsignalmanager/`).
