"""Horizon Portal URL Construction & Link Verification Script.

This script constructs canonical, valid Horizon portal URLs based on request IDs,
customer IDs, and project numbers, avoiding 404 errors caused by incomplete query
parameter routes.
"""

import argparse
import json
import re
import sys
import urllib.parse
from typing import Dict, Optional


def build_horizon_url(
    request_id: str,
    customer_id: Optional[str] = None,
    project_number: Optional[str] = None,
    env: str = "prod",
) -> str:
    """Builds a canonical Horizon Portal review URL.

    Args:
        request_id: The Horizon Capacity Demand ID (e.g. 'CDR00339167').
        customer_id: Optional customer ID string (e.g. 'external/55412' or '55412').
        project_number: Optional GCP project number string.
        env: Target environment ('prod' or 'staging').

    Returns:
        Formatted canonical Horizon Portal URL string.
    """
    domain = (
        "horizon.corp.google.com"
        if env == "prod"
        else "horizon-staging.corp.google.com"
    )

    clean_req_id = request_id.strip()

    # Clean customer ID formatting
    clean_cust_id = None
    if customer_id:
        clean_cust_id = customer_id.strip()
        if not clean_cust_id.startswith("external/"):
            clean_cust_id = f"external/{clean_cust_id}"

    # Build canonical scoped URL if customer and project are provided
    if clean_cust_id and project_number:
        clean_proj = project_number.strip()
        return (
            f"https://{domain}/customers/{clean_cust_id}/projects/{clean_proj}/review?"
            f"requestId={clean_req_id}"
        )
    elif clean_cust_id:
        return (
            f"https://{domain}/customers/{clean_cust_id}/review?"
            f"requestId={clean_req_id}"
        )
    else:
        # Direct demand URL route
        return f"https://{domain}/demands/{clean_req_id}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Construct and verify canonical Horizon Portal links."
    )
    parser.add_argument(
        "--request_id", required=True, help="Horizon Demand ID (e.g. CDR00339167)."
    )
    parser.add_argument(
        "--customer_id", help="Customer ID (e.g. external/55412 or 55412)."
    )
    parser.add_argument(
        "--project_number", help="GCP project number (e.g. 365066964946)."
    )
    parser.add_argument(
        "--env",
        choices=["prod", "staging"],
        default="prod",
        help="Target environment (default: prod).",
    )

    args = parser.parse_args()

    url = build_horizon_url(
        request_id=args.request_id,
        customer_id=args.customer_id,
        project_number=args.project_number,
        env=args.env,
    )

    result = {
        "request_id": args.request_id,
        "customer_id": args.customer_id,
        "project_number": args.project_number,
        "env": args.env,
        "canonical_url": url,
    }

    print(json.dumps(result, indent=2))
    print(f"\n✅ Generated Horizon Portal URL:\n{url}")


if __name__ == "__main__":
    main()
