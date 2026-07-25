#!/usr/bin/env python3
"""
MCP Publisher for Closed-Loop Learning

Publishes structured lesson submissions exclusively via the submit_lesson MCP tool.
Validates submission payloads against Contract v1 schema.
"""

import json
import logging
import os
import pathlib
import subprocess
from typing import Dict, Any

import ce_config
import mcp_client
from tag_scrubber import strip_boilerplate


def validate_submission(submission_payload: Dict[str, Any]) -> None:
    """Validates submission payload against Contract v1 schema rules."""
    for field in ["source_bug_id", "raw_error_context", "remediation", "submitted_by"]:
        if field not in submission_payload or submission_payload[field] is None:
            raise ValueError(f"Submission payload missing required field '{field}'")

    raw_ctx = submission_payload.get("raw_error_context", {})
    if not isinstance(raw_ctx, dict):
        raise ValueError("raw_error_context must be a dictionary")

    for field in ["failed_command", "stderr_output"]:
        if field not in raw_ctx:
            raise ValueError(f"raw_error_context missing required field '{field}'")

    schema_path = (
        pathlib.Path(__file__).resolve().parent.parent / "contracts" / "lesson_submission.schema.json"
    )
    if not schema_path.exists():
        for parent in pathlib.Path(__file__).resolve().parents:
            candidate = parent / "doc" / "contracts" / "lesson_submission.schema.json"
            if candidate.is_file():
                schema_path = candidate
                break

    try:
        import jsonschema
        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
            jsonschema.validate(instance=submission_payload, schema=schema)
    except (ImportError, ModuleNotFoundError):
        pass
    except Exception as e:
        if "ValidationError" in type(e).__name__:
            raise ValueError(f"Submission payload failed schema validation: {e}") from e


def resolve_submitted_by() -> str:
    """Resolves active submitter account email."""
    account = (
        ce_config.get_secret("closed_loop_account")
        or os.environ.get("CLOSED_LOOP_ACCOUNT")
        or os.environ.get("CE_CLOSED_LOOP_ACCOUNT")
    )
    if not account:
        try:
            res = subprocess.run(["gcloud", "config", "get-value", "account"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                account = res.stdout.strip()
        except Exception:
            pass
    return account or f"{os.environ.get('USER', 'shacharb')}@google.com"


def submit_to_mcp(submission_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Invokes submit_lesson tool on remote MCP server via mcp_client."""
    validate_submission(submission_payload)
    return mcp_client.call_mcp_tool("submit_lesson", {"submission": submission_payload})
