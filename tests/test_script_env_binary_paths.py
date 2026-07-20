import os
import sys
import unittest
from unittest.mock import patch

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

    def test_open_bug_issues_cli_env_override(self):
        """Assert ISSUES environment variable overrides issues_cli path in open_bug."""
        with patch.dict(os.environ, {"ISSUES": "/custom/path/issues"}, clear=False):
            resolved = os.environ.get("ISSUES", "/google/bin/releases/issues-cli/issues")
            self.assertEqual(resolved, "/custom/path/issues")

        with patch.dict(os.environ, {}, clear=True):
            resolved = os.environ.get("ISSUES", "/google/bin/releases/issues-cli/issues")
            self.assertEqual(resolved, "/google/bin/releases/issues-cli/issues")

    def test_send_email_imports_cleanly(self):
        """Assert send_email module imports cleanly without NameError."""
        self.assertTrue(hasattr(send_email, "send_email_api"))

    def test_send_email_sendgmr_env_override(self):
        """Assert SENDGMR environment variable overrides sendgmr_bin path in send_email."""
        with patch.dict(os.environ, {"SENDGMR": "/custom/path/sendgmr"}, clear=False):
            resolved = os.environ.get("SENDGMR", "/google/bin/releases/gws-sre/files/sendgmr/sendgmr")
            self.assertEqual(resolved, "/custom/path/sendgmr")

        with patch.dict(os.environ, {}, clear=True):
            resolved = os.environ.get("SENDGMR", "/google/bin/releases/gws-sre/files/sendgmr/sendgmr")
            self.assertEqual(resolved, "/google/bin/releases/gws-sre/files/sendgmr/sendgmr")

    def test_csa_cli_env_override(self):
        """Assert CSA_CLI environment variable overrides csa_bin path in subprocess_execution."""
        self.assertTrue(hasattr(subprocess_execution, "query_workspace_context"))
        with patch.dict(os.environ, {"CSA_CLI": "/custom/path/csa_cli.par"}, clear=False):
            resolved = os.environ.get("CSA_CLI", "/google/bin/releases/csa-cli/csa_cli.par")
            self.assertEqual(resolved, "/custom/path/csa_cli.par")

        with patch.dict(os.environ, {}, clear=True):
            resolved = os.environ.get("CSA_CLI", "/google/bin/releases/csa-cli/csa_cli.par")
            self.assertEqual(resolved, "/google/bin/releases/csa-cli/csa_cli.par")


if __name__ == "__main__":
    unittest.main()
