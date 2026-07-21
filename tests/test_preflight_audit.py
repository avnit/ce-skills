import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPT_DIR = os.path.join(
    REPO_ROOT, ".agents", "skills", "codelab-validation", "scripts"
)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from preflight_audit import (  # noqa: E402
    audit_codelab,
    generate_report_markdown,
)


class TestPreflightAudit(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_temp_lab(self, content: str) -> str:
        lab_path = os.path.join(self.temp_dir.name, "test_lab.lab.md")
        with open(lab_path, "w", encoding="utf-8") as f:
            f.write(content)
        return lab_path

    def test_syntax_error_fails(self):
        """Syntax-error execution unit fails and names syntax error."""
        content = """# Test Lab
```bash
if true; then
  echo "missing fi"
```
"""
        lab_path = self._create_temp_lab(content)
        summary, reports = audit_codelab(lab_path)

        self.assertEqual(summary["verdict"], "FAIL")
        self.assertGreater(summary["fail_count"], 0)
        self.assertTrue(any("Syntax Error" in str(r["details"]) for r in reports))

    def test_clean_lab_passes(self):
        """Clean markdown execution units pass pre-flight audit."""
        content = """# Test Lab
```bash
echo "hello world"
export MY_VAR="value"
```
"""
        lab_path = self._create_temp_lab(content)
        summary, reports = audit_codelab(lab_path)

        self.assertEqual(summary["verdict"], "PASS")
        self.assertEqual(summary["fail_count"], 0)
        self.assertEqual(reports[0]["status"], "PASS")

    def test_unresolved_placeholder_fails_and_variables_resolves(self):
        """Unresolved <placeholder> fails; resolved via variables.json passes."""
        content = """# Test Lab
```bash
gcloud config set project <my-project-id>
```
"""
        lab_path = self._create_temp_lab(content)

        # 1. Audit without variables => FAIL
        summary_no_vars, reports_no_vars = audit_codelab(lab_path)
        self.assertEqual(summary_no_vars["verdict"], "FAIL")
        self.assertTrue(
            any("<my-project-id>" in str(r["details"]) for r in reports_no_vars)
        )

        # 2. Audit with variables.json resolving <my-project-id> => PASS
        vars_path = os.path.join(self.temp_dir.name, "variables.json")
        with open(vars_path, "w", encoding="utf-8") as f:
            json.dump({"my-project-id": "my-test-proj-123"}, f)

        summary_with_vars, _ = audit_codelab(lab_path, variables_path=vars_path)
        self.assertEqual(summary_with_vars["verdict"], "PASS")

    def test_interactive_traps_warn_not_fail(self):
        """Interactive traps (ssh without --command, missing image flags) WARN not FAIL."""
        content = """# Test Lab
```bash
gcloud compute ssh my-instance
gcloud compute instances create my-vm --zone=us-central1-a
sudo apt-get update
gcloud auth login
```
"""
        lab_path = self._create_temp_lab(content)
        summary, reports = audit_codelab(lab_path)

        self.assertEqual(summary["verdict"], "PASS")
        self.assertEqual(summary["fail_count"], 0)
        self.assertGreater(summary["warn_count"], 0)
        details_text = " ".join([str(r["details"]) for r in reports])
        self.assertIn("Interactive SSH session", details_text)
        self.assertIn("missing explicit `--image-family`", details_text)
        self.assertIn("sudo", details_text)

    @patch("subprocess.run")
    def test_check_gcloud_surface_invokes_mocked_gcloud_and_fails(self, mock_run):
        """--check-gcloud-surface invokes mocked gcloud with group path and fails on nonzero mock."""
        content = """# Test Lab
```bash
gcloud compute badgroup create my-res
```
"""
        lab_path = self._create_temp_lab(content)

        def side_effect(cmd, **kwargs):
            # If bash -n syntax check
            if cmd == ["bash", "-n"]:
                res = MagicMock()
                res.returncode = 0
                res.stderr = ""
                return res
            # If gcloud surface check
            if cmd[0] == "gcloud" and "badgroup" in cmd:
                res = MagicMock()
                res.returncode = 1
                res.stderr = "ERROR: (gcloud.compute) Invalid choice: 'badgroup'."
                return res
            res = MagicMock()
            res.returncode = 0
            res.stderr = ""
            return res

        mock_run.side_effect = side_effect

        summary, reports = audit_codelab(lab_path, check_gcloud=True)

        self.assertEqual(summary["verdict"], "FAIL")
        self.assertTrue(
            any("Gcloud Surface Error" in str(r["details"]) for r in reports)
        )

    def test_report_file_written_with_verdict(self):
        """Markdown report file is written with proper headings and verdict."""
        content = """# Test Lab
```bash
echo "testing report generation"
```
"""
        lab_path = self._create_temp_lab(content)
        report_path = os.path.join(self.temp_dir.name, "report.md")

        summary, reports = audit_codelab(lab_path)
        report_md = generate_report_markdown(summary, reports)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_md)

        self.assertTrue(os.path.exists(report_path))
        with open(report_path, "r", encoding="utf-8") as f:
            saved_content = f.read()

        self.assertIn("# Phase 3.5 Pre-Flight Code Audit Report", saved_content)
        self.assertIn("**`PASS`**", saved_content)


if __name__ == "__main__":
    unittest.main()
