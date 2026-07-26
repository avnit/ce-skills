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

    def test_units_field_flat_three_line_unit_failure(self):
        """Flat 3-unit block: unit 2 fails => units = [DONE, FAILED, PENDING] in step-001.json."""
        md_content = (
            "## Step 1: Flat Units Test\n"
            "```bash\n"
            "echo line1\n"
            "non_existent_command_fails_9999\n"
            "echo line3\n"
            "```\n"
        )
        md_file = self.tmp_dir / "lab.md"
        md_file.write_text(md_content, encoding="utf-8")

        t = tester.StatefulCodelabTester(str(md_file))
        success = t.run()

        self.assertFalse(success)
        step_1_file = self.tmp_dir / ".tester_state" / "step-001.json"
        with open(step_1_file, "r") as f:
            step_json = json.load(f)

        units = step_json.get("units", [])
        self.assertEqual(len(units), 3)

        self.assertEqual(units[0]["status"], "DONE")
        self.assertEqual(units[0]["text"], "echo line1")
        self.assertEqual(units[0]["tier"], "flat")

        self.assertEqual(units[1]["status"], "FAILED")
        self.assertEqual(units[1]["text"], "non_existent_command_fails_9999")
        self.assertEqual(units[1]["tier"], "flat")
        self.assertIn("non_existent_command_fails_9999", units[1]["output_tail"])

        self.assertEqual(units[2]["status"], "PENDING")
        self.assertEqual(units[2]["text"], "echo line3")
        self.assertEqual(units[2]["tier"], "flat")

    def test_units_field_skipped_cached_on_resume(self):
        """Resuming with a cached unit records status SKIPPED-CACHED in step units."""
        md_content_1 = (
            "## Step 1: Cache Units\n"
            "```bash\n"
            "echo cached_unit_1\n"
            "echo cached_unit_2\n"
            "```\n"
        )
        md_file = self.tmp_dir / "lab.md"
        md_file.write_text(md_content_1, encoding="utf-8")

        t1 = tester.StatefulCodelabTester(str(md_file))
        self.assertTrue(t1.run())

        md_content_2 = (
            "## Step 1: Cache Units\n"
            "```bash\n"
            "echo cached_unit_1\n"
            "echo new_unit_2\n"
            "```\n"
        )
        md_file.write_text(md_content_2, encoding="utf-8")

        step_1_file = self.tmp_dir / ".tester_state" / "step-001.json"
        with open(step_1_file, "r") as sf:
            step_data = json.load(sf)
        step_data["status"] = "PENDING"
        with open(step_1_file, "w") as sf:
            json.dump(step_data, sf)

        t2 = tester.StatefulCodelabTester(str(md_file))
        self.assertTrue(t2.run())

        with open(step_1_file, "r") as f:
            step_json = json.load(f)

        units = step_json.get("units", [])
        self.assertEqual(len(units), 2)
        self.assertEqual(units[0]["status"], "SKIPPED-CACHED")
        self.assertEqual(units[0]["text"], "echo cached_unit_1")
        self.assertEqual(units[1]["status"], "DONE")
        self.assertEqual(units[1]["text"], "echo new_unit_2")

    def test_units_field_compound_blocks(self):
        """Compound blocks produce 1 unit entry with tier compound_pure / compound_stateful."""
        md_content = (
            "## Step 1: Compound Test\n"
            "```bash\n"
            "if [ 1 -eq 1 ]; then\n"
            "    echo pure\n"
            "fi\n"
            "```\n"
            "```bash\n"
            "if [ 1 -eq 1 ]; then\n"
            "    export VAR=stateful\n"
            "fi\n"
            "```\n"
        )
        md_file = self.tmp_dir / "lab.md"
        md_file.write_text(md_content, encoding="utf-8")

        t = tester.StatefulCodelabTester(str(md_file))
        self.assertTrue(t.run())

        step_1_file = self.tmp_dir / ".tester_state" / "step-001.json"
        with open(step_1_file, "r") as f:
            step_json = json.load(f)

        units = step_json.get("units", [])
        self.assertEqual(len(units), 2)
        self.assertEqual(units[0]["tier"], "compound_pure")
        self.assertEqual(units[0]["status"], "DONE")
        self.assertEqual(units[1]["tier"], "compound_stateful")
        self.assertEqual(units[1]["status"], "DONE")

    def test_html_reporter_subrows_rendering(self):
        """html_reporter renders per-unit sub-rows with correct chips under step row."""
        steps = [{
            "num": 1,
            "title": "Reporter Units Step",
            "status": "FAILED",
            "instructions": "Run commands",
            "commands": ["echo line1\necho line2"],
            "units": [
                {"text": "echo line1", "tier": "flat", "status": "DONE", "output_tail": "line1\n"},
                {"text": "echo line2", "tier": "flat", "status": "FAILED", "output_tail": "error line2\n"},
                {"text": "echo line3", "tier": "flat", "status": "PENDING", "output_tail": ""}
            ]
        }]
        html_out = tester.HTMLReporter.generate_board("test-proj", steps)
        self.assertIn("Step 1: Reporter Units Step", html_out)
        self.assertIn(">DONE</span>", html_out)
        self.assertIn(">FAILED</span>", html_out)
        self.assertIn(">PENDING</span>", html_out)
        self.assertIn("echo line1</code>", html_out)

    def test_validator_compile_report_units_details(self):
        """validator.compile_report details include per-unit statuses from step units."""
        val_path = REPO / ".agents" / "skills" / "codelab-validation" / "scripts" / "validator.py"
        spec = importlib.util.spec_from_file_location("validator", val_path)
        val_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(val_mod)

        tester_state_dir = self.tmp_dir / ".tester_state"
        tester_state_dir.mkdir(parents=True, exist_ok=True)

        progress = {"total_steps": 1, "current_step": 1, "status": "FAILED"}
        with open(tester_state_dir / "progress.json", "w") as f:
            json.dump(progress, f)

        step_data = {
            "num": 1,
            "title": "Report Step",
            "status": "FAILED",
            "units": [
                {"text": "gcloud info", "tier": "flat", "status": "DONE", "output_tail": ""},
                {"text": "gcloud fail", "tier": "flat", "status": "FAILED", "output_tail": ""}
            ]
        }
        with open(tester_state_dir / "step-001.json", "w") as f:
            json.dump(step_data, f)

        report_file = self.tmp_dir / "validation-report.md"
        val_mod.compile_report(str(tester_state_dir), str(self.tmp_dir), str(report_file), "test-proj", False)

        report_content = report_file.read_text(encoding="utf-8")
        self.assertIn("[DONE] <code>gcloud info</code>", report_content)
        self.assertIn("[FAILED] <code>gcloud fail</code>", report_content)

    def test_units_field_live_flush_per_unit(self):
        """Live flush: 3-unit step calls write_visual_boards at least once per completed unit."""
        md_content = (
            "## Step 1: Live Flush Test\n"
            "```bash\n"
            "echo unit1\n"
            "echo unit2\n"
            "echo unit3\n"
            "```\n"
        )
        md_file = self.tmp_dir / "lab.md"
        md_file.write_text(md_content, encoding="utf-8")

        t = tester.StatefulCodelabTester(str(md_file))
        with patch.object(t, "write_visual_boards", wraps=t.write_visual_boards) as mock_boards:
            success = t.run()
            self.assertTrue(success)
            # Should be called at least 3 times (once per completed unit) in addition to step start/finish calls
            self.assertGreaterEqual(mock_boards.call_count, 3)


if __name__ == "__main__":
    unittest.main()
