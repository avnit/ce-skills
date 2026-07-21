"""Horizon Portal URL Construction & Link Verification Script.

This script constructs canonical, concise Horizon portal URLs based on request IDs,
customer IDs, and project numbers according to the official Horizon route hierarchy.
"""

import argparse
import json
import re
import sys
from typing import Dict, Optional


def build_horizon_url(
    request_id: str,
    customer_id: Optional[str] = None,
    project_number: Optional[str] = None,
    env: str = "prod",
) -> Dict[str, str]:
    """Builds the canonical and direct fallback Horizon Portal review URLs.

    Args:
        request_id: The Horizon Capacity Demand ID (e.g. 'CDR00380246').
        customer_id: Optional customer ID string (e.g. 'external/0014M00001vluJ3QAI' or '0014M00001vluJ3QAI').
        project_number: Optional GCP project number string (e.g. '496537482084').
        env: Target environment ('prod' or 'staging').

    Returns:
        Dict containing 'primary_url', 'direct_url', and 'markdown_link'.
    """
    domain = (
        "horizon.corp.google.com"
        if env == "prod"
        else "horizon-staging.corp.google.com"
    )

    clean_req = request_id.strip()

    # Normalize customer ID prefix
    clean_cust = None
    if customer_id:
        c = customer_id.strip()
        clean_cust = c if c.startswith("external/") else f"external/{c}"

    clean_proj = project_number.strip() if project_number else None

    # Construct URLs based on parameter availability
    if clean_cust and clean_proj:
        primary_url = (
            f"https://{domain}/customers/{clean_cust}/projects/{clean_proj}/review?"
            f"requestId={clean_req}"
        )
    elif clean_cust:
        primary_url = (
            f"https://{domain}/customers/{clean_cust}/review?"
            f"requestId={clean_req}"
        )
    else:
        primary_url = f"https://{domain}/demands/{clean_req}"

    direct_url = f"https://{domain}/demands/{clean_req}"

    markdown_link = (
        f"[{clean_req}]({primary_url})"
        if primary_url == direct_url
        else f"[{clean_req}]({primary_url}) | [Direct Link]({direct_url})"
    )

    return {
        "request_id": clean_req,
        "customer_id": clean_cust,
        "project_number": clean_proj,
        "env": env,
        "primary_url": primary_url,
        "direct_url": direct_url,
        "markdown_link": markdown_link,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Construct and verify concise Horizon Portal links."
    )
    parser.add_argument(
        "--request_id", required=True, help="Horizon Demand ID (e.g. CDR00380246)."
    )
    parser.add_argument(
        "--customer_id", help="Customer ID (e.g. external/0014M00001vluJ3QAI)."
    )
    parser.add_argument(
        "--project_number", help="GCP Project Number (e.g. 496537482084)."
    )
    parser.add_argument(
        "--env",
        choices=["prod", "staging"],
        default="prod",
        help="Target environment (default: prod).",
    )

    args = parser.parse_args()

    res = build_horizon_url(
        request_id=args.request_id,
        customer_id=args.customer_id,
        project_number=args.project_number,
        env=args.env,
    )

    print(json.dumps(res, indent=2))
    print(f"\n✅ Formatted Markdown Link:\n{res['markdown_link']}")


if __name__ == "__main__":
    main()
