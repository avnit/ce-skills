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

        res = onboard.install_cluster_tooling()
        self.assertFalse(res)
        out = captured.getvalue()
        self.assertIn("could not install/verify kubectl", out)
        self.assertNotIn("cluster tooling present", out)

    @patch("sys.stdout")
    @patch("subprocess.run")
    @patch("shutil.which")
    def test_tooling_install_verified_success(self, mock_which, mock_run, mock_stdout):
        import io
        captured = io.StringIO()
        mock_stdout.write = captured.write

        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_run.return_value = mock_res
        mock_which.return_value = "/usr/bin/kubectl"

        res = onboard.install_cluster_tooling()
        self.assertTrue(res)
        out = captured.getvalue()
        self.assertIn("cluster tooling present", out)

    @patch("os.path.exists")
    def test_docs_mcp_pruned_when_par_absent(self, mock_exists):
        mock_exists.side_effect = lambda path: False if "docs_mcp_server.par" in path else True

        mcp_servers = {"google-developer-knowledge": {}}
        onboard.configure_docs_mcp(mcp_servers)
        self.assertNotIn("google-developer-knowledge", mcp_servers)

    @patch("os.path.exists")
    def test_docs_mcp_url_header_injected_when_par_absent(self, mock_exists):
        mock_exists.side_effect = lambda path: False if "docs_mcp_server.par" in path else True

        mcp_servers = {
            "google-developer-knowledge": {
                "httpUrl": "http://localhost:8080/mcp"
            }
        }
        onboard.configure_docs_mcp(mcp_servers, knowledge_project="my-custom-proj")
        self.assertIn("google-developer-knowledge", mcp_servers)
        self.assertEqual(
            mcp_servers["google-developer-knowledge"]["headers"]["X-goog-user-project"],
            "my-custom-proj",
        )

    @patch("os.path.exists")
    def test_docs_mcp_env_override(self, mock_exists):
        mock_exists.return_value = True
        mcp_servers = {}
        with patch.dict(os.environ, {"DOCS_MCP_SERVER": "/custom/path/docs_mcp.par"}, clear=False):
            onboard.configure_docs_mcp(mcp_servers)
            self.assertEqual(
                mcp_servers["google-developer-knowledge"]["command"],
                "/custom/path/docs_mcp.par",
            )

        mcp_servers = {}
        with patch.dict(os.environ, {}, clear=True):
            onboard.configure_docs_mcp(mcp_servers)
            self.assertEqual(
                mcp_servers["google-developer-knowledge"]["command"],
                "/google/bin/releases/docs-mcp-local/docs_mcp_server.par",
            )

    @patch("os.path.exists")
    def test_docs_mcp_legacy_key_migrated(self, mock_exists):
        mock_exists.return_value = True
        mcp_servers = {
            "google-developer-documentation-mcp": {
                "command": "/custom/path/docs_mcp.par",
                "headers": {"X-goog-user-project": "old-proj"},
            }
        }
        onboard.configure_docs_mcp(mcp_servers)
        self.assertNotIn("google-developer-documentation-mcp", mcp_servers)
        self.assertIn("google-developer-knowledge", mcp_servers)
        self.assertEqual(
            mcp_servers["google-developer-knowledge"]["command"],
            "/custom/path/docs_mcp.par",
        )
        self.assertEqual(
            mcp_servers["google-developer-knowledge"]["headers"]["X-goog-user-project"],
            "old-proj",
        )

    def test_workspace_mcp_env_override(self):
        mcp_servers = {}
        with patch.dict(os.environ, {"WORKSPACE_MCP_SERVER": "/custom/path/workspace_server.par"}, clear=False):
            onboard.configure_workspace_mcp(mcp_servers)
            self.assertEqual(mcp_servers["workspace"]["command"], "/custom/path/workspace_server.par")

        mcp_servers = {}
        with patch.dict(os.environ, {}, clear=True):
            onboard.configure_workspace_mcp(mcp_servers)
            self.assertEqual(
                mcp_servers["workspace"]["command"],
                "/google/bin/releases/codemind-mcp-servers/workspace_server.par",
            )


if __name__ == "__main__":
    unittest.main()
