#!/usr/bin/env python3
"""
Hermetic unit tests for account identity resolution and text redactions.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = REPO_ROOT / ".agents" / "lib"
SKILLS_DIR = REPO_ROOT / ".agents" / "skills" / "closed-loop-learning" / "scripts"

if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(SKILLS_DIR) not in sys.path:
    sys.path.insert(0, str(SKILLS_DIR))

from tag_scrubber import strip_boilerplate  # noqa: E402
from mcp_publisher import resolve_submitted_by  # noqa: E402


def test_strip_boilerplate_clean_prefixes():
    """Verify strip_boilerplate removes common boilerplate prefixes."""
    assert strip_boilerplate("Verified remediation: Grant Cloud Run Admin role.") == "Grant Cloud Run Admin role."
    assert strip_boilerplate("Lesson learned: Always set --zone flag.") == "Always set --zone flag."
    assert strip_boilerplate("Specific lesson: Command failed due to 403.") == "Command failed due to 403."
    assert strip_boilerplate("") == ""
    assert strip_boilerplate(None) == ""


def test_resolve_submitted_by_fallback():
    """Verify resolve_submitted_by returns active account email."""
    account = resolve_submitted_by()
    assert "@" in account
