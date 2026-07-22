import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

def test_no_author_hardcoding():
    """Asserts no occurrences of 'shacharb' or 'skynet' in content files."""
    targets = [
        REPO / ".agents",
        REPO / "prompts",
        REPO / "scripts",
        REPO / "README.md",
        REPO / "ce-scale",
    ]

    hits = []
    pattern = re.compile(r"(shacharb|skynet)", re.IGNORECASE)

    for target in targets:
        if not target.exists():
            continue
        if target.is_file():
            files = [target]
        else:
            files = [f for f in target.rglob("*") if f.is_file() and not f.name.endswith(".pyc")]

        for filepath in files:
            if "state" in filepath.parts or "mailboxes" in filepath.parts:
                continue
            # Skip binary files or non-text files by trying UTF-8 read
            try:
                content = filepath.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue

            for line_num, line in enumerate(content.splitlines(), start=1):
                if pattern.search(line):
                    rel_path = filepath.relative_to(REPO)
                    hits.append(f"{rel_path}:{line_num}: {line.strip()}")

    assert not hits, "Found author-specific hardcoding:\n" + "\n".join(hits)
