import pathlib
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO / ".agents"


class TestNoStaleReferences(unittest.TestCase):
    def test_no_deprecated_script_or_skill_references(self):
        """Assert zero occurrences of deterministic_runner or smith-monitoring in .agents/."""
        forbidden_terms = ["deterministic_runner", "smith-monitoring"]

        hits = []
        for file_path in AGENTS_DIR.rglob("*"):
            if file_path.is_file():
                try:
                    content = file_path.read_text(encoding="utf-8")
                except Exception:
                    continue

                for term in forbidden_terms:
                    if term in content:
                        hits.append(f"{file_path.relative_to(REPO)}: contains '{term}'")

        self.assertEqual(hits, [], "Found stale references in .agents/:\n" + "\n".join(hits))


if __name__ == "__main__":
    unittest.main()
