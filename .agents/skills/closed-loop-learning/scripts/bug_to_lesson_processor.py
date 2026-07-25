#!/usr/bin/env python3
"""
Bug to Lesson Processor for Closed-Loop Learning

Modular CLI entry point that scans bug reports, distills lessons via subagent/Agent API,
and publishes structured lessons exclusively to the submit_lesson MCP tool contract.
"""

import argparse
import glob
import json
import logging
import os
import pathlib
import sys
from typing import Dict, Any

def _setup_ce_config():
    current = pathlib.Path(__file__).resolve().parent
    for parent in current.parents:
        if (parent / ".agents").is_dir():
            lib_path = str(parent / ".agents" / "lib")
            if lib_path not in sys.path:
                sys.path.insert(0, lib_path)
            return

_setup_ce_config()

from tag_scrubber import (  # noqa: E402
    strip_boilerplate,
    enforce_command_scaffolding,
    clean_topics,
)
from lesson_extractor import (  # noqa: E402
    try_agentapi_extraction,
    extract_generalized_lesson,
)
from mcp_publisher import (  # noqa: E402
    validate_submission,
    resolve_submitted_by,
    submit_to_mcp,
)


def process_bug_file(filepath: str) -> bool:
    """
    Processes a single bug file into an MCP lesson submission.
    Returns True if successful or cleanly skipped, False on failure.
    Guarantee: local file status never mutates to PROCESSED if submit_to_mcp fails.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            bug_payload = json.load(f)

        if bug_payload.get("status") == "PROCESSED":
            return True

        if bug_payload.get("status") != "FIXED":
            logging.info(f"Skipping {filepath}: status is '{bug_payload.get('status')}' (must be 'FIXED').")
            return True

        logging.info(f"Processing verified FIXED bug file: {filepath}")

        error_logs = bug_payload.get("error_logs", {})
        submitted_by = resolve_submitted_by()
        extracted_info = extract_generalized_lesson(bug_payload)

        lesson_submission = {
            "source_bug_id": bug_payload.get("bug_id") or bug_payload.get("source_bug_id"),
            "raw_error_context": {
                "failed_command": error_logs.get("failed_command", ""),
                "stderr_output": error_logs.get("stderr_output") or error_logs.get("error_message", ""),
            },
            "remediation": strip_boilerplate(bug_payload.get("remediation", "")),
            "submitted_by": submitted_by,
            "topics": extracted_info.get("topics", ["GCP"]),
        }
        if extracted_info.get("specific_lesson"):
            lesson_submission["specific_lesson"] = extracted_info["specific_lesson"]
        if extracted_info.get("generalized_lesson"):
            lesson_submission["generalized_lesson"] = extracted_info["generalized_lesson"]

        if "exit_code" in error_logs and error_logs["exit_code"] is not None:
            lesson_submission["raw_error_context"]["exit_code"] = error_logs["exit_code"]

        origin_dict = {}
        if bug_payload.get("lab_name") is not None:
            origin_dict["lab_name"] = str(bug_payload.get("lab_name"))
        if bug_payload.get("step_number") is not None:
            try:
                origin_dict["step_number"] = int(bug_payload.get("step_number"))
            except (ValueError, TypeError):
                pass
        if bug_payload.get("workflow") is not None:
            origin_dict["workflow"] = str(bug_payload.get("workflow"))
        if origin_dict:
            lesson_submission["origin"] = origin_dict

        validate_submission(lesson_submission)
        try:
            receipt = submit_to_mcp(lesson_submission)
            logging.info(f"MCP submission successful for {lesson_submission['source_bug_id']}. Extraction mode: {receipt.get('extraction_mode', 'subagent')}")
            possible_dups = receipt.get("possible_duplicates", []) if isinstance(receipt, dict) else []
            if possible_dups:
                logging.info(f"Advisory: possible duplicates found: {possible_dups}")
        except Exception as e:
            err_str = str(e)
            if "already exists with status" in err_str or "Conflict" in err_str:
                logging.warning(f"Terminal conflict error for {filepath}: {err_str}. Transitioning status to PROCESSED to stop retry loop.")
            else:
                raise

        # Atomic transition: reached ONLY if submit_to_mcp succeeded without raising
        bug_payload["status"] = "PROCESSED"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(bug_payload, f, indent=2)

        logging.info(f"Successfully processed and updated status for {filepath}")
        return True

    except Exception as e:
        logging.error(f"Processing aborted for {filepath} due to error: {e}. File status preserved.")
        return False


def main():
    parser = argparse.ArgumentParser(description="Process bugs into lessons learned via submit_lesson MCP tool.")
    parser.add_argument("--scan-dir", type=str, required=True, help="Directory to scan for bug JSON files.")
    args = parser.parse_args()

    search_pattern = os.path.join(args.scan_dir, "bug_*.json")
    bug_files = glob.glob(search_pattern)

    if not bug_files:
        logging.info(f"No bug files found in {args.scan_dir}")
        return

    for bug_file in bug_files:
        process_bug_file(bug_file)


if __name__ == "__main__":
    main()
