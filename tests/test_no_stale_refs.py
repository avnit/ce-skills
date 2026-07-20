import pathlib
import re
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO / ".agents"


class TestNoStaleReferences(unittest.TestCase):
    def test_no_deprecated_script_or_skill_references(self):
        """Assert zero occurrences of deprecated scripts or root-pointing file:/// URIs in .agents/, prompts/, or README.md."""
        forbidden_terms = ["deterministic_runner", "smith-monitoring"]
        # Root-pointing file:/// URIs (e.g. file:///.agents/..., file:///prompts/...) fail to resolve workspace-relative paths.
        # Placeholder templates intended for runtime expansion (e.g. file:///<appDataDir>..., file:///{workspace_dir}...) are allowed.
        root_file_uri_pattern = re.compile(r"file:///(\.agents|prompts|references|labs|doc)/")

        targets = [REPO / ".agents", REPO / "prompts", REPO / "README.md"]

        hits = []
        for target in targets:
            if not target.exists():
                continue
            if target.is_file():
                files = [target]
            else:
                files = [f for f in target.rglob("*") if f.is_file()]

            for file_path in files:
                if any(part in file_path.parts for part in ("state", "mailboxes", "reports")):
                    continue
                try:
                    content = file_path.read_text(encoding="utf-8")
                except Exception:
                    continue

                for term in forbidden_terms:
                    if term in content:
                        hits.append(f"{file_path.relative_to(REPO)}: contains '{term}'")

                match = root_file_uri_pattern.search(content)
                if match:
                    hits.append(f"{file_path.relative_to(REPO)}: contains root-pointing URI '{match.group(0)}'")

        self.assertEqual(hits, [], "Found stale/forbidden references:\n" + "\n".join(hits))


if __name__ == "__main__":
    unittest.main()
