# Horizon API Guide

## Overview

The `DemandManager` Go Boq service (`//depot/google3/cloud/capacity/horizon/platform/services/demandmanager/proto/demandmanager_service.proto`) exposes the primary RPCs for automating and managing Horizon capacity demands (`go/horizon-api-user-guide`).

## Key RPCs & Core Behavior

| RPC Method             | Input Proto                   | Description                                                                                 |
| :--------------------- | :---------------------------- | :------------------------------------------------------------------------------------------ |
| `CreateCapacityDemand` | `CreateCapacityDemandRequest` | Creates a new capacity demand proposal in `CAPACITY_DEMAND_STATE_DRAFT`.                    |
| `UpdateCapacityDemand` | `UpdateCapacityDemandRequest` | Modifies an existing demand proposal that is still un-acknowledged/un-submitted.            |
| `SubmitCapacityDemand` | `SubmitCapacityDemandRequest` | Promotes a draft proposal into the formal evaluation/assessment queue (`UNDER_ASSESSMENT`). |
| `GetCapacityDemand`    | `GetCapacityDemandRequest`    | Fetches current schema, status, assessment notes, and fulfillment details.                  |
| `ListCapacityDemand`   | `ListCapacityDemandRequest`   | Lists historical or active requests matching filter criteria.                               |

## Enum Handling Rules (CRITICAL)

A frequent source of errors when building payloads across Horizon tools:

1.  **Mutating RPCs (`Create` / `Update`)**: Always use **integer** values for enums in the JSON payload body.
    - `"state": 1` (`DRAFT`)
    - `"state": 2` (`UNDER_ASSESSMENT`)
    - `"state": 3` (`ACKNOWLEDGED`)
    - `"state": 4` (`SUBMITTED`)
2.  **Listing Filters (`ListCapacityDemand`)**: Always use **string** names for enum values when querying.
    - `filter: "state=CAPACITY_DEMAND_STATE_ACKNOWLEDGED"`

## Update Restrictions & Safety

- **DRAFT State Only**: You are strictly permitted to invoke `UpdateCapacityDemand` on proposals whose current state is `DRAFT` (`int: 1`).
- **Locked States**: Do **not** attempt to modify demands in `UNDER_ASSESSMENT`, `ACKNOWLEDGED`, or `SUBMITTED` state via `UpdateCapacityDemand`. If an approved or submitted assessment requires changes, advise the CE to cancel/withdraw the request or file an explicit amendment request through `ccnp-ops@`.

## Error Recovery Protocol

When interacting with Horizon Boq endpoints or ADK tools:

```python
# Retry logic pattern for transient gRPC deadline or connection resets
max_retries = 2
for attempt in range(max_retries):
  try:
    response = horizon_client.call_rpc(method, request)
    break
  except gRPCError as e:
    if attempt == max_retries - 1:
      logging.error("Final RPC failure after %d tries: %e", max_retries, e)
      raise
    logging.warning("Transient RPC error, retrying (%d/%d)...", attempt + 1, max_retries)
```

Always verify EUC (End User Credentials) delegation when calling RPCs on behalf of a Customer Engineer.
