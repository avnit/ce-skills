import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO = Path(__file__).resolve().parents[1]
TESTER_PATH = REPO / ".agents" / "skills" / "codelab-validation" / "scripts" / "tester.py"


def _load_tester():
    spec = importlib.util.spec_from_file_location("tester", TESTER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["tester"] = module
    spec.loader.exec_module(module)
    return module


tester = _load_tester()


class TestTesterContracts(unittest.TestCase):

    def setUp(self):
        self.tmp_dir_obj = tempfile.TemporaryDirectory()
        self.tmp_dir = Path(self.tmp_dir_obj.name)
        self.fake_home = self.tmp_dir / "fake_home"
        self.fake_home.mkdir(parents=True, exist_ok=True)

        self.proj_patcher = patch.object(tester, "get_active_project", return_value="mock-project")
        self.mock_get_active_project = self.proj_patcher.start()

        def mock_expanduser(path):
            if path.startswith("~"):
                return str(self.fake_home / path[2:])
            return path

        self.expanduser_patcher = patch("os.path.expanduser", side_effect=mock_expanduser)
        self.mock_expanduser = self.expanduser_patcher.start()

        real_popen = subprocess.Popen
        self.processor_popen_calls = []

        def mock_popen(*args, **kwargs):
            cmd_args = args[0] if args else kwargs.get("args", [])
            if any("bug_to_lesson_processor.py" in str(a) for a in cmd_args):
                self.processor_popen_calls.append(cmd_args)
                return MagicMock()
            return real_popen(*args, **kwargs)

        self.popen_patcher = patch.object(tester.subprocess, "Popen", side_effect=mock_popen)
        self.popen_patcher.start()

    def tearDown(self):
        self.popen_patcher.stop()
        self.expanduser_patcher.stop()
        self.proj_patcher.stop()
        self.tmp_dir_obj.cleanup()

    def test_exit_semantics_passing_and_failing(self):
        """1. Exit semantics: failing command => FAILED status & error; passing lab => COMPLETED."""
        md_content_fail = (
            "## Step 1: Failing Step\n"
            "```bash\n"
            "(exit 7)\n"
            "```\n"
        )
        md_file_fail = self.tmp_dir / "lab_fail.md"
        md_file_fail.write_text(md_content_fail, encoding="utf-8")

        t_fail = tester.StatefulCodelabTester(str(md_file_fail))
        success = t_fail.run()

        self.assertFalse(success)
        self.assertEqual(t_fail.steps[0]["status"], "FAILED")
        self.assertIn("Command failed with status 7", t_fail.steps[0]["error"])

        progress_file = self.tmp_dir / ".tester_state" / "progress.json"
        self.assertTrue(progress_file.exists())
        with open(progress_file, "r") as f:
            progress = json.load(f)
        self.assertEqual(progress["status"], "FAILED")

        # Verify bug JSON was written into hermetic fake_home directory
        central_bugs_dir = self.fake_home / ".gemini" / "jetski" / "bugs"
        self.assertTrue(central_bugs_dir.exists())
        central_bug_files = list(central_bugs_dir.glob("bug_*.json"))
        self.assertEqual(len(central_bug_files), 1)

        # Verify processor popen call was intercepted and recorded
        self.assertTrue(any("bug_to_lesson_processor.py" in str(c) for c in self.processor_popen_calls))

        md_content_pass = (
            "## Step 1: Passing Step\n"
            "```bash\n"
            "echo hello\n"
            "```\n"
        )
        pass_dir = self.tmp_dir / "pass_lab"
        pass_dir.mkdir()
        md_file_pass = pass_dir / "lab_pass.md"
        md_file_pass.write_text(md_content_pass, encoding="utf-8")

        t_pass = tester.StatefulCodelabTester(str(md_file_pass))
        success = t_pass.run()

        self.assertTrue(success)
        self.assertEqual(t_pass.steps[0]["status"], "DONE")

        progress_file_pass = pass_dir / ".tester_state" / "progress.json"
        with open(progress_file_pass, "r") as f:
            progress_pass = json.load(f)
        self.assertEqual(progress_pass["status"], "COMPLETED")

    def test_subshell_runner_exit_code_protocol(self):
        """1b. SubshellRunner protocol: exiting status 7 reports status 7."""
        runner = tester.SubshellRunner(cwd=str(self.tmp_dir))
        try:
            status, _ = runner.run_command("(exit 7)")
            self.assertEqual(status, 7)
        finally:
            runner.close()

    def test_hash_cache_skips_and_invalidates_on_edit(self):
        """2. Hash-cache: true hash skip on PENDING step + env re-source, and edit invalidation."""
        md_content_1 = (
            "## Step 1: Cache Step\n"
            "```bash\n"
            "echo cache-me\n"
            "```\n"
        )
        md_file = self.tmp_dir / "lab.md"
        md_file.write_text(md_content_1, encoding="utf-8")

        # First run - populates .state and .env files
        t1 = tester.StatefulCodelabTester(str(md_file))
        success1 = t1.run()
        self.assertTrue(success1)

        state_file = self.tmp_dir / "lab.md.state"
        env_file = self.tmp_dir / "lab.md.env"
        self.assertTrue(state_file.exists())
        self.assertTrue(env_file.exists())
        initial_hashes = state_file.read_text().splitlines()
        self.assertEqual(len(initial_hashes), 1)

        # Reset step state to PENDING while keeping command UNCHANGED.
        # This tests true hash-cache skip (loop reaches hash check) & env re-source.
        step_1_file = self.tmp_dir / ".tester_state" / "step-001.json"
        with open(step_1_file, "r") as sf:
            step_data = json.load(sf)
        step_data["status"] = "PENDING"
        with open(step_1_file, "w") as sf:
            json.dump(step_data, sf)

        mock_runner = MagicMock()
        mock_runner.run_command.return_value = (0, "mock output")
        with patch.object(tester, "SubshellRunner", return_value=mock_runner):
            t2 = tester.StatefulCodelabTester(str(md_file))
            success2 = t2.run()

        self.assertTrue(success2)
        executed_cmds = [call.args[0] for call in mock_runner.run_command.call_args_list]

        # Assert environment re-source call was issued on resume
        expected_env_cmd = f"source {env_file}"
        self.assertIn(expected_env_cmd, executed_cmds)

        # Assert command was skipped via hash cache (NOT executed)
        self.assertNotIn("echo cache-me", executed_cmds)

        # Edit command text - invalidates hash and re-runs
        md_content_2 = (
            "## Step 1: Cache Step\n"
            "```bash\n"
            "echo cache-edited\n"
            "```\n"
        )
        md_file.write_text(md_content_2, encoding="utf-8")

        # Reset step state to PENDING to allow tester to evaluate edited command
        with open(step_1_file, "r") as sf:
            step_data = json.load(sf)
        step_data["status"] = "PENDING"
        with open(step_1_file, "w") as sf:
            json.dump(step_data, sf)

        mock_runner2 = MagicMock()
        mock_runner2.run_command.return_value = (0, "edited output")
        with patch.object(tester, "SubshellRunner", return_value=mock_runner2):
            t3 = tester.StatefulCodelabTester(str(md_file))
            success3 = t3.run()

        self.assertTrue(success3)
        executed_cmds2 = [call.args[0] for call in mock_runner2.run_command.call_args_list]
        self.assertIn("echo cache-edited", executed_cmds2)

    def test_env_persistence_across_steps_and_resumes(self):
        """3. Env persistence: export in step 1 is visible to step 2; .env cache is saved."""
        md_content = (
            "## Step 1: Export Var\n"
            "```bash\n"
            "export TEST_CONTRACT_VAR=hello_world\n"
            "```\n"
            "## Step 2: Read Var\n"
            "```bash\n"
            "echo \"VAL=$TEST_CONTRACT_VAR\"\n"
            "```\n"
        )
        md_file = self.tmp_dir / "lab.md"
        md_file.write_text(md_content, encoding="utf-8")

        t = tester.StatefulCodelabTester(str(md_file))
        success = t.run()

        self.assertTrue(success)
        self.assertIn("VAL=hello_world", t.steps[1]["output"])

        env_file = self.tmp_dir / "lab.md.env"
        self.assertTrue(env_file.exists())
        env_text = env_file.read_text()
        self.assertIn("TEST_CONTRACT_VAR", env_text)

    def test_state_resume_skips_done_steps_and_re_reads_edited_commands(self):
        """4. State resume: DONE steps are skipped on re-run; edited commands are re-read."""
        md_content_v1 = (
            "## Step 1: Step One\n"
            "```bash\n"
            "echo step1-v1\n"
            "```\n"
            "## Step 2: Step Two\n"
            "```bash\n"
            "echo step2-v1\n"
            "```\n"
        )
        md_file = self.tmp_dir / "lab.md"
        md_file.write_text(md_content_v1, encoding="utf-8")

        # Initial state setup: step 1 DONE, step 2 FAILED
        t1 = tester.StatefulCodelabTester(str(md_file))
        t1.load_or_initialize_state()
        t1.steps[0]["status"] = "DONE"
        t1.steps[0]["output"] = "step1 output"
        t1.steps[1]["status"] = "FAILED"
        t1.save_state()

        # Edit step 2 command in markdown
        md_content_v2 = (
            "## Step 1: Step One\n"
            "```bash\n"
            "echo step1-v1\n"
            "```\n"
            "## Step 2: Step Two\n"
            "```bash\n"
            "echo step2-fixed\n"
            "```\n"
        )
        md_file.write_text(md_content_v2, encoding="utf-8")

        t2 = tester.StatefulCodelabTester(str(md_file))
        t2.load_or_initialize_state()

        # Step 1 should remain DONE
        self.assertEqual(t2.steps[0]["status"], "DONE")
        self.assertEqual(t2.steps[0]["output"], "step1 output")

        # Step 2 keeps FAILED status from cache, but re-reads fresh command
        self.assertEqual(t2.steps[1]["status"], "FAILED")
        self.assertEqual(t2.steps[1]["commands"], ["echo step2-fixed"])

    def test_bug_json_contract_v1_schema_and_locations(self):
        """5. Bug-JSON contract v1: exact schema keys written to local and central dirs."""
        md_content = (
            "## Step 1: Faulty Step\n"
            "```bash\n"
            "echo faulty\n"
            "```\n"
        )
        md_file = self.tmp_dir / "lab.md"
        md_file.write_text(md_content, encoding="utf-8")

        t = tester.StatefulCodelabTester(str(md_file))
        t.load_or_initialize_state()

        t.file_bug_and_notify_mailbox(
            failed_step=1,
            failed_command="echo faulty",
            error_output="command failed with exit code 1"
        )

        self.assertTrue(any("bug_to_lesson_processor.py" in str(c) for c in self.processor_popen_calls))

        local_bugs_dir = self.tmp_dir / "bugs"
        local_bug_files = list(local_bugs_dir.glob("bug_*.json"))
        self.assertEqual(len(local_bug_files), 1)

        central_bugs_dir = self.fake_home / ".gemini" / "jetski" / "bugs"
        central_bug_files = list(central_bugs_dir.glob("bug_*.json"))
        self.assertEqual(len(central_bug_files), 1)

        with open(local_bug_files[0], "r") as f:
            bug_data = json.load(f)

        required_keys = ["bug_id", "timestamp", "lab_name", "step_number", "step_title", "error_logs", "status", "remediation"]
        for key in required_keys:
            self.assertIn(key, bug_data)

        self.assertEqual(bug_data["status"], "NEW")
        self.assertEqual(bug_data["remediation"], "")
        self.assertEqual(bug_data["step_number"], 1)

        self.assertIn("failed_command", bug_data["error_logs"])
        self.assertIn("stderr_output", bug_data["error_logs"])
        self.assertEqual(bug_data["error_logs"]["failed_command"], "echo faulty")
        self.assertEqual(bug_data["error_logs"]["stderr_output"], "command failed with exit code 1")

    def test_sanitize_command_project_id_and_custom_vars(self):
        """6. sanitize_command: <PROJECT_ID>/$PROJECT_ID substitution & custom variables.json replacement."""
        cmd = (
            "echo <PROJECT_ID>\n"
            "echo $PROJECT_ID\n"
            "echo ${PROJECT_ID}\n"
            "echo <CUSTOM_REGION>\n"
            "echo $CUSTOM_ZONE\n"
            "echo ${CUSTOM_ZONE}"
        )
        custom_vars = {
            "CUSTOM_REGION": "us-central1",
            "CUSTOM_ZONE": "us-central1-a"
        }
        sanitized = tester.sanitize_command(cmd, project_id="my-test-project", custom_vars=custom_vars)

        self.assertIn("echo my-test-project", sanitized)
        self.assertNotIn("<PROJECT_ID>", sanitized)
        self.assertNotIn("$PROJECT_ID", sanitized)
        self.assertNotIn("${PROJECT_ID}", sanitized)

        self.assertIn("echo us-central1", sanitized)
        self.assertIn("echo us-central1-a", sanitized)
        self.assertNotIn("<CUSTOM_REGION>", sanitized)
        self.assertNotIn("$CUSTOM_ZONE", sanitized)
        self.assertNotIn("${CUSTOM_ZONE}", sanitized)

    def test_multiline_midfailure_currently_masked(self):
        """7. KNOWN BUG PIN (Issue #121):
        In tester.py SubshellRunner.run_command, a multiline code block is wrapped in
        '{ cmd; } < /dev/null' without 'set -e'. When line 2 of a 3-line block fails,
        bash continues executing line 3, and only the exit code of line 3 ($status) is returned.
        This currently causes a mid-block failure to be masked as DONE.
        Upcoming PR #121 will fix this exec loop, which must flip this test assertion from DONE -> FAILED.
        """
        md_content = (
            "## Step 1: Multiline Block\n"
            "```bash\n"
            "echo line1-ok\n"
            "non_existent_command_fails_here_12345\n"
            "echo line3-ok\n"
            "```\n"
        )
        md_file = self.tmp_dir / "lab.md"
        md_file.write_text(md_content, encoding="utf-8")

        t = tester.StatefulCodelabTester(str(md_file))
        success = t.run()

        # PR #121 fix verification: mid-block failure now properly caught as FAILED
        self.assertFalse(success)
        self.assertEqual(t.steps[0]["status"], "FAILED")


if __name__ == "__main__":
    unittest.main()
