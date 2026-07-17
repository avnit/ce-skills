import argparse
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add script directory to sys.path for importing get_release_notes
script_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".agents", "skills", "gcp-release-notes", "scripts"))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

import get_release_notes


class TestGcpReleaseNotes(unittest.TestCase):

    def test_html_to_markdown_conversions(self):
        """Verify HTML tags and pipe characters are properly converted to Markdown."""
        raw_html = "<p>Feature <b>bold</b> and <i>italic</i> with <code>code</code> and <a href=\"https://cloud.google.com\">link</a>.</p>"
        md_table = get_release_notes.html_to_markdown(raw_html, is_table_mode=True)
        self.assertIn("**bold**", md_table)
        self.assertIn("*italic*", md_table)
        self.assertIn("`code`", md_table)
        self.assertIn("[link](https://cloud.google.com)", md_table)

        pipe_text = "Data | Column | Value"
        escaped = get_release_notes.html_to_markdown(pipe_text, is_table_mode=True)
        self.assertIn("Data \\| Column \\| Value", escaped)

    def test_validate_date(self):
        """Verify date format validator."""
        self.assertEqual(get_release_notes.validate_date("2026-05-01"), "2026-05-01")
        with self.assertRaises(argparse.ArgumentTypeError):
            get_release_notes.validate_date("05-01-2026")

    @patch("get_release_notes.load_gcp_config")
    @patch("subprocess.run")
    @patch("urllib.request.urlopen")
    def test_generate_explanation_http_fallback_dynamic_project(self, mock_urlopen, mock_subproc, mock_config):
        """Verify HTTP fallback uses dynamic project ID and parses JSON correctly."""
        mock_config.return_value = {"billing_project": "custom-test-project-123"}
        mock_subproc.return_value = MagicMock(returncode=0, stdout="mock_token\n")

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Architects can enforce fine-grained egress URL filtering."}
                        ]
                    }
                }
            ]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Force SDK import to fail so HTTP fallback runs
        with patch.dict(sys.modules, {"google.genai": None}):
            result = get_release_notes.generate_explanation("Cloud NGFW", "FEATURE", "URL filtering overview")

        self.assertEqual(result, "Architects can enforce fine-grained egress URL filtering.")
        
        # Verify URL built with dynamic project ID
        called_req = mock_urlopen.call_args[0][0]
        self.assertIn("projects/custom-test-project-123/locations", called_req.full_url)

    @patch("subprocess.run")
    def test_generate_explanation_honest_failure_no_fabrication(self, mock_subproc):
        """Verify failures report honest 'AI Explanation Unavailable' error without silent text fabrication."""
        mock_subproc.return_value = MagicMock(returncode=1, stderr="Auth error")

        with patch.dict(sys.modules, {"google.genai": None}):
            result = get_release_notes.generate_explanation("Cloud Load Balancing", "FEATURE", "Some long release text")

        self.assertTrue(result.startswith("⚠️ AI Explanation Unavailable:"))
        self.assertNotIn("Architectural Update:", result)


if __name__ == "__main__":
    unittest.main()
