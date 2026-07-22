import importlib.util
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PARSER_PATH = REPO / ".agents" / "skills" / "codelab-validation" / "scripts" / "codelab_parser.py"
TESTER_PATH = REPO / ".agents" / "skills" / "codelab-validation" / "scripts" / "tester.py"


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


codelab_parser = _load_module("codelab_parser", PARSER_PATH)
tester = _load_module("tester", TESTER_PATH)


class TestCodelabParser(unittest.TestCase):

    def test_reexported_symbols_identity(self):
        """Assert move-only invariance: tester.<name> is codelab_parser.<name>."""
        symbols = [
            "_EXECUTABLE_FENCE_LANGS",
            "_FENCE_LINE_RE",
            "_extract_command_blocks",
            "_filter_hermetic_commands",
            "normalize_command",
            "get_cmd_hash",
            "classify_block",
        ]
        for name in symbols:
            self.assertTrue(
                hasattr(tester, name),
                f"tester.py missing re-exported symbol: {name}",
            )
            self.assertIs(
                getattr(tester, name),
                getattr(codelab_parser, name),
                f"tester.{name} is not codelab_parser.{name}",
            )

    def test_heredoc_block_compound_pure(self):
        """Heredoc EOF block stays whole and is classified as compound_pure."""
        block = (
            "cat <<EOF > test.txt\n"
            "line 1\n"
            "line 2\n"
            "EOF"
        )
        tier, units = codelab_parser.classify_block(block)
        self.assertEqual(tier, "compound_pure")
        self.assertEqual(units, [block])

    def test_backslash_continuation_joins_to_single_flat_unit(self):
        """Backslash line-continuations join into a single logical line unit."""
        block = (
            "gcloud compute instances create my-vm \\\n"
            "    --zone=us-central1-a \\\n"
            "    --machine-type=e2-micro"
        )
        tier, units = codelab_parser.classify_block(block)
        self.assertEqual(tier, "flat")
        self.assertEqual(
            units,
            ["gcloud compute instances create my-vm --zone=us-central1-a --machine-type=e2-micro"],
        )

    def test_operator_continuation_and_operator(self):
        """Line ending in && continues onto next line as a single flat unit."""
        block = (
            "gsutil cp x y &&\n"
            "echo done"
        )
        tier, units = codelab_parser.classify_block(block)
        self.assertEqual(tier, "flat")
        self.assertEqual(units, ["gsutil cp x y && echo done"])

    def test_operator_continuation_pipe(self):
        """Line ending in | continues onto next line as a single flat unit."""
        block = (
            "cat file |\n"
            "grep pattern"
        )
        tier, units = codelab_parser.classify_block(block)
        self.assertEqual(tier, "flat")
        self.assertEqual(units, ["cat file | grep pattern"])

    def test_flat_three_line_block(self):
        """Flat 3-line block splits into 3 logical units."""
        block = "echo 1\necho 2\necho 3"
        tier, units = codelab_parser.classify_block(block)
        self.assertEqual(tier, "flat")
        self.assertEqual(units, ["echo 1", "echo 2", "echo 3"])

    def test_comments_and_blanks_dropped(self):
        """Comment lines and blank lines are dropped from flat units."""
        block = (
            "# Top comment\n"
            "\n"
            "echo hello\n"
            "  # Inline leading comment\n"
            "\n"
            "echo world\n"
        )
        tier, units = codelab_parser.classify_block(block)
        self.assertEqual(tier, "flat")
        self.assertEqual(units, ["echo hello", "echo world"])

    def test_control_flow_if_fi_compound_pure(self):
        """Control-flow if/fi block without state mutation is compound_pure."""
        block = (
            "if [ -f file.txt ]; then\n"
            "    echo exists\n"
            "fi"
        )
        tier, units = codelab_parser.classify_block(block)
        self.assertEqual(tier, "compound_pure")
        self.assertEqual(units, [block])

    def test_control_flow_with_export_compound_stateful(self):
        """Control-flow block with export inside is compound_stateful."""
        block = (
            "if [ -f file.txt ]; then\n"
            "    export MY_VAR=1\n"
            "fi"
        )
        tier, units = codelab_parser.classify_block(block)
        self.assertEqual(tier, "compound_stateful")
        self.assertEqual(units, [block])

    def test_control_flow_with_dot_source_compound_stateful(self):
        """Control-flow block with dot-source (. ./env.sh) is compound_stateful."""
        block = (
            "if [ -f env.sh ]; then\n"
            "    . ./env.sh\n"
            "fi"
        )
        tier, units = codelab_parser.classify_block(block)
        self.assertEqual(tier, "compound_stateful")
        self.assertEqual(units, [block])

    def test_control_flow_with_bare_assignment_compound_stateful(self):
        """Control-flow block with bare variable assignment (FOO=bar) is compound_stateful."""
        block = (
            "if [ -f env.sh ]; then\n"
            "    FOO=bar\n"
            "fi"
        )
        tier, units = codelab_parser.classify_block(block)
        self.assertEqual(tier, "compound_stateful")
        self.assertEqual(units, [block])

    def test_flat_block_with_export_remains_flat(self):
        """Flat block with export line is still flat (export is a valid flat unit)."""
        block = (
            "export FOO=bar\n"
            "echo $FOO"
        )
        tier, units = codelab_parser.classify_block(block)
        self.assertEqual(tier, "flat")
        self.assertEqual(units, ["export FOO=bar", "echo $FOO"])

    def test_and_operator_stays_single_unit(self):
        """Logical operators (&&, ||) on same line stay as ONE unit in flat tier."""
        block = "echo 1 && echo 2"
        tier, units = codelab_parser.classify_block(block)
        self.assertEqual(tier, "flat")
        self.assertEqual(units, ["echo 1 && echo 2"])

    def test_semicolon_separated_flat_unit(self):
        """Semicolon-separated statements (a; b) stay as ONE unit in flat tier."""
        block = "echo 1; echo 2"
        tier, units = codelab_parser.classify_block(block)
        self.assertEqual(tier, "flat")
        self.assertEqual(units, ["echo 1; echo 2"])

    def test_trailing_ampersand_compound_pure(self):
        """Trailing & classifies block as compound_pure."""
        block = "sleep 10 &"
        tier, units = codelab_parser.classify_block(block)
        self.assertEqual(tier, "compound_pure")
        self.assertEqual(units, ["sleep 10 &"])


if __name__ == "__main__":
    unittest.main()
