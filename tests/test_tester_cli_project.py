import importlib.util
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = pathlib.Path(__file__).resolve().parent.parent
TESTER_PATH = REPO / ".agents" / "skills" / "codelab-validation" / "scripts" / "tester.py"
VALIDATOR_PATH = REPO / ".agents" / "skills" / "codelab-validation" / "scripts" / "validator.py"


def _load(path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(path.stem, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


tester = _load(TESTER_PATH)
validator = _load(VALIDATOR_PATH)


class TestTesterCLIProjectEnforcement(unittest.TestCase):
    def setUp(self):
        self.tmp_dir_obj = tempfile.TemporaryDirectory()
        self.tmp_dir = pathlib.Path(self.tmp_dir_obj.name)
        self.lab_dir = self.tmp_dir / "lab"
        self.lab_dir.mkdir(parents=True, exist_ok=True)
        self.md_file = self.lab_dir / "test.lab.md"
        self.md_file.write_text(
            "# Test Lab\n\n## Step 1: Print Project\n```bash\necho \"P=$PROJECT_ID C=$CLOUDSDK_CORE_PROJECT\"\n```\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp_dir_obj.cleanup()

    def test_cli_fails_without_project_flags_and_creates_no_state_dir(self):
        """main() with neither flag exits non-zero and creates no .tester_state directory."""
        state_dir = self.lab_dir / ".tester_state"
        self.assertFalse(state_dir.exists())

        with patch.object(sys, "argv", ["tester.py", str(self.md_file)]):
            with self.assertRaises(SystemExit) as cm:
                tester.main()
            self.assertEqual(cm.exception.code, 1)

        self.assertFalse(state_dir.exists())

    def test_cli_with_project_id_exports_both_env_vars(self):
        """main() --project-id my-proj exports PROJECT_ID and CLOUDSDK_CORE_PROJECT in subshell."""
        with patch.object(sys, "argv", ["tester.py", str(self.md_file), "--project-id", "my-proj"]):
            with self.assertRaises(SystemExit) as cm:
                tester.main()
            self.assertEqual(cm.exception.code, 0)

        # Inspect saved step output
        step_json = self.lab_dir / ".tester_state" / "step-001.json"
        self.assertTrue(step_json.exists())
        data = json.loads(step_json.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "DONE")
        self.assertIn("P=my-proj C=my-proj", data["output"])

    def test_cli_with_allow_active_project_adopts_ambient_project(self):
        """main() --allow-active-project adopts ambient project and logs warning banner."""
        with patch.object(tester, "get_active_project", return_value="ambient-proj"), \
             patch.object(sys, "argv", ["tester.py", str(self.md_file), "--allow-active-project"]):
            with self.assertRaises(SystemExit) as cm:
                tester.main()
            self.assertEqual(cm.exception.code, 0)

        step_json = self.lab_dir / ".tester_state" / "step-001.json"
        data = json.loads(step_json.read_text(encoding="utf-8"))
        self.assertIn("P=ambient-proj C=ambient-proj", data["output"])

    def test_cli_with_allow_active_project_fails_when_ambient_unknown(self):
        """main() --allow-active-project fails if ambient resolves to Unknown or empty."""
        for unknown_val in ["Unknown", ""]:
            with patch.object(tester, "get_active_project", return_value=unknown_val), \
                 patch.object(sys, "argv", ["tester.py", str(self.md_file), "--allow-active-project"]):
                with self.assertRaises(SystemExit) as cm:
                    tester.main()
                self.assertEqual(cm.exception.code, 1)

    def test_validator_includes_project_id_flag_in_tester_cmd(self):
        """validator.py appends --project-id {project_id} to tester_cmd."""
        with patch.object(validator, "run_command") as mock_run_cmd, \
             patch.object(validator, "setup_active_lab"), \
             patch.object(validator, "scan_placeholders", return_value=[]), \
             patch.object(validator, "compile_report"), \
             patch.object(os, "makedirs"), \
             patch("builtins.open", unittest.mock.mock_open()), \
             patch.object(sys, "argv", ["validator.py", "--src", "dummy.lab.md", "--project-id", "my-test-proj"]), \
             patch.object(sys, "exit"):
            mock_run_cmd.return_value = (True, "success")
            validator.main()

            executed_cmds = [call.args[0] for call in mock_run_cmd.call_args_list]
            tester_calls = [cmd for cmd in executed_cmds if "tester.py" in cmd]
            self.assertTrue(len(tester_calls) > 0)
            self.assertIn("--project-id my-test-proj", tester_calls[0])


if __name__ == "__main__":
    unittest.main()
