import pathlib
import re
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
TASKS_RULE_PATH = REPO / ".agents" / "rules" / "tasks.md"


class TestTasksRuleTemplate(unittest.TestCase):
    def test_tasks_template_has_zero_indentation(self):
        """Assert no line inside the template HTML block in tasks.md starts with whitespace followed by an HTML tag."""
        content = TASKS_RULE_PATH.read_text(encoding="utf-8")

        # Extract ```html ... ``` block
        match = re.search(r"```html\n(.*?)```", content, re.DOTALL)
        self.assertIsNotNone(match, "Could not find ```html block in tasks.md")

        html_block = match.group(1)
        indented_html_lines = []

        for line_num, line in enumerate(html_block.splitlines(), start=1):
            if re.match(r"^\s+<", line):
                indented_html_lines.append(f"Line {line_num}: '{line}'")

        self.assertEqual(
            indented_html_lines,
            [],
            "Found indented HTML lines in tasks.md template block:\n"
            + "\n".join(indented_html_lines),
        )

    def test_tasks_template_contains_project_id_and_test_status_header_fields(self):
        """Assert template header block contains GCP Project ID and Test Status fields (#112)."""
        content = TASKS_RULE_PATH.read_text(encoding="utf-8")

        self.assertIn(
            "GCP Project ID:",
            content,
            "tasks.md template header is missing 'GCP Project ID:' field (#112)",
        )
        self.assertIn(
            "Test Status:",
            content,
            "tasks.md template header is missing 'Test Status:' field (#112)",
        )

if __name__ == "__main__":
    unittest.main()
