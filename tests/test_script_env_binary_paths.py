import os
import sys
import unittest
from unittest.mock import MagicMock, patch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OPEN_BUG_DIR = os.path.join(REPO_ROOT, ".agents", "skills", "open-bug", "scripts")
SEND_EMAIL_DIR = os.path.join(REPO_ROOT, ".agents", "skills", "send-email", "scripts")
CSA_DIR = os.path.join(REPO_ROOT, ".agents", "skills", "workspace-agency-csa", "references")

for d in (OPEN_BUG_DIR, SEND_EMAIL_DIR, CSA_DIR):
    if d not in sys.path:
        sys.path.insert(0, d)

import open_bug  # noqa: E402
import send_email  # noqa: E402
import subprocess_execution  # noqa: E402


class TestScriptEnvBinaryPaths(unittest.TestCase):
    def test_open_bug_imports_cleanly(self):
        """Assert open_bug module imports cleanly without NameError or missing dependencies."""
        self.assertTrue(hasattr(open_bug, "main"))

    @patch("subprocess.run")
    def test_open_bug_issues_cli_env_override(self, mock_run):
        """Assert open_bug.main() uses ISSUES env var override or defaults to /google/bin/releases/issues-cli/issues."""
        mock_run.return_value = MagicMock(returncode=0, stdout="Bug 123 created", stderr="")
        test_args = ["open_bug.py", "--title", "Test Bug", "--description", "Test details"]

        with patch.object(sys, "argv", test_args):
            with patch.dict(os.environ, {"ISSUES": "/custom/path/issues"}, clear=False):
                open_bug.main()
                mock_run.assert_called_once()
                cmd = mock_run.call_args[0][0]
                self.assertEqual(cmd[0], "/custom/path/issues")

        mock_run.reset_mock()
        with patch.object(sys, "argv", test_args):
            with patch.dict(os.environ, {}, clear=True):
                open_bug.main()
                mock_run.assert_called_once()
                cmd = mock_run.call_args[0][0]
                self.assertEqual(cmd[0], "/google/bin/releases/issues-cli/issues")

    def test_send_email_imports_cleanly(self):
        """Assert send_email module imports cleanly without NameError."""
        self.assertTrue(hasattr(send_email, "send_email_api"))

    @patch("send_email.run_command")
    @patch("os.path.exists")
    def test_send_email_sendgmr_env_override(self, mock_exists, mock_run_cmd):
        """Assert send_email_api() uses SENDGMR env var override or defaults to /google/bin/releases/gws-sre/files/sendgmr/sendgmr."""
        mock_exists.return_value = True
        mock_run_cmd.return_value = (True, "OK", "")

        with patch.dict(os.environ, {"SENDGMR": "/custom/path/sendgmr"}, clear=False):
            res = send_email.send_email_api("user@google.com", "Test Subject", "Test Body")
            self.assertTrue(res)
            mock_run_cmd.assert_called_once()
            cmd = mock_run_cmd.call_args[0][0]
            self.assertEqual(cmd[0], "/custom/path/sendgmr")

        mock_run_cmd.reset_mock()
        with patch.dict(os.environ, {}, clear=True):
            res = send_email.send_email_api("user@google.com", "Test Subject", "Test Body")
            self.assertTrue(res)
            mock_run_cmd.assert_called_once()
            cmd = mock_run_cmd.call_args[0][0]
            self.assertEqual(cmd[0], "/google/bin/releases/gws-sre/files/sendgmr/sendgmr")

    def test_csa_cli_imports_cleanly(self):
        """Assert subprocess_execution module imports cleanly and exposes query_workspace_context."""
        self.assertTrue(hasattr(subprocess_execution, "query_workspace_context"))


if __name__ == "__main__":
    unittest.main()
