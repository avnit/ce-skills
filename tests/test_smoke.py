"""Green baseline for CI. Asserts real, currently-true invariants so the unit-test
gate is meaningful from day one. Hermetic: no network, no gcloud/bq, no live GCP.
"""

import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _load(module_path):
    """Load a repo module by file path (scripts aren't an installable package)."""
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_mapped_subagent_prompt_files_exist():
    """Every prompt file referenced by SUBAGENTS_MAP must exist in prompts/."""
    cp = _load(REPO / ".agents" / "scripts" / "compile_prompts.py")
    prompts_dir = REPO / "prompts"
    missing = [
        meta["file"]
        for meta in cp.SUBAGENTS_MAP.values()
        if not (prompts_dir / meta["file"]).exists()
    ]
    assert not missing, f"Mapped prompt files missing from prompts/: {missing}"


def test_compile_prompts_emits_valid_manifest(tmp_path, monkeypatch):
    """compile_prompts.py produces a manifest with every subagent and a non-empty prompt."""
    cp = _load(REPO / ".agents" / "scripts" / "compile_prompts.py")
    out = tmp_path / "compiled_subagents.json"
    monkeypatch.setattr(cp, "OUTPUT_MANIFEST", str(out))

    cp.compile_prompts()

    manifest = json.loads(out.read_text())
    assert set(manifest) == set(cp.SUBAGENTS_MAP), "manifest keys != SUBAGENTS_MAP keys"
    for name, entry in manifest.items():
        assert entry["system_prompt"].strip(), f"empty system prompt compiled for {name}"
