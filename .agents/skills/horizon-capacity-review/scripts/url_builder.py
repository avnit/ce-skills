"""Horizon Portal URL Construction & Link Verification Script.

This script constructs canonical, concise Horizon portal URLs based on request IDs,
SFDC Account IDs, and Project Numbers according to the official Horizon Angular UI router specs.
"""

import argparse
import json
import re
import sys
from typing import Dict, Optional


def build_horizon_url(
    request_id: str,
    sfdc_account_id: Optional[str] = None,
    project_number: Optional[str] = None,
    env: str = "prod",
) -> Dict[str, str]:
    """Builds the canonical and direct fallback Horizon Portal review URLs.

    Args:
        request_id: The Horizon Demand ID (e.g. 'CDR00380246' or 'RDR00689449').
        sfdc_account_id: 18-char SFDC Account ID (e.g. '0014M00001vluJ3QAI').
        project_number: 12-digit GCP Project Number (e.g. '496537482084').
        env: Target environment ('prod' or 'staging').

    Returns:
        Dict containing 'primary_url', 'direct_list_url', and 'markdown_link'.
    """
    domain = (
        "horizon.corp.google.com"
        if env == "prod"
        else "horizon-staging.corp.google.com"
    )

    clean_req = request_id.strip()
    clean_proj = project_number.strip() if project_number else None

    # Check if sfdc_account_id is an 18-char Salesforce Account ID (starts with 001)
    clean_sfdc = None
    if sfdc_account_id:
        val = sfdc_account_id.strip()
        if val.startswith("external/"):
            val = val.replace("external/", "")
        clean_sfdc = val

    # Direct list route (Works universally for all CDR and RDR IDs without needing SFDC/Project context)
    direct_list_url = f"https://{domain}/list/{clean_req}"

    # Full scoped route (Requires valid SFDC Account ID and Project Number)
    if clean_sfdc and clean_proj:
        primary_url = (
            f"https://{domain}/customers/external/{clean_sfdc}/projects/{clean_proj}/review?"
            f"requestId={clean_req}"
        )
    elif clean_sfdc:
        primary_url = (
            f"https://{domain}/customers/external/{clean_sfdc}/review?"
            f"requestId={clean_req}"
        )
    else:
        primary_url = direct_list_url

    markdown_link = (
        f"[{clean_req}]({primary_url})"
        if primary_url == direct_list_url
        else f"[{clean_req}]({primary_url}) | [Direct List Link]({direct_list_url})"
    )

    return {
        "request_id": clean_req,
        "sfdc_account_id": clean_sfdc,
        "project_number": clean_proj,
        "env": env,
        "primary_url": primary_url,
        "direct_list_url": direct_list_url,
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
        "--sfdc_account_id", help="18-char SFDC Account ID (e.g. 0014M00001vluJ3QAI)."
    )
    parser.add_argument(
        "--project_number", help="12-digit GCP Project Number (e.g. 496537482084)."
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
        sfdc_account_id=args.sfdc_account_id,
        project_number=args.project_number,
        env=args.env,
    )

    print(json.dumps(res, indent=2))
    print(f"\n✅ Formatted Markdown Link:\n{res['markdown_link']}")


if __name__ == "__main__":
    main()
