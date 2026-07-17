import importlib.util
import sys
import unittest
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

    def test_main_run_defers_cleanup_and_explicit_phase_runs_it(self):
        import tempfile
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
            with unittest.mock.patch.object(tester, "SubshellRunner", return_value=mock_runner):
                t_test = tester.StatefulCodelabTester(str(md_file), phase="test")
                success_test = t_test.run()

                self.assertTrue(success_test)
                self.assertEqual(t_test.steps[0]["status"], "DONE")
                self.assertEqual(t_test.steps[1]["status"], "DEFERRED")
                self.assertIn("echo deploy-workload", mock_runner.executed_commands)
                self.assertNotIn("echo destroy-workload", mock_runner.executed_commands)

                # Now run explicit cleanup phase
                mock_runner_cleanup = MockSubshellRunner()
                with unittest.mock.patch.object(tester, "SubshellRunner", return_value=mock_runner_cleanup):
                    t_cleanup = tester.StatefulCodelabTester(str(md_file), phase="cleanup")
                    success_cleanup = t_cleanup.run()

                    self.assertTrue(success_cleanup)
                    self.assertEqual(t_cleanup.steps[1]["status"], "DONE")
                    self.assertIn("echo destroy-workload", mock_runner_cleanup.executed_commands)

    def test_title_regex_heuristic_removed(self):
        import tempfile
        md_content = (
            "## Step 1: Clean up your data\n"
            "```bash\n"
            "echo normal-step-command\n"
            "```\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir_str:
            tmp_dir = Path(tmp_dir_str)
            md_file = tmp_dir / "lab.md"
            md_file.write_text(md_content, encoding="utf-8")

            mock_runner = MockSubshellRunner()
            with unittest.mock.patch.object(tester, "SubshellRunner", return_value=mock_runner):
                t = tester.StatefulCodelabTester(str(md_file), phase="test")
                success = t.run()

                self.assertTrue(success)
                # Without explicit <!-- cleanup --> marker, title regex is NOT used to skip
                self.assertEqual(t.steps[0]["status"], "DONE")
                self.assertIn("echo normal-step-command", mock_runner.executed_commands)


if __name__ == "__main__":
    unittest.main()
