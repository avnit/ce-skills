import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TESTER_PATH = REPO / ".agents" / "skills" / "codelab-validation" / "scripts" / "tester.py"


def _load_tester():
    spec = importlib.util.spec_from_file_location("tester", TESTER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["tester"] = module
    spec.loader.exec_module(module)
    return module


tester = _load_tester()


class TestTesterExecLoop(unittest.TestCase):

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

    def test_flat_three_line_block_line2_failure(self):
        """Flat 3-line block: line 2 fails => FAILED, line 2 named in bug JSON, line 3 unexecuted."""
        md_content = (
            "## Step 1: Flat Block\n"
            "```bash\n"
            "touch line1_marker.txt\n"
            "non_existent_command_fails_12345\n"
            "touch line3_marker.txt\n"
            "```\n"
        )
        md_file = self.tmp_dir / "lab.md"
        md_file.write_text(md_content, encoding="utf-8")

        t = tester.StatefulCodelabTester(str(md_file))
        success = t.run()

        self.assertFalse(success)
        self.assertEqual(t.steps[0]["status"], "FAILED")
        self.assertIn("non_existent_command_fails_12345", t.steps[0]["error"])

        # Check line 1 executed (marker exists)
        self.assertTrue((self.tmp_dir / "line1_marker.txt").exists())
        # Check line 3 did NOT execute (marker does not exist)
        self.assertFalse((self.tmp_dir / "line3_marker.txt").exists())

        # Check bug JSON exactly names line 2 as failed_command
        local_bugs_dir = self.tmp_dir / "bugs"
        local_bug_files = list(local_bugs_dir.glob("bug_*.json"))
        self.assertEqual(len(local_bug_files), 1)

        with open(local_bug_files[0], "r") as f:
            bug_data = json.load(f)
        self.assertEqual(bug_data["error_logs"]["failed_command"], "non_existent_command_fails_12345")

    def test_compound_pure_failure_via_subshell_errexit(self):
        """Compound pure (if/fi) block with internal failure fails via subshell errexit."""
        md_content = (
            "## Step 1: Compound Pure\n"
            "```bash\n"
            "if [ 1 -eq 1 ]; then\n"
            "    non_existent_cmd_inside_if_54321\n"
            "fi\n"
            "```\n"
        )
        md_file = self.tmp_dir / "lab.md"
        md_file.write_text(md_content, encoding="utf-8")

        t = tester.StatefulCodelabTester(str(md_file))
        success = t.run()

        self.assertFalse(success)
        self.assertEqual(t.steps[0]["status"], "FAILED")

    def test_compound_stateful_warning_output(self):
        """Compound stateful block runs and includes warning text in step output."""
        md_content = (
            "## Step 1: Compound Stateful\n"
            "```bash\n"
            "if [ 1 -eq 1 ]; then\n"
            "    export MY_STATEFUL_VAR=test_value\n"
            "fi\n"
            "```\n"
        )
        md_file = self.tmp_dir / "lab.md"
        md_file.write_text(md_content, encoding="utf-8")

        t = tester.StatefulCodelabTester(str(md_file))
        success = t.run()

        self.assertTrue(success)
        self.assertEqual(t.steps[0]["status"], "DONE")
        self.assertIn("[WARNING] Intermediate command failures inside this compound stateful block", t.steps[0]["output"])

    def test_heredoc_execution_file_landing(self):
        """Heredoc block (cat <<EOF) executes byte-identically and creates expected file."""
        md_content = (
            "## Step 1: Heredoc\n"
            "```bash\n"
            "cat <<EOF > output.txt\n"
            "hello world\n"
            "EOF\n"
            "```\n"
        )
        md_file = self.tmp_dir / "lab.md"
        md_file.write_text(md_content, encoding="utf-8")

        t = tester.StatefulCodelabTester(str(md_file))
        success = t.run()

        self.assertTrue(success)
        output_file = self.tmp_dir / "output.txt"
        self.assertTrue(output_file.exists())
        self.assertEqual(output_file.read_text().strip(), "hello world")

    def test_export_in_flat_unit_visible_to_next_unit_and_next_step(self):
        """Export in a flat unit is visible to subsequent units in the block and to the next step."""
        md_content = (
            "## Step 1: Export in Flat Unit\n"
            "```bash\n"
            "export FLAT_VAR=value_123\n"
            "echo \"UNIT2=$FLAT_VAR\"\n"
            "```\n"
            "## Step 2: Read in Next Step\n"
            "```bash\n"
            "echo \"STEP2=$FLAT_VAR\"\n"
            "```\n"
        )
        md_file = self.tmp_dir / "lab.md"
        md_file.write_text(md_content, encoding="utf-8")

        t = tester.StatefulCodelabTester(str(md_file))
        success = t.run()

        self.assertTrue(success)
        self.assertIn("UNIT2=value_123", t.steps[0]["output"])
        self.assertIn("STEP2=value_123", t.steps[1]["output"])

    def test_finer_resume_per_unit_hash_cache(self):
        """Fine-grained resume: in a 2-command flat block, editing command 2 skips command 1 and re-executes command 2."""
        md_content_1 = (
            "## Step 1: Two Commands\n"
            "```bash\n"
            "echo cmd1-initial\n"
            "echo cmd2-initial\n"
            "```\n"
        )
        md_file = self.tmp_dir / "lab.md"
        md_file.write_text(md_content_1, encoding="utf-8")

        t1 = tester.StatefulCodelabTester(str(md_file))
        success1 = t1.run()
        self.assertTrue(success1)

        # Edit command 2 in markdown
        md_content_2 = (
            "## Step 1: Two Commands\n"
            "```bash\n"
            "echo cmd1-initial\n"
            "echo cmd2-edited\n"
            "```\n"
        )
        md_file.write_text(md_content_2, encoding="utf-8")

        # Reset step state to PENDING to force evaluation of step 1
        step_1_file = self.tmp_dir / ".tester_state" / "step-001.json"
        with open(step_1_file, "r") as sf:
            step_data = json.load(sf)
        step_data["status"] = "PENDING"
        with open(step_1_file, "w") as sf:
            json.dump(step_data, sf)

        mock_runner = MagicMock()
        mock_runner.run_command.return_value = (0, "edited output")

        with patch.object(tester, "SubshellRunner", return_value=mock_runner):
            t2 = tester.StatefulCodelabTester(str(md_file))
            success2 = t2.run()

        self.assertTrue(success2)
        executed_cmds = [call.args[0] for call in mock_runner.run_command.call_args_list]

        # Command 1 (echo cmd1-initial) should be skipped via hash cache
        self.assertNotIn("echo cmd1-initial", executed_cmds)
        # Command 2 (echo cmd2-edited) should be re-executed
        self.assertIn("echo cmd2-edited", executed_cmds)


if __name__ == "__main__":
    unittest.main()
