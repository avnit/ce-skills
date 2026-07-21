import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _load(module_path):
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tester = _load(REPO / ".agents" / "skills" / "codelab-validation" / "scripts" / "tester.py")


def test_narrative_between_blocks_not_captured():
    """#77: a non-bash output block + narrative between two bash blocks must not leak
    into commands, and BOTH real commands must be extracted. (The old findall regex
    captured 'Now continue with setup.' as a command and dropped 'gcloud auth list'.)"""
    body = (
        "Run the command:\n"
        "```bash\n"
        "gcloud config list\n"
        "```\n"
        "Expected output:\n"
        "```text\n"
        "project = my-proj (name)\n"
        "```\n"
        "Now continue with setup.\n"
        "```bash\n"
        "gcloud auth list\n"
        "```\n"
    )
    cmds = tester._extract_command_blocks(body)
    assert cmds == ["gcloud config list", "gcloud auth list"]
    joined = "\n".join(cmds)
    assert "Now continue" not in joined          # narrative never captured
    assert "project = my-proj" not in joined      # sample output never captured


def test_crlf_and_bare_fences_still_extract():
    """CRLF endings and bare fences still work (no #22/#41 regression)."""
    body = "## S\r\n```bash\r\necho crlf\r\n```\r\n## T\r\n```\r\necho bare\r\n```\r\n"
    assert tester._extract_command_blocks(body) == ["echo crlf", "echo bare"]


def test_non_executable_and_prose_yield_no_commands():
    """A lab with only a non-executable block or only prose yields zero commands —
    which feeds the #22 loud-fail, never a vacuous pass."""
    assert tester._extract_command_blocks("Just prose, no fences at all.\n") == []
    assert tester._extract_command_blocks("```yaml\nkey: value\n```\n") == []
    assert tester._extract_command_blocks("```text\nsome output (paren)\n```\n") == []
    assert tester._extract_command_blocks("```console\nNAME STATE\nfoo ACTIVE\n```\n") == []
