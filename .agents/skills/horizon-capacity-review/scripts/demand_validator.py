"""Offline deterministic validator for Horizon Capacity Demands prior to HITL confirmation.

This script ensures that any proposed CapacityDemand JSON payload adheres to
Horizon schema guidelines, validates shaped vs. shapeless memory parameters,
verifies enum integer conversions for create/update RPCs, and checks for common
gotchas before the Customer Engineer (CE) confirms submission via ask_question.
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Tuple

# Known enum string vs integer mappings for CapacityDemandState
VALID_STATE_INTEGERS = {1, 2, 3, 4, 5, 6}  # e.g., 1=DRAFT, 2=UNDER_ASSESSMENT
STATE_STRING_NAMES = {
    "CAPACITY_DEMAND_STATE_UNSPECIFIED",
    "CAPACITY_DEMAND_STATE_DRAFT",
    "CAPACITY_DEMAND_STATE_UNDER_ASSESSMENT",
    "CAPACITY_DEMAND_STATE_ACKNOWLEDGED",
    "CAPACITY_DEMAND_STATE_SUBMITTED",
    "CAPACITY_DEMAND_STATE_REJECTED",
}


def validate_demand(
    payload: Dict[str, Any],
) -> Tuple[bool, List[str], List[str]]:
    """Validates the CapacityDemand JSON payload against Horizon best practices.

    Args:
      payload: Dictionary representation of the JSON demand payload.

    Returns:
      A 3-tuple (is_valid, errors, warnings).
    """
    errors = []
    warnings = []

    # 1. State check (must use integer for Create/Update RPC payloads)
    state = payload.get("state")
    if state is not None:
        if isinstance(state, str) and state in STATE_STRING_NAMES:
            errors.append(
                f"Enum Violation: Payload uses string state '{state}'. For Create or"
                " Update RPC calls, state MUST be an integer value (e.g., 1 for"
                " DRAFT). String names are only permitted in list filter parameters."
            )
        elif isinstance(state, int) and state not in VALID_STATE_INTEGERS:
            errors.append(
                f"Enum Violation: Invalid integer state value {state}. Expected"
                f" one of {sorted(VALID_STATE_INTEGERS)}."
            )

    # 2. Required identifier checks
    if not payload.get("customer_id") and not payload.get("project_number"):
        warnings.append(
            "Missing identification: Neither 'customer_id' nor 'project_number' is"
            " populated. Ensure at least one is provided before submission."
        )

    if not payload.get("location"):
        errors.append(
            "Missing mandatory parameter: 'location' (e.g., 'us-central1' or"
            " 'us-east4') is required."
        )

    # 3. Resources validation (shaped vs. shapeless)
    resources = payload.get("resources", [])
    if not isinstance(resources, list) or not resources:
        errors.append(
            "Missing resources: Payload must contain a non-empty 'resources' list."
        )
    else:
        for idx, resource in enumerate(resources):
            if not isinstance(resource, dict):
                errors.append(f"Resource index {idx}: Must be a JSON object.")
                continue

            sku = resource.get("sku") or resource.get("planning_sku")
            shape = resource.get("machine_shape")
            cpu_cores = resource.get("cpu_cores")
            ram_gb = resource.get("ram_gb")

            # Check shaped vs shapeless logic
            if shape:
                if not sku:
                    warnings.append(
                        f"Resource index {idx}: Machine shape '{shape}' provided cleanly"
                        " without an explicit 'planning_sku'. Ensure SKU matches the"
                        " compute template."
                    )
            else:
                # Shapeless check
                if cpu_cores and not ram_gb:
                    warnings.append(
                        f"Resource index {idx}: Shapeless CPU cores ({cpu_cores})"
                        " specified without explicit 'ram_gb'. Total RAM will be"
                        " auto-calculated using resource_metadata.textproto ratio during"
                        " intake."
                    )

            # Check ramp timeline
            ramp_schedule = resource.get("ramp_schedule", [])
            if not ramp_schedule:
                warnings.append(
                    f"Resource index {idx}: No 'ramp_schedule' provided. Ensure demand"
                    " specifies delivery date/quarter expectations."
                )

    # 4. Justifications check
    justification = payload.get("justification") or payload.get(
        "demand_preferences", {}
    ).get("justification")
    if not justification:
        warnings.append(
            "Missing justification: No organic/inorganic growth notes or business"
            " justification attached. CEs should verify why incremental capacity is"
            " requested (e.g., new customer workload, QIR safeguard) before"
            " approval."
        )

    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Offline deterministic validator for Horizon Capacity Demands."
    )
    parser.add_argument(
        "--demand_json_path",
        help="Path to the JSON file containing the proposed CapacityDemand payload.",
    )
    parser.add_argument(
        "--payload_json",
        help="Raw JSON string containing the proposed CapacityDemand payload.",
    )

    args = parser.parse_args()

    if args.payload_json:
        try:
            payload = json.loads(args.payload_json)
            source_name = "inline --payload_json string"
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in --payload_json: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.demand_json_path:
        filepath = args.demand_json_path
        if not os.path.exists(filepath):
            print(f"ERROR: File not found: {filepath}", file=sys.stderr)
            sys.exit(1)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
            source_name = filepath
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON file '{filepath}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.error(
            "You must provide either --payload_json or --demand_json_path."
        )

    print(f"=== Running Horizon Demand Validation on: {source_name} ===")
    _, errors, warnings = validate_demand(payload)

    if warnings:
        print("\n[WARNINGS - Review with CE]:")
        for w in warnings:
            print(f"  * {w}")

    if errors:
        print("\n[ERRORS - Must be resolved prior to submission]:")
        for err in errors:
            print(f"  * {err}")
        print("\nValidation FAILED.")
        sys.exit(1)

    print(
        "\n✅ Verification PASSED: Payload passes all structure and enum rules."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
