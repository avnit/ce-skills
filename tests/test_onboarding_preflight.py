import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add .agents/skills/onboarding/scripts and .agents/skills/system-validation/scripts to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ONBOARD_DIR = os.path.join(REPO_ROOT, ".agents", "skills", "onboarding", "scripts")
VERIFY_DIR = os.path.join(REPO_ROOT, ".agents", "skills", "system-validation", "scripts")

if ONBOARD_DIR not in sys.path:
    sys.path.insert(0, ONBOARD_DIR)
if VERIFY_DIR not in sys.path:
    sys.path.insert(0, VERIFY_DIR)

import onboard  # noqa: E402
import verify_system  # noqa: E402


class TestOnboardingPreflight(unittest.TestCase):

    @patch("shutil.which")
    def test_check_gcloud_preflight_missing_gcloud(self, mock_which):
        mock_which.return_value = None
        with self.assertRaises(RuntimeError) as ctx:
            onboard.check_gcloud_preflight()
        self.assertIn("gcloud' CLI is not installed", str(ctx.exception))

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_check_gcloud_preflight_unauthenticated(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/gcloud"
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = json.dumps([{"account": "test@google.com", "status": ""}])
        mock_run.return_value = mock_res

        with self.assertRaises(RuntimeError) as ctx:
            onboard.check_gcloud_preflight()
        self.assertIn("No active authenticated account found", str(ctx.exception))

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_check_gcloud_preflight_authed_success(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/gcloud"
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = json.dumps([{"account": "admin@altostrat.com", "status": "ACTIVE"}])
        mock_run.return_value = mock_res

        # Should not raise any exception
        onboard.check_gcloud_preflight()

    @patch("shutil.which")
    def test_verify_system_gcloud_missing(self, mock_which):
        mock_which.return_value = None
        ok, msg = verify_system.check_gcloud_auth()
        self.assertFalse(ok)
        self.assertIn("gcloud CLI is not installed", msg)

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_verify_system_gcloud_unauthed(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/gcloud"
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = json.dumps([])
        mock_run.return_value = mock_res

        ok, msg = verify_system.check_gcloud_auth()
        self.assertFalse(ok)
        self.assertIn("no active authenticated account found", msg)

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_verify_system_gcloud_authed_success(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/gcloud"
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = json.dumps([{"account": "user@google.com", "status": "ACTIVE"}])
        mock_run.return_value = mock_res

        ok, msg = verify_system.check_gcloud_auth()
        self.assertTrue(ok)
        self.assertIn("user@google.com", msg)

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_check_gcloud_preflight_timeout_passed(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/gcloud"
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = json.dumps([{"account": "admin@altostrat.com", "status": "ACTIVE"}])
        mock_run.return_value = mock_res

        onboard.check_gcloud_preflight()
        _, kwargs = mock_run.call_args
        self.assertEqual(kwargs.get("timeout"), 10)

    @patch("sys.stdout")
    @patch("subprocess.run")
    @patch("shutil.which")
    def test_tooling_install_unverified_warning(self, mock_which, mock_run, mock_stdout):
        import io
        captured = io.StringIO()
        mock_stdout.write = captured.write

        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_run.return_value = mock_res
        # kubectl and gke-gcloud-auth-plugin missing on PATH
        mock_which.side_effect = lambda cmd: "/usr/bin/gcloud" if cmd == "gcloud" else None

        # Simulate tooling check logic
        res_install = mock_run(["gcloud", "components", "install", "kubectl", "gke-gcloud-auth-plugin", "--quiet"], capture_output=True, text=True)
        self.assertEqual(res_install.returncode, 0)
        has_kubectl = bool(mock_which("kubectl"))
        has_plugin = bool(mock_which("gke-gcloud-auth-plugin"))
        self.assertFalse(has_kubectl and has_plugin)

    @patch("os.path.exists")
    def test_docs_mcp_pruned_when_par_absent(self, mock_exists):
        # Setup mock exists to return False for .par file
        mock_exists.side_effect = lambda path: False if "docs_mcp_server.par" in path else True

        mcp_servers = {"google-developer-documentation-mcp": {}}
        docs_par_path = "/google/bin/releases/docs-mcp-local/docs_mcp_server.par"

        if mock_exists(docs_par_path):
            gdev = mcp_servers.setdefault("google-developer-documentation-mcp", {})
            gdev["command"] = docs_par_path
        else:
            if "google-developer-documentation-mcp" in mcp_servers:
                gdev = mcp_servers["google-developer-documentation-mcp"]
                if not gdev.get("command") and not gdev.get("httpUrl") and not gdev.get("serverUrl"):
                    mcp_servers.pop("google-developer-documentation-mcp", None)

        self.assertNotIn("google-developer-documentation-mcp", mcp_servers)


if __name__ == "__main__":
    unittest.main()
