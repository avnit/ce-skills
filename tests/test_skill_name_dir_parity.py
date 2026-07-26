import pathlib
import re
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO / ".agents" / "skills"

# Allowlist for directories under .agents/skills/ that do not contain a SKILL.md.
MANIFESTLESS_DIRS_ALLOWLIST = {
    "reports",  # Subdirectory housing skill review reports
}

OLD_UNDERSCORE_SKILL_NAMES = [
    "workspace_agency_csa",
    "codelab_audit_logging",
    "customer_architecture_researcher",
    "customer_gap_analysis",
    "customer_meeting_prep",
    "creating_gcp_diagrams",
    "extracting_requirements_from_meetings",
    "agent_waf_system",
]


class TestSkillNameDirParity(unittest.TestCase):
    def test_skill_name_matches_directory_name(self):
        """Assert every directory under .agents/skills/ with a SKILL.md has name: matching directory name."""
        self.assertTrue(SKILLS_DIR.is_dir(), f"Skills directory not found: {SKILLS_DIR}")

        dir_names = set()
        for item in SKILLS_DIR.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                dir_names.add(item.name)

        for dir_name in sorted(dir_names):
            skill_dir = SKILLS_DIR / dir_name
            skill_md = skill_dir / "SKILL.md"

            if not skill_md.exists():
                self.assertIn(
                    dir_name,
                    MANIFESTLESS_DIRS_ALLOWLIST,
                    f"Directory '{dir_name}' lacks a SKILL.md manifest and is not in MANIFESTLESS_DIRS_ALLOWLIST (#131).",
                )
                continue

            content = skill_md.read_text(encoding="utf-8")
            # Parse frontmatter name field: name: <name>
            match = re.search(r"^name:\s*([^\s#]+)", content, re.MULTILINE)
            self.assertIsNotNone(
                match, f"Could not find 'name:' frontmatter in {skill_md.relative_to(REPO)}"
            )

            frontmatter_name = match.group(1).strip()
            self.assertEqual(
                frontmatter_name,
                dir_name,
                f"Frontmatter name '{frontmatter_name}' does not match directory name '{dir_name}' in {skill_md.relative_to(REPO)}",
            )

    def test_no_deprecated_underscore_skill_name_references(self):
        """Assert zero occurrences of the 7 old underscore skill names across .agents/ and repo root."""
        search_dirs = [REPO / ".agents", REPO / "doc", REPO / "references"]
        search_files = [REPO / "README.md"]

        hits = []
        for search_target in search_dirs:
            if not search_target.exists():
                continue
            for file_path in search_target.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith("."):
                    self._check_file_for_old_names(file_path, hits)

        for file_path in search_files:
            if file_path.exists():
                self._check_file_for_old_names(file_path, hits)

        self.assertEqual(
            hits,
            [],
            "Found references to deprecated underscore skill names:\n" + "\n".join(hits),
        )

    def _check_file_for_old_names(self, file_path, hits):
        if file_path.name == "skills_audit.json":
            return

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return

        # Ignore backend blaze build-target identifier //agent_waf_system:mcp_server in orchestrator.py
        content_to_check = content.replace("//agent_waf_system:mcp_server", "")

        for old_name in OLD_UNDERSCORE_SKILL_NAMES:
            if old_name in content_to_check:
                rel_path = file_path.relative_to(REPO)
                hits.append(f"{rel_path}: contains deprecated name '{old_name}'")


if __name__ == "__main__":
    unittest.main()
