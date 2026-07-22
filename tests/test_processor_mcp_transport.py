#!/usr/bin/env python3
"""
Hermetic unit tests for W4-1 processor MCP transport.
Covers:
- Schema vendoring drift test against backend source of truth.
- Transport signature-guard test for streamable_http_client.
- Payload mapping and schema validation.
- Flag selection (default firestore vs mcp).
- Receipt-gated FIXED -> PROCESSED transition.
- Error handling paths (validation, conflict, transport) preserving file status.
"""

import inspect
import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

# Add script lib/scripts to sys.path so we can import bug_to_lesson_processor
import sys
REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / ".agents" / "skills" / "closed-loop-learning" / "scripts"
if str(SKILLS_DIR) not in sys.path:
    sys.path.insert(0, str(SKILLS_DIR))

import bug_to_lesson_processor as processor  # noqa: E402


class TestProcessorMcpTransport(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.env_patcher = patch.dict(os.environ, {
            "CLOSED_LOOP_ACCOUNT": "test-agent@google.com",
            "CE_MCP_SERVER_URL": "https://mock.mcp.server/mcp",
            "CLOSED_LOOP_STORAGE_BACKEND": "local",
        })
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_schema_vendoring_drift(self):
        """Verify vendored schema exists, has drift note, and matches backend schema shape."""
        vendored_path = REPO_ROOT / ".agents" / "skills" / "closed-loop-learning" / "contracts" / "lesson_submission.schema.json"
        self.assertTrue(vendored_path.exists(), "Vendored lesson_submission.schema.json not found")

        with open(vendored_path, "r", encoding="utf-8") as f:
            vendored = json.load(f)

        self.assertIn("_drift_note", vendored)
        self.assertIn("Vendored from", vendored["_drift_note"])

        backend_path = Path("/usr/local/google/home/shacharb/ce-skills-close-loop-learning/doc/contracts/lesson_submission.schema.json")
        if backend_path.exists():
            with open(backend_path, "r", encoding="utf-8") as f:
                backend = json.load(f)
            # Remove drift note for comparison
            vendored_copy = dict(vendored)
            vendored_copy.pop("_drift_note", None)
            self.assertEqual(vendored_copy, backend, "Vendored schema has drifted from backend source of truth")

    def test_transport_signature_guard(self):
        """Ported from backend: streamable_http_client must support auth header/http_client injection."""
        from mcp.client.streamable_http import streamable_http_client
        params = inspect.signature(streamable_http_client).parameters
        self.assertTrue(
            "headers" in params or "http_client" in params,
            "streamable_http_client must support headers or http_client injection"
        )

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
        processor.validate_submission(valid_submission)

        # Missing required field should raise
        invalid_submission = dict(valid_submission)
        del invalid_submission["remediation"]
        with self.assertRaises(ValueError):
            processor.validate_submission(invalid_submission)

    @patch.object(processor, "push_to_firebase")
    @patch.object(processor, "submit_to_mcp")
    def test_flag_selection_default_firestore(self, mock_mcp, mock_firebase):
        """When CLOSED_LOOP_TRANSPORT is unset (default), use firestore path."""
        with patch.dict(os.environ, {"CLOSED_LOOP_STORAGE_BACKEND": "local"}, clear=True):
            os.environ.pop("CLOSED_LOOP_TRANSPORT", None)
            bug_file = os.path.join(self.test_dir, "bug_default.json")
            with open(bug_file, "w", encoding="utf-8") as f:
                json.dump({
                    "bug_id": "bug_def_01",
                    "status": "FIXED",
                    "remediation": "Fix permissions",
                    "error_logs": {"failed_command": "cmd"}
                }, f)

            res = processor.process_bug_file(bug_file)
            self.assertTrue(res)
            mock_firebase.assert_called_once()
            mock_mcp.assert_not_called()

    @patch.object(processor, "push_to_firebase")
    @patch.object(processor, "submit_to_mcp")
    def test_flag_selection_mcp_path_and_receipt_gating(self, mock_mcp, mock_firebase):
        """When CLOSED_LOOP_TRANSPORT=mcp, use mcp path and gate PROCESSED on receipt."""
        with patch.dict(os.environ, {"CLOSED_LOOP_TRANSPORT": "mcp"}):
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
            mock_firebase.assert_not_called()

            # Verify submission payload structure (no generalized_lesson)
            sent_payload = mock_mcp.call_args[0][0]
            self.assertEqual(sent_payload["source_bug_id"], "bug_mcp_01")
            self.assertEqual(sent_payload["raw_error_context"]["failed_command"], "gcloud projects list")
            self.assertEqual(sent_payload["raw_error_context"]["stderr_output"], "403 permission denied")
            self.assertEqual(sent_payload["raw_error_context"]["exit_code"], 1)
            self.assertNotIn("generalized_lesson", sent_payload)
            self.assertEqual(sent_payload["origin"]["lab_name"], "lab-1")
            self.assertEqual(sent_payload["origin"]["step_number"], 2)
            self.assertEqual(sent_payload["origin"]["workflow"], "validate")

            # Verify disk status transitioned to PROCESSED
            with open(bug_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(saved["status"], "PROCESSED")

    @patch.object(processor, "submit_to_mcp")
    def test_error_paths_preserve_file_status(self, mock_mcp):
        """When MCP submit fails with transport or validation errors, status remains FIXED."""
        with patch.dict(os.environ, {"CLOSED_LOOP_TRANSPORT": "mcp"}):
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

    @patch.object(processor, "submit_to_mcp")
    def test_conflict_error_transitions_to_processed(self, mock_mcp):
        """When MCP submit fails with terminal conflict error, status transitions to PROCESSED."""
        with patch.dict(os.environ, {"CLOSED_LOOP_TRANSPORT": "mcp"}):
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

    @patch.object(processor, "submit_to_mcp")
    def test_missing_account_preserves_status(self, mock_mcp):
        """When closed_loop_account is unset and no fallback exists, raise error and preserve FIXED."""
        with patch.dict(os.environ, {"CLOSED_LOOP_TRANSPORT": "mcp"}):
            os.environ.pop("CLOSED_LOOP_ACCOUNT", None)
            os.environ.pop("CE_CLOSED_LOOP_ACCOUNT", None)
            with patch.object(processor.ce_config, "get_secret", return_value=None):
                with patch.dict(processor.STORAGE_CFG, {}, clear=True):
                    bug_file = os.path.join(self.test_dir, "bug_no_account.json")
                    with open(bug_file, "w", encoding="utf-8") as f:
                        json.dump({
                            "bug_id": "bug_no_account",
                            "status": "FIXED",
                            "remediation": "Some remediation",
                            "error_logs": {"failed_command": "cmd", "stderr_output": "err"}
                        }, f)

                    res = processor.process_bug_file(bug_file)
                    self.assertFalse(res)
                    mock_mcp.assert_not_called()

                    with open(bug_file, "r", encoding="utf-8") as f:
                        saved = json.load(f)
                    self.assertEqual(saved["status"], "FIXED")

    @patch.object(processor, "push_to_firebase")
    def test_firestore_path_executes_without_mcp_deps(self, mock_firebase):
        """Verify module imports cleanly and firestore path executes when jsonschema and mcp are absent."""
        with patch.dict(sys.modules, {"jsonschema": None, "mcp": None, "mcp.client": None, "mcp.client.session": None, "mcp.client.streamable_http": None}):
            with patch.dict(os.environ, {"CLOSED_LOOP_STORAGE_BACKEND": "local"}, clear=True):
                os.environ.pop("CLOSED_LOOP_TRANSPORT", None)
                bug_file = os.path.join(self.test_dir, "bug_no_deps.json")
                with open(bug_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "bug_id": "bug_no_deps",
                        "status": "FIXED",
                        "remediation": "Fix permissions",
                        "error_logs": {"failed_command": "cmd"}
                    }, f)

                res = processor.process_bug_file(bug_file)
                self.assertTrue(res)
                mock_firebase.assert_called_once()

    def test_mcp_path_raises_actionable_error_without_deps(self):
        """Verify missing jsonschema or mcp raises actionable RuntimeError with installation instructions."""
        with patch.dict(sys.modules, {"jsonschema": None, "mcp": None}):
            with self.assertRaises(RuntimeError) as cm:
                processor.validate_submission({"source_bug_id": "test"})
            self.assertIn("CLOSED_LOOP_TRANSPORT=mcp requires extra deps", str(cm.exception))
            self.assertIn("requirements.txt", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
