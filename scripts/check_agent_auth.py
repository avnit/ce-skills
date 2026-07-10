#!/usr/bin/env python3
"""Hub gate H3: decide whether a comment author may trigger the dev agent.

Called by .github/workflows/dev-agent.yml. Prints "true" or "false" and exits 0;
any unexpected condition (missing/invalid allowlist) prints "false" — the gate
fails closed. Replicated from the backend repo (W4-0); keep in sync.
"""

import json
import sys

ALLOWED_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}


def is_authorized(author: str, association: str, allowlist_path: str) -> bool:
    if not author or not association:
        return False
    try:
        with open(allowlist_path, "r", encoding="utf-8") as f:
            allowed = json.load(f).get("allowed", [])
    except Exception:
        return False
    if not isinstance(allowed, list):
        return False
    return author in allowed and association.upper() in ALLOWED_ASSOCIATIONS


def main() -> None:
    if len(sys.argv) != 4:
        print("false")
        return
    author, association, allowlist_path = sys.argv[1], sys.argv[2], sys.argv[3]
    print("true" if is_authorized(author, association, allowlist_path) else "false")


if __name__ == "__main__":
    main()
