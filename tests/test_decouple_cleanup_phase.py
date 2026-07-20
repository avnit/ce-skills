import importlib.util
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TESTER_PATH = REPO / ".agents" / "skills" / "codelab-validation" / "scripts" / "tester.py"
VALIDATOR_PATH = REPO / ".agents" / "skills" / "codelab-validation" / "scripts" / "validator.py"


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


tester = _load_module("tester", TESTER_PATH)
validator = _load_module("validator", VALIDATOR_PATH)


class MockSubshellRunner:
    def __init__(self, *args, **kwargs):
        self.executed_commands = []

    def run_command(self, cmd, *args, **kwargs):
        self.executed_commands.append(cmd)
        return 0, "mock output"

    def set_env(self, *args, **kwargs):
        pass

    def close(self):
        pass


class TestDecoupleCleanupPhase(unittest.TestCase):

    def setUp(self):
        self.patcher = patch.object(tester, "get_active_project", return_value="mock-project")
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_marker_based_cleanup_deferred(self):
        md_content = (
            "## Step 1: Deploy Service\n"
            "```bash\n"
            "echo deploy-workload\n"
            "```\n"
            "## Step 2: Teardown Infrastructure <!-- phase: cleanup -->\n"
            "```bash\n"
            "echo destroy-workload\n"
            "```\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir_str:
            tmp_dir = Path(tmp_dir_str)
            md_file = tmp_dir / "lab.md"
            md_file.write_text(md_content, encoding="utf-8")

            mock_runner = MockSubshellRunner()
            with patch.object(tester, "SubshellRunner", return_value=mock_runner):
                t_test = tester.StatefulCodelabTester(str(md_file), phase="test")
                success_test = t_test.run()

                self.assertTrue(success_test)
                self.assertEqual(t_test.steps[0]["status"], "DONE")
                self.assertEqual(t_test.steps[1]["status"], "DEFERRED")
                self.assertIn("echo deploy-workload", mock_runner.executed_commands)
                self.assertNotIn("echo destroy-workload", mock_runner.executed_commands)

                # Now run explicit cleanup phase
                mock_runner_cleanup = MockSubshellRunner()
                with patch.object(tester, "SubshellRunner", return_value=mock_runner_cleanup):
                    t_cleanup = tester.StatefulCodelabTester(str(md_file), phase="cleanup")
                    success_cleanup = t_cleanup.run()

                    self.assertTrue(success_cleanup)
                    self.assertEqual(t_cleanup.steps[1]["status"], "DONE")
                    self.assertIn("echo destroy-workload", mock_runner_cleanup.executed_commands)

    def test_title_regex_heuristic_fallback(self):
        md_content = (
            "## Step 1: Setup Workload\n"
            "```bash\n"
            "echo setup\n"
            "```\n"
            "## Step 2: Clean up your data\n"
            "```bash\n"
            "echo cleanup-cmd\n"
            "```\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir_str:
            tmp_dir = Path(tmp_dir_str)
            md_file = tmp_dir / "lab.md"
            md_file.write_text(md_content, encoding="utf-8")

            mock_runner = MockSubshellRunner()
            with patch.object(tester, "SubshellRunner", return_value=mock_runner):
                t = tester.StatefulCodelabTester(str(md_file), phase="test")
                success = t.run()

                self.assertTrue(success)
                self.assertEqual(t.steps[0]["status"], "DONE")
                # Title regex fallback defers step 2 when no marker is present
                self.assertTrue(t.steps[1]["is_cleanup"])
                self.assertEqual(t.steps[1]["status"], "DEFERRED")
                self.assertNotIn("echo cleanup-cmd", mock_runner.executed_commands)

    def test_tester_cli_skip_cleanup_alias(self):
        md_content = (
            "## Step 1: Run Workload\n"
            "```bash\n"
            "echo workload\n"
            "```\n"
            "## Step 2: Clean up\n"
            "```bash\n"
            "echo cleanup\n"
            "```\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir_str:
            tmp_dir = Path(tmp_dir_str)
            md_file = tmp_dir / "lab.md"
            md_file.write_text(md_content, encoding="utf-8")

            mock_runner = MockSubshellRunner()
            real_init = tester.StatefulCodelabTester.__init__
            created_testers = []

            def spy_init(self, *args, **kwargs):
                real_init(self, *args, **kwargs)
                created_testers.append(self)

            with patch.object(tester, "SubshellRunner", return_value=mock_runner), \
                 patch.object(tester.StatefulCodelabTester, "__init__", spy_init), \
                 patch.object(sys, "argv", ["tester.py", str(md_file), "--skip-cleanup", "--project-id", "test-proj"]), \
                 patch.object(sys, "exit") as mock_exit:
                tester.main()
                mock_exit.assert_called_once_with(0)
                self.assertEqual(len(created_testers), 1)
                self.assertEqual(created_testers[0].steps[1]["status"], "DEFERRED")

    def test_validator_arg_passing(self):
        with patch.object(validator, "run_command") as mock_run_cmd, \
             patch.object(validator, "setup_active_lab"), \
             patch.object(validator, "scan_placeholders", return_value=[]), \
             patch.object(validator, "compile_report"), \
             patch.object(os, "makedirs"), \
             patch("builtins.open", unittest.mock.mock_open()), \
             patch.object(sys, "argv", ["validator.py", "--src", "dummy.lab.md", "--project-id", "test-proj", "--skip-cleanup"]), \
             patch.object(sys, "exit"):
            mock_run_cmd.return_value = (True, "success")
            validator.main()

            # Verify tester.py was invoked with --phase test and --project-id test-proj
            executed_cmds = [call.args[0] for call in mock_run_cmd.call_args_list]
            tester_calls = [cmd for cmd in executed_cmds if "tester.py" in cmd]
            self.assertTrue(len(tester_calls) > 0)
            self.assertIn("--phase test", tester_calls[0])
            self.assertIn("--project-id test-proj", tester_calls[0])

    def test_validator_default_passes_phase_all(self):
        with patch.object(validator, "run_command") as mock_run_cmd, \
             patch.object(validator, "setup_active_lab"), \
             patch.object(validator, "scan_placeholders", return_value=[]), \
             patch.object(validator, "compile_report"), \
             patch.object(os, "makedirs"), \
             patch("builtins.open", unittest.mock.mock_open()), \
             patch.object(sys, "argv", ["validator.py", "--src", "dummy.lab.md", "--project-id", "test-proj"]), \
             patch.object(sys, "exit"):
            mock_run_cmd.return_value = (True, "success")
            validator.main()

            # Verify tester.py was invoked with --phase all when --skip-cleanup is omitted
            executed_cmds = [call.args[0] for call in mock_run_cmd.call_args_list]
            tester_calls = [cmd for cmd in executed_cmds if "tester.py" in cmd]
            self.assertTrue(len(tester_calls) > 0)
            self.assertIn("--phase all", tester_calls[0])
            self.assertIn("--project-id test-proj", tester_calls[0])

    def test_bug_json_keys_and_step_schema_preserved(self):
        md_content = (
            "## Step 1: Failing Step\n"
            "```bash\n"
            "echo fail-cmd\n"
            "```\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir_str:
            tmp_dir = Path(tmp_dir_str)
            md_file = tmp_dir / "lab.md"
            md_file.write_text(md_content, encoding="utf-8")

            t = tester.StatefulCodelabTester(str(md_file))
            t.load_or_initialize_state()

            # Verify step schema keys
            step = t.steps[0]
            for key in ["num", "title", "status", "instructions", "prerequisites", "commands", "output", "error", "has_gui", "is_cleanup"]:
                self.assertIn(key, step)

            # Test bug file generation keys
            with patch.object(tester.subprocess, "Popen"):
                t.file_bug_and_notify_mailbox(failed_step=1, failed_command="echo fail-cmd", error_output="command failed")

            bug_dir = tmp_dir / "bugs"
            bug_files = list(bug_dir.glob("bug_*.json"))
            self.assertEqual(len(bug_files), 1)

            with open(bug_files[0], "r") as bf:
                bug_data = json.load(bf)

            self.assertIn("error_logs", bug_data)
            self.assertIn("failed_command", bug_data["error_logs"])
            self.assertIn("stderr_output", bug_data["error_logs"])
            self.assertEqual(bug_data["error_logs"]["failed_command"], "echo fail-cmd")
            self.assertEqual(bug_data["error_logs"]["stderr_output"], "command failed")


if __name__ == "__main__":
    unittest.main()
