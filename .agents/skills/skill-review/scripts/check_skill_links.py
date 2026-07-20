"""Script to validate all file references and markdown links inside an agent skill directory."""

import argparse
import os
import re
import sys
from typing import Any, List, Tuple

# pylint: disable=g-import-not-at-top
try:
  from absl import app as absl_app
  from absl import flags as absl_flags

  FLAGS: Any = absl_flags.FLAGS
  absl_flags.DEFINE_string(
      "skill_path",
      "",
      "Absolute path to the target SKILL.md file or skill root directory.",
  )
  _HAS_ABSL = True
except ImportError:
  _HAS_ABSL = False
  absl_app: Any = None

  class _MockFlags:
    skill_path = ""

  FLAGS: Any = _MockFlags()
# pylint: enable=g-import-not-at-top

# Regex to match markdown links: [text](target_url_or_path)
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)\s]+)[^)]*\)")

# Constants & static scan patterns (absorbed from comprehensive static linter standards)
MAX_DESC_CHARS = 1024
MAX_SKILL_MD_LINES_BEST = 200
MAX_SKILL_MD_LINES_LIMIT = 500
REF_TOC_LINE_THRESHOLD = 100

FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
SECRET_PATTERN = re.compile(
    r"(?:AIza[0-9A-Za-z-_]{35}|BEGIN (?:RSA|OPENSSH) PRIVATE"
    r" KEY|ghp_[a-zA-Z0-9]{36})"
)
DESTRUCTIVE_PATTERN = re.compile(
    r"(?:rm\s+-rf\s+/|curl\s+.*\|\s*bash|chmod\s+777)"
)
FIRST_SECOND_PERSON = re.compile(
    r"\b(i\s+can\s+help|you\s+can\s+use|this\s+helps\s+you)\b", re.IGNORECASE
)


def find_files_to_check(skill_root: str) -> List[str]:
  """Recursively finds all markdown (.md) and textproto/yaml files in skill root."""
  files_to_check = []
  for root, _, files in os.walk(skill_root):
    for filename in files:
      if filename.endswith((".md", ".txtpb", ".yaml", ".tf")):
        files_to_check.append(os.path.join(root, filename))
  return files_to_check


def is_google3_env(path: str) -> bool:
  """Detects whether the target skill resides in a Google3 Piper/CitC workspace vs.

  GitHub/OSS.
  """
  return (
      "google3/" in path
      or "/google/src/" in path
      or os.path.exists("/google/src/files")
  )


def check_link(
    source_file: str, link_text: str, link_target: str, skill_root: str
) -> Tuple[bool, str]:
  """Checks if a single link target is valid (handling both Google3 and GitHub/OSS modes)."""
  g3_mode = is_google3_env(source_file)

  # Rule 1 (Google3 mode only): Check for ephemeral cloud workspace references
  if g3_mode and (
      link_target.startswith("file://") or "/google/src/cloud/" in link_target
  ):
    return (
        False,
        (
            f"[EPHEMERAL PATH VIOLATION] Link '{link_text}' -> '{link_target}'"
            f" in {source_file} uses an ephemeral user workspace or file://"
            " URI. In Google3, use canonical google3/... paths."
        ),
    )

  # Rule 2: Ignore external HTTP/HTTPS web links (and go/ shortlinks in Google3)
  if link_target.startswith(("http://", "https://", "mailto:", "#")) or (
      g3_mode and link_target.startswith("go/")
  ):
    return (True, "")

  # Strip line anchors (#L10-L20) or query params from local paths
  clean_target = link_target.split("#")[0].split("?")[0]
  if not clean_target:
    return (True, "")

  # Rule 3: Resolve local file path
  if g3_mode and clean_target.startswith("google3/"):
    # Canonical google3 workspace reference
    workspace_idx = source_file.find("google3/")
    if workspace_idx != -1:
      workspace_root = source_file[:workspace_idx]
      resolved_path = os.path.join(workspace_root, clean_target)
    else:
      resolved_path = f"/{clean_target}"
  elif g3_mode and clean_target.startswith("//depot/google3/"):
    # Piper depot path -> map to google3 local
    workspace_idx = source_file.find("google3/")
    if workspace_idx != -1:
      workspace_root = source_file[:workspace_idx]
      rel_path = clean_target[len("//depot/") :]
      resolved_path = os.path.join(workspace_root, rel_path)
    else:
      return (True, "")  # Snapshot path, skip local filesystem verification
  elif clean_target.startswith("/"):
    resolved_path = clean_target
  else:
    # Relative path from the directory containing source_file (e.g. references/foo.md or ./assets/bar.tf)
    resolved_path = os.path.join(os.path.dirname(source_file), clean_target)

  if os.path.exists(resolved_path):
    return (True, "")
  else:
    rel_source = os.path.relpath(source_file, skill_root)
    env_label = "Google3" if g3_mode else "GitHub/OSS"
    return (
        False,
        (
            f"[{env_label} BROKEN LINK] In {rel_source}: link '{link_text}' ->"
            f" '{link_target}' points to missing file '{resolved_path}'."
        ),
    )


