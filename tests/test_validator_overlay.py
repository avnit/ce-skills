import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = REPO / ".agents" / "skills" / "codelab-validation" / "scripts" / "validator.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location("validator", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["validator"] = module
    spec.loader.exec_module(module)
    return module


validator = _load_validator()


class TestValidatorOverlay(unittest.TestCase):

    def setUp(self):
        self.tmp_dir_obj = tempfile.TemporaryDirectory()
        self.tmp_dir = Path(self.tmp_dir_obj.name)
        self.validate_dir = self.tmp_dir / "validate_lab"
        self.validate_dir.mkdir(parents=True, exist_ok=True)
        self.active_lab_path = self.validate_dir / "active-lab.lab.md"

    def tearDown(self):
        self.tmp_dir_obj.cleanup()

    def test_failing_curl_post_no_longer_rewritten(self):
        """curl POST googleapis.com blocks are no longer appended with || true."""
        src_content = (
            "# My Lab\n\n"
            "```bash\n"
            "curl -X POST https://example.googleapis.com/v1/projects/my-proj/services\n"
            "```\n"
        )
        src_file = self.tmp_dir / "src.md"
        src_file.write_text(src_content, encoding="utf-8")

        validator.setup_active_lab(str(src_file), str(self.validate_dir), str(self.active_lab_path))

        staged_content = self.active_lab_path.read_text(encoding="utf-8")
        self.assertNotIn("|| true", staged_content)
        self.assertIn("curl -X POST https://example.googleapis.com/v1/projects/my-proj/services", staged_content)

    def test_no_overlay_equals_source_plus_generic_policies(self):
        """When no overlay.json exists, staged lab contains source + generic policies only."""
        src_content = (
            "# Title\n\n"
            "```bash\n"
            "gcloud auth login\n"
            "echo <your-project-id>\n"
            "```\n"
        )
        src_file = self.tmp_dir / "src.md"
        src_file.write_text(src_content, encoding="utf-8")

        transforms = validator.setup_active_lab(str(src_file), str(self.validate_dir), str(self.active_lab_path))

        self.assertEqual(transforms, [])
        staged_content = self.active_lab_path.read_text(encoding="utf-8")

        # Generic policies applied: auth login commented out, project id substituted
        self.assertIn("# gcloud auth login", staged_content)
        self.assertIn("echo ${PROJECT_ID}", staged_content)
        self.assertNotIn("<your-project-id>", staged_content)

    def test_literal_regex_and_append_after_match_overlays(self):
        """Literal replacements, regex replacements, and append_after_match apply correctly."""
        src_content = (
            "# Overlay Test Lab\n\n"
            "```bash\n"
            "echo LITERAL_OLD\n"
            "gcloud compute instances create my-vm-123\n"
            "```\n"
        )
        src_file = self.tmp_dir / "src.md"
        src_file.write_text(src_content, encoding="utf-8")

        overlay_data = {
            "description": "Test overlay rules",
            "replacements": [
                {"find": "LITERAL_OLD", "replace": "LITERAL_NEW", "regex": False},
                {"find": r"my-vm-\d+", "replace": "my-vm-456", "regex": True}
            ],
            "append_after_match": [
                {
                    "match": "gcloud compute instances create",
                    "append_lines": ["echo VM creation finished"]
                }
            ]
        }
        overlay_file = self.validate_dir / "overlay.json"
        overlay_file.write_text(json.dumps(overlay_data), encoding="utf-8")

        transforms = validator.setup_active_lab(str(src_file), str(self.validate_dir), str(self.active_lab_path))

        self.assertEqual(len(transforms), 3)
        staged_content = self.active_lab_path.read_text(encoding="utf-8")

        self.assertIn("LITERAL_NEW", staged_content)
        self.assertNotIn("LITERAL_OLD", staged_content)
        self.assertIn("my-vm-456", staged_content)
        self.assertIn("echo VM creation finished", staged_content)

    def test_overlay_json_survives_run_dir_cleanup(self):
        """setup_active_lab's cleanup preserves overlay.json."""
        overlay_file = self.validate_dir / "overlay.json"
        overlay_file.write_text(json.dumps({"description": "Keep me"}), encoding="utf-8")

        # Create a junk file in validate_dir that SHOULD be cleaned up
        junk_file = self.validate_dir / "leftover_junk.txt"
        junk_file.write_text("trash", encoding="utf-8")

        src_content = "# Lab\n\n```bash\necho hello\n```\n"
        src_file = self.tmp_dir / "src.md"
        src_file.write_text(src_content, encoding="utf-8")

        validator.setup_active_lab(str(src_file), str(self.validate_dir), str(self.active_lab_path))

        self.assertTrue(overlay_file.exists())
        self.assertFalse(junk_file.exists())

    def test_malformed_overlay_json_causes_hard_error(self):
        """Malformed overlay.json causes validator to exit non-zero with a clear error."""
        overlay_file = self.validate_dir / "overlay.json"
        overlay_file.write_text("{ malformed json ...", encoding="utf-8")

        src_content = "# Lab\n\n```bash\necho hello\n```\n"
        src_file = self.tmp_dir / "src.md"
        src_file.write_text(src_content, encoding="utf-8")

        with self.assertRaises(SystemExit) as cm:
            validator.setup_active_lab(str(src_file), str(self.validate_dir), str(self.active_lab_path))

        self.assertEqual(cm.exception.code, 1)

    def test_generic_policies_still_applied(self):
        """Generic policies (auth login, project id, optional sections) are applied."""
        src_content = (
            "# Lab\n\n"
            "```bash\n"
            "gcloud auth application-default login\n"
            "gcloud config set project <project-id>\n"
            "```\n\n"
            "## Optional Section (Optional)\n"
            "```bash\n"
            "echo optional_cmd\n"
            "```\n"
        )
        src_file = self.tmp_dir / "src.md"
        src_file.write_text(src_content, encoding="utf-8")

        validator.setup_active_lab(str(src_file), str(self.validate_dir), str(self.active_lab_path))

        staged_content = self.active_lab_path.read_text(encoding="utf-8")
        self.assertIn("# gcloud auth application-default login", staged_content)
        self.assertIn("gcloud config set project ${PROJECT_ID}", staged_content)
        # Optional section code block is commented out
        self.assertIn("# ```bash\n# echo optional_cmd", staged_content)

    def test_compile_report_includes_overlay_transforms_section(self):
        """compile_report includes '## Applied Overlay Transforms' section."""
        report_dir = self.tmp_dir / "report"
        report_path = report_dir / "validation-report.md"
        tester_state_dir = self.tmp_dir / ".tester_state"
        tester_state_dir.mkdir(parents=True, exist_ok=True)

        applied = ["Literal replacement: 'a' -> 'b'", "Append after match 'c': Appended 1 lines"]
        validator.compile_report(str(tester_state_dir), str(report_dir), str(report_path), "test-proj", True, applied_transforms=applied)

        report_content = report_path.read_text(encoding="utf-8")
        self.assertIn("## Applied Overlay Transforms", report_content)
        self.assertIn("- Literal replacement: 'a' -> 'b'", report_content)
        self.assertIn("- Append after match 'c': Appended 1 lines", report_content)

        # Test none applied case
        validator.compile_report(str(tester_state_dir), str(report_dir), str(report_path), "test-proj", True, applied_transforms=[])
        report_content_none = report_path.read_text(encoding="utf-8")
        self.assertIn("None — lab validated as written", report_content_none)


if __name__ == "__main__":
    unittest.main()
