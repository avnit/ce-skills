import pathlib
import re
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO / ".agents"

# Regex matching Markdown links: [text](target)
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
PLACEHOLDER_CHARS = set("<>{}[]$")

# TODO(#165): Allowlist for illustrative markdown template/example placeholder links that serve as documentation snippets.
TEMPLATE_PLACEHOLDER_ALLOWLIST = {
    "URL",
    "url",
    "absolute_path_to_image",
    "design_blueprint.md",
    "assets/design_diagram.png",
    "assets/data_pipeline.png",
    "assets/architecture_diagram.png",
    "img/cloud-shell-icon.png",
    "img/screenshot.png",
    "../../labs/dev/customer-a-storage/customer-a-storage.lab.md",
}


class TestMarkdownLinksResolve(unittest.TestCase):
    def test_markdown_links_resolve(self):
        """Extract relative markdown links across .agents/**/*.md and assert target existence."""
        hits = []

        for file_path in AGENTS_DIR.rglob("*.md"):
            if any(part in file_path.parts for part in ("state", "mailboxes", "reports")):
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception:
                continue

            file_dir = file_path.parent

            for match in LINK_PATTERN.finditer(content):
                link_text, link_target = match.groups()
                target_clean = link_target.strip()

                # Skip absolute URLs, mailto, and pure anchor links
                if target_clean.startswith(("http://", "https://", "mailto:", "#")):
                    continue

                # Skip links containing template placeholders (< >, { }, [ ], $)
                if any(c in target_clean for c in PLACEHOLDER_CHARS):
                    continue

                # Skip known illustrative template placeholders (TODO #165)
                if target_clean in TEMPLATE_PLACEHOLDER_ALLOWLIST:
                    continue

                # Strip anchor fragment (e.g., #L10 or #section)
                file_target_str = target_clean.split("#")[0]
                if not file_target_str:
                    continue

                # Check resolution against containing directory OR repo root
                rel_to_dir = (file_dir / file_target_str).resolve()
                rel_to_repo = (REPO / file_target_str.lstrip("/")).resolve()

                if not (rel_to_dir.exists() or rel_to_repo.exists()):
                    hits.append(
                        f"{file_path.relative_to(REPO)}: broken relative link [{link_text}]({link_target})"
                    )

        self.assertEqual(
            hits,
            [],
            "Found unresolvable relative markdown links under .agents/:\n" + "\n".join(hits),
        )


if __name__ == "__main__":
    unittest.main()