def check_frontmatter(skill_root: str) -> List[str]:
  """Checks SKILL.md frontmatter parsing, description length, and persona hygiene."""
  errs = []
  skill_md = os.path.join(skill_root, "SKILL.md")
  if not os.path.exists(skill_md):
    return ["P0 Blocker: SKILL.md missing in root directory."]

  try:
    with open(skill_md, "r", encoding="utf-8") as f:
      content = f.read()
  except Exception as e:
    return [f"P0 Blocker: Cannot read SKILL.md: {e}"]

  fm_match = FRONTMATTER_PATTERN.search(content)
  if not fm_match:
    errs.append(
        "[FM01] P0 Blocker: SKILL.md missing or unparseable YAML frontmatter"
        " block."
    )
    return errs

  fm_text = fm_match.group(1)
  desc_match = re.search(
      r"^description:\s*(?:>-\s*\n)?(.*?)(\n\w+:|\Z)",
      fm_text,
      re.MULTILINE | re.DOTALL,
  )
  if not desc_match:
    errs.append("[FM03] P0 Blocker: Frontmatter missing 'description' field.")
  else:
    desc = desc_match.group(1).strip()
    if len(desc) > MAX_DESC_CHARS:
      errs.append(
          f"[FM04] P0 Blocker: Description length ({len(desc)} chars) exceeds"
          f" {MAX_DESC_CHARS} max limit."
      )
    if FIRST_SECOND_PERSON.search(desc):
      errs.append(
          "[FM10] P1 High Impact: Description uses first/second person prose"
          " (e.g., 'I can help'). Use third-person imperative."
      )

  name_match = re.search(r"^name:\s*([^\s]+)", fm_text, re.MULTILINE)
  if not name_match:
    errs.append("[FM05] P0 Blocker: Frontmatter missing 'name' field.")
  return errs


