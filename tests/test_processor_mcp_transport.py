#!/usr/bin/env python3
"""
Hermetic unit tests for W4-1 processor MCP transport.
Covers:
- Schema vendoring drift test against backend source of truth.
- Payload mapping and schema validation via mcp_publisher.
- Receipt-gated FIXED -> PROCESSED transition.
- Error handling paths (validation, conflict, transport) preserving file status.
"""

import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import sys
REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / ".agents" / "skills" / "closed-loop-learning" / "scripts"
if str(SKILLS_DIR) not in sys.path:
    sys.path.insert(0, str(SKILLS_DIR))

import bug_to_lesson_processor as processor  # noqa: E402
import mcp_publisher  # noqa: E402


class TestProcessorMcpTransport(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.env_patcher = patch.dict(os.environ, {
            "CLOSED_LOOP_ACCOUNT": "test-agent@google.com",
            "CE_MCP_SERVER_URL": "https://mock.mcp.server/mcp",
        })
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_schema_vendoring_drift(self):
        """Verify vendored schema exists, has drift note, and matches backend schema shape."""
        vendored_path = REPO_ROOT / ".agents" / "skills" / "closed-loop-learning" / "contracts" / "lesson_submission.schema.json"
        if not vendored_path.exists():
            vendored_path = REPO_ROOT / "doc" / "contracts" / "lesson_submission.schema.json"
        self.assertTrue(vendored_path.exists(), "lesson_submission.schema.json not found")

        with open(vendored_path, "r", encoding="utf-8") as f:
            vendored = json.load(f)

        backend_path = Path("/usr/local/google/home/shacharb/ce-skills-close-loop-learning/doc/contracts/lesson_submission.schema.json")
        if backend_path.exists():
            with open(backend_path, "r", encoding="utf-8") as f:
                backend = json.load(f)
            vendored_copy = dict(vendored)
            vendored_copy.pop("_drift_note", None)
            self.assertEqual(vendored_copy, backend, "Vendored schema has drifted from backend source of truth")

    def test_payload_mapping_and_validation(self):
        """Test canonical payload mapping and local schema validation."""
        valid_submission = {
            "source_bug_id": "BUG_101",
            "raw_error_context": {
                "failed_command": "gcloud run deploy",
                "stderr_output": "ERROR: permission denied"
            },
            "remediation": "Grant Cloud Run Admin role.",
            "submitted_by": "test-agent@google.com"
        }
        # Should not raise
        mcp_publisher.validate_submission(valid_submission)

        # Missing required field should raise
        invalid_submission = dict(valid_submission)
        del invalid_submission["remediation"]
        with self.assertRaises(ValueError):
            mcp_publisher.validate_submission(invalid_submission)

    @patch("bug_to_lesson_processor.submit_to_mcp")
    def test_mcp_path_and_receipt_gating(self, mock_mcp):
        """When processing bug file, use mcp path and gate PROCESSED on receipt."""
        mock_mcp.return_value = {
            "lesson_id": "bug_mcp_01",
            "status": "pending_review",
            "extraction_mode": "llm",
            "possible_duplicates": []
        }

        bug_file = os.path.join(self.test_dir, "bug_mcp.json")
        with open(bug_file, "w", encoding="utf-8") as f:
            json.dump({
                "bug_id": "bug_mcp_01",
                "status": "FIXED",
                "remediation": "Grant viewer role.",
                "error_logs": {
                    "failed_command": "gcloud projects list",
                    "stderr_output": "403 permission denied",
                    "exit_code": 1
                },
                "lab_name": "lab-1",
                "step_number": 2,
                "workflow": "validate"
            }, f)

        res = processor.process_bug_file(bug_file)
        self.assertTrue(res)
        mock_mcp.assert_called_once()

        # Verify submission payload structure
        sent_payload = mock_mcp.call_args[0][0]
        self.assertEqual(sent_payload["source_bug_id"], "bug_mcp_01")
        self.assertEqual(sent_payload["raw_error_context"]["failed_command"], "gcloud projects list")
        self.assertEqual(sent_payload["raw_error_context"]["stderr_output"], "403 permission denied")
        self.assertEqual(sent_payload["raw_error_context"]["exit_code"], 1)
        self.assertEqual(sent_payload["origin"]["lab_name"], "lab-1")
        self.assertEqual(sent_payload["origin"]["step_number"], 2)
        self.assertEqual(sent_payload["origin"]["workflow"], "validate")

        # Verify disk status transitioned to PROCESSED
        with open(bug_file, "r", encoding="utf-8") as f:
            saved = json.load(f)
        self.assertEqual(saved["status"], "PROCESSED")

    @patch("bug_to_lesson_processor.submit_to_mcp")
    def test_error_paths_preserve_file_status(self, mock_mcp):
        """When MCP submit fails with transport or validation errors, status remains FIXED."""
        for err_type, exc in [
            ("transport", RuntimeError("MCP Server communication error: Connection refused")),
            ("validation", ValueError("Submission payload failed schema validation"))
        ]:
            with self.subTest(err_type=err_type):
                mock_mcp.side_effect = exc
                bug_file = os.path.join(self.test_dir, f"bug_{err_type}.json")
                with open(bug_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "bug_id": f"bug_{err_type}",
                        "status": "FIXED",
                        "remediation": "Some remediation",
                        "error_logs": {"failed_command": "cmd", "stderr_output": "err"}
                    }, f)

                res = processor.process_bug_file(bug_file)
                self.assertFalse(res)

                # Ensure disk file status is still FIXED
                with open(bug_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self.assertEqual(saved["status"], "FIXED")

    @patch("bug_to_lesson_processor.submit_to_mcp")
    def test_conflict_error_transitions_to_processed(self, mock_mcp):
        """When MCP submit fails with terminal conflict error, status transitions to PROCESSED."""
        mock_mcp.side_effect = RuntimeError("MCP tool error: Lesson already exists with status 'approved'")
        bug_file = os.path.join(self.test_dir, "bug_conflict.json")
        with open(bug_file, "w", encoding="utf-8") as f:
            json.dump({
                "bug_id": "bug_conflict",
                "status": "FIXED",
                "remediation": "Some remediation",
                "error_logs": {"failed_command": "cmd", "stderr_output": "err"}
            }, f)

        res = processor.process_bug_file(bug_file)
        self.assertTrue(res)

        with open(bug_file, "r", encoding="utf-8") as f:
            saved = json.load(f)
        self.assertEqual(saved["status"], "PROCESSED")


if __name__ == "__main__":
    unittest.main()
