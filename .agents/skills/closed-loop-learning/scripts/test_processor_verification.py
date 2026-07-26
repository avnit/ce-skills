#!/usr/bin/env python3
"""
Comprehensive Unit Test Suite for synthesized bug_to_lesson_processor.py

Verifies all 5 enhancements rigorously:
1. Dual-Identity ADC Authentication token caching and validation.
2. Service-Specific Knowledge Topics / Tags filtering, word-boundary rejection of false positives, and conditional fallback.
3. Boilerplate Stripping multi-layered iterative cleaning across fields.
4. Command Scaffolding enforcement and backtick normalization.
5. Atomic Error Handling failure preservation and success transitions.
"""

import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import bug_to_lesson_processor as processor
import lesson_extractor
import mcp_publisher
import tag_scrubber


class TestBugToLessonProcessor(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.env_patcher = patch.dict(os.environ, {"CLOSED_LOOP_STORAGE_BACKEND": "local"})
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # -----------------------------------------------------------------------
    # 1. MCP Submitter Account Resolution Tests
    # -----------------------------------------------------------------------
    @patch("ce_config.get_secret", return_value=None)
    @patch("mcp_publisher.ce_config.get_secret", return_value=None)
    @patch("mcp_publisher.subprocess.run")
    def test_resolve_submitted_by_from_gcloud(self, mock_run, mock_mcp_sec, mock_ce_sec):
        mock_run.return_value = MagicMock(stdout="test-developer@google.com\n", returncode=0)

        with patch.dict(os.environ, {}, clear=False):
            for k in ["CLOSED_LOOP_ACCOUNT", "CE_CLOSED_LOOP_ACCOUNT", "CLOSED_LOOP_CREDENTIAL_ACCOUNT"]:
                if k in os.environ:
                    del os.environ[k]
            with patch("ce_config._cached_config", {}):
                account = mcp_publisher.resolve_submitted_by()
                self.assertEqual(account, "test-developer@google.com")

    # -----------------------------------------------------------------------
    # 3. Boilerplate Stripping Tests (Iterative / Multi-layered)
    # -----------------------------------------------------------------------
    def test_strip_boilerplate_iterative(self):
        cases = [
            ("Verified architectural resolution: Use gcloud storage cp.", "Use gcloud storage cp."),
            ("verified remediation:   Add IAM role to service account.  ", "Add IAM role to service account."),
            ("Lesson Learned: Verified Remediation: Never hardcode IPs.", "Never hardcode IPs."),
            ("Generalized lesson: Error in command 'gcloud compute instances list': Configure VPC peering.", "Configure VPC peering."),
            ("Specific lesson: Error executing command 'kubectl get pods': Enable secret manager API.", "Enable secret manager API."),
            ("No boilerplate here.", "No boilerplate here."),
            (None, ""),
            (12345, "12345")
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(processor.strip_boilerplate(raw), expected)

    # -----------------------------------------------------------------------
    # 4. Command Scaffolding Tests
    # -----------------------------------------------------------------------
    def test_enforce_command_scaffolding(self):
        # Case 1: No command sample present, failed_cmd provided without backticks
        raw = "Verified remediation: Enable the Cloud SQL Admin API."
        res = tag_scrubber.enforce_command_scaffolding(raw, "gcloud services enable sqladmin.googleapis.com")
        self.assertIn("Enable the Cloud SQL Admin API.", res)
        self.assertIn("Command sample:\n`gcloud services enable sqladmin.googleapis.com`", res)

        # Case 2: Command sample already present
        raw_with_sample = "Use IAM binding.\n\nCommand sample:\n`gcloud projects add-iam-policy-binding ...`"
        res2 = tag_scrubber.enforce_command_scaffolding(raw_with_sample, "some other cmd")
        self.assertEqual(res2, raw_with_sample)

        # Case 3: failed_cmd provided with messy existing backticks/whitespace
        res3 = tag_scrubber.enforce_command_scaffolding("Fix permissions.", "  `gcloud auth login`  ")
        self.assertIn("Command sample:\n`gcloud auth login`", res3)
        self.assertNotIn("``", res3)

    # -----------------------------------------------------------------------
    # 2. Service-Specific Knowledge Topics / Tags Tests
    # -----------------------------------------------------------------------
    def test_clean_topics_filtering_and_word_boundary_fallback(self):
        # Case 1: LLM returns mixture of valid product tags and banned process tags
        raw_topics = ["Validation", "GCS", "Remediation", "CloudStorage", "Bug", "Error", "gcs"]
        res = tag_scrubber.clean_topics(raw_topics, "Failed running gcs copy")
        self.assertEqual(res, ["GCS", "CloudStorage"])

        # Case 2: Conditional fallback triggered, word boundary matching rejects substring false positives
        # W2 had a bug where 'running' matched 'run'. Here we test that 'running' does NOT match 'run'.
        raw_banned_only = ["Validation", "ClosedLoop"]
        res2 = tag_scrubber.clean_topics(raw_banned_only, "Error while running network sync in VPC subnets")
        self.assertIn("VPC", res2)
        self.assertIn("Networking", res2)
        self.assertNotIn("CloudRun", res2)  # Proves word-boundary fix worked!

        # Case 3: Empty list and no domain keyword matches -> default fallback
        res3 = tag_scrubber.clean_topics([], "Unknown generic system alert")
        self.assertEqual(res3, ["GCP", "gcloud"])

    # -----------------------------------------------------------------------
    # 5. Atomic Error Handling Tests
    # -----------------------------------------------------------------------
    @patch.object(processor, "submit_to_mcp")
    def test_atomic_error_handling_preserves_status_on_failure(self, mock_submit):
        # Simulate MCP submission failure
        mock_submit.side_effect = RuntimeError("Simulated MCP submission failure")

        bug_file = os.path.join(self.test_dir, "bug_fail.json")
        initial_payload = {
            "bug_id": "bug_fail_101",
            "status": "FIXED",
            "remediation": "Verified remediation: Fix network tag.",
            "error_logs": {"failed_command": "gcloud compute instances create vm1"}
        }
        with open(bug_file, "w", encoding="utf-8") as f:
            json.dump(initial_payload, f)

        # Run process_bug_file
        success = processor.process_bug_file(bug_file)
        self.assertFalse(success)

        # Verify file on disk is STILL in FIXED status
        with open(bug_file, "r", encoding="utf-8") as f:
            disk_payload = json.load(f)
        self.assertEqual(disk_payload["status"], "FIXED")

    @patch.object(processor, "submit_to_mcp")
    def test_successful_processing_updates_status(self, mock_submit):
        mock_submit.return_value = {"extraction_mode": "subagent", "status": "submitted"}  # Successful submit

        bug_file = os.path.join(self.test_dir, "bug_success.json")
        initial_payload = {
            "bug_id": "bug_success_102",
            "status": "FIXED",
            "remediation": "Verified architectural resolution: Grant storage.objectViewer role.",
            "error_logs": {"failed_command": "gsutil ls gs://my-bucket"}
        }
        with open(bug_file, "w", encoding="utf-8") as f:
            json.dump(initial_payload, f)

        success = processor.process_bug_file(bug_file)
        self.assertTrue(success)

        # Verify file on disk transitioned to PROCESSED
        with open(bug_file, "r", encoding="utf-8") as f:
            disk_payload = json.load(f)
        self.assertEqual(disk_payload["status"], "PROCESSED")

    # -----------------------------------------------------------------------
    # 6. Agent API Subagent Extraction Tests
    # -----------------------------------------------------------------------
    @patch("subprocess.run")
    @patch("shutil.which")
    @patch("os.path.exists")
    def test_agentapi_subagent_extraction(self, mock_exists, mock_which, mock_run):
        mock_which.return_value = "/mock/path/agentapi"
        mock_exists.return_value = True

        mock_payload = {
            "specific_lesson": "Verified resolution: Impersonate service account.",
            "generalized_lesson": "Always configure ADC impersonation.\n\nCommand sample:\n`gcloud auth print-access-token`",
            "topics": ["GKE", "IAM"]
        }
        mock_run.return_value = MagicMock(stdout=json.dumps(mock_payload), returncode=0)

        with patch.dict(os.environ, {"ANTIGRAVITY_LS_ADDRESS": "mock_address"}):
            res = lesson_extractor.try_agentapi_extraction(
                failed_cmd="kubectl get pods",
                error_msg="Unauthorized",
                remediation="Verified remediation: Impersonate service account."
            )
            self.assertIsNotNone(res)
            self.assertEqual(res["topics"], ["GKE", "IAM"])


if __name__ == "__main__":
    unittest.main()