def check_file_hygiene(
    filepath: str, content: str, skill_root: str
) -> List[str]:
  """Checks size boundaries, Table of Contents rules, static safety, and deep chaining."""
  errs = []
  rel_path = os.path.relpath(filepath, skill_root)
  lines = content.splitlines()
  num_lines = len(lines)

  # Size & Progressive Disclosure checks
  if rel_path == "SKILL.md":
    if num_lines > MAX_SKILL_MD_LINES_LIMIT:
      errs.append(
          f"[SZ01] P0 Context Bomb: SKILL.md ({num_lines} lines) exceeds"
          f" {MAX_SKILL_MD_LINES_LIMIT} maximum line limit."
      )
    elif num_lines > MAX_SKILL_MD_LINES_BEST:
      errs.append(
          f"[SZ02] P1 High Impact: SKILL.md ({num_lines} lines) exceeds"
          f" {MAX_SKILL_MD_LINES_BEST}-line progressive disclosure benchmark."
      )
  elif rel_path.startswith("references/") and rel_path.endswith(".md"):
    if num_lines >= REF_TOC_LINE_THRESHOLD and not re.search(
        r"^#{1,3}\s+(?:Table\s+of\s+)?Contents",
        content,
        re.MULTILINE | re.IGNORECASE,
    ):
      errs.append(
          f"[SZ05] P1 High Impact: Long reference file {rel_path} ({num_lines}"
          " lines) lacks a Markdown Table of Contents header."
      )

    # Deep chaining check inside reference files
    for match in LINK_PATTERN.finditer(content):
      _, link_target = match.groups()
      if link_target.startswith(("references/", "./references/")) or (
          "/" not in link_target and link_target.endswith(".md")
      ):
        errs.append(
            f"[ST02] P1 Deep Chaining: Reference {rel_path} deep-links to"
            f" another reference ({link_target}). Keep all reference links"
            " exactly 1 level deep from SKILL.md."
        )

  # Security & destructive command checks (skip if skill-lint-allow or pragma is present)
  if "skill-lint-allow" not in content and SECRET_PATTERN.search(content):
    errs.append(
        f"[LN04] P0 Security Blocker: {rel_path} contains potential hardcoded"
        " API keys or private certificates."
    )
  if "skill-lint-allow" not in content and DESTRUCTIVE_PATTERN.search(content):
    errs.append(
        f"[LN06] P0 Security Blocker: {rel_path} contains unguarded destructive"
        " shell commands (e.g., rm -rf / or curl | bash)."
    )

  return errs


def main(argv: List[str]) -> None:
  if len(argv) > 1 and not FLAGS.skill_path:
    FLAGS.skill_path = argv[1]

  if not FLAGS.skill_path:
    print("Error: --skill_path argument is required.")
    sys.exit(1)

  target_path = os.path.abspath(FLAGS.skill_path)
  if os.path.isfile(target_path):
    skill_root = os.path.dirname(target_path)
  elif os.path.isdir(target_path):
    skill_root = target_path
  else:
    print(f"Error: Target path '{target_path}' does not exist.")
    sys.exit(1)

  files_to_check = find_files_to_check(skill_root)
  total_links = 0
  errors: List[str] = check_frontmatter(skill_root)

  for filepath in files_to_check:
    try:
      with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    except Exception as e:
      errors.append(f"[READ ERROR] Could not read {filepath}: {e}")
      continue

    errors.extend(check_file_hygiene(filepath, content, skill_root))

    for match in LINK_PATTERN.finditer(content):
      total_links += 1
      link_text, link_target = match.groups()
      is_valid, err_msg = check_link(
          filepath, link_text, link_target.strip(), skill_root
      )
      if not is_valid:
        errors.append(err_msg)

  print(
      f"\n=== Skill Verification & Static Audit Report for '{skill_root}' ==="
  )
  print(
      f"Scanned {len(files_to_check)} files | Checked {total_links} links |"
      " Verified frontmatter & size boundaries."
  )

  if errors:
    print(f"\n❌ FOUND {len(errors)} STATIC VERIFICATION / PATH VIOLATIONS:")
    for err in errors:
      print(f"  * {err}")
    sys.exit(1)
  else:
    print(
        "\n✅ ALL CHECKS PASSED: Zero broken links, ephemeral paths, secrets,"
        " or size/frontmatter violations."
    )
    sys.exit(0)


if __name__ == "__main__":
  if _HAS_ABSL and absl_app is not None:
    absl_app.run(main)
  else:
    parser = argparse.ArgumentParser(
        description=(
            "Validate all file references and markdown links in a skill path."
        )
    )
    parser.add_argument(
        "--skill_path",
        default="",
        help=(
            "Absolute path to the target SKILL.md file or skill root directory."
        ),
    )
    args, unknown = parser.parse_known_args()
    if args.skill_path:
      FLAGS.skill_path = args.skill_path
    main(sys.argv)
