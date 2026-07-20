#!/usr/bin/env python3
"""
Automated Buganizer ticket creation script targeting Component ID 2150801 (ce-skills).
Attempts direct CLI creation via issues-cli and outputs an instant pre-filled web fallback URL.
"""

import argparse
import subprocess
import urllib.parse


def main():
    parser = argparse.ArgumentParser(
        description="Open a Buganizer issue for ce-skills."
    )
    parser.add_argument("--title", required=True, help="Issue title")
    parser.add_argument(
        "--description", required=True, help="Issue detailed description"
    )
    parser.add_argument(
        "--priority",
        default="P2",
        choices=["P0", "P1", "P2", "P3", "P4"],
        help="Issue priority",
    )
    parser.add_argument(
        "--type",
        default="BUG",
        choices=["BUG", "FEATURE_REQUEST", "PROCESS", "CLEANUP"],
        help="Issue type",
    )
    parser.add_argument(
        "--assignee", default="", help="Assignee LDAP (without @google.com)"
    )
    parser.add_argument(
        "--component-id",
        default="2150801",
        help="Buganizer Component ID (defaults to 2150801)",
    )

    args = parser.parse_args()

    # 1. Build URL-encoded query parameters for self-service web UI fallback
    query_params = {
        "component": args.component_id,
        "title": args.title,
        "description": args.description,
        "priority": args.priority,
        "type": args.type,
    }
    if args.assignee:
        query_params["assignee"] = args.assignee

    encoded_params = urllib.parse.urlencode(query_params)
    web_url = f"https://b.corp.google.com/issues/new?{encoded_params}"

    print("==========================================================")
    print("🐞 PREPARING BUGANIZER ISSUE FILING")
    print("==========================================================")
    print(f"📦 Component ID: {args.component_id} (ce-skills)")
    print(f"📌 Title:        {args.title}")
    print(f"🚨 Priority:     {args.priority}")
    print(f"🏷️  Type:         {args.type}")
    if args.assignee:
        print(f"👤 Assignee:     {args.assignee}")
    print(f"📝 Description:\n{args.description}")
    print("----------------------------------------------------------")
    print("🌐 Pre-filled Web UI Filing URL (One-Click):")
    print(f"👉 {web_url}")
    print("==========================================================")

    # 2. Attempt direct CLI creation via internal issues tool
    issues_cli = os.environ.get("ISSUES", "/google/bin/releases/issues-cli/issues")
    cli_cmd = [
        issues_cli,
        "create",
        "--component_id",
        args.component_id,
        "--title",
        args.title,
        "--description",
        args.description,
        "--priority",
        args.priority,
        "--type",
        args.type,
    ]
    if args.assignee:
        cli_cmd.extend(["--assignee", args.assignee])

    print("\nAttempting direct CLI creation via issues-cli...")
    try:
        res = subprocess.run(cli_cmd, capture_output=True, text=True, check=False)
        if res.returncode == 0:
            print("✅ Successfully created Buganizer issue via CLI!")
            print(res.stdout.strip())
        else:
            print(
                f"⚠️ Notice: Direct CLI mutation failed (returncode {res.returncode})."
            )
            if (
                "CredsPermissionException" in res.stderr
                or "Rejected by creds_policy" in res.stderr
                or "auth.creds.useLOAS" in res.stderr
            ):
                print(
                    "   Reason: Your Cloudtop session requires explicit LOAS credentials or network proxy authorization for CLI mutations."
                )
            print(
                "👉 Please click the pre-filled Web UI URL above to submit your bug instantly in your browser!"
            )
    except Exception as e:
        print(f"⚠️ Could not execute issues-cli: {e}")
        print(
            "👉 Please click the pre-filled Web UI URL above to submit your bug instantly in your browser!"
        )


if __name__ == "__main__":
    main()
