import importlib.util
from pathlib import Path
import os
import json

REPO = Path(__file__).resolve().parents[1]

def _load(module_path):
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

sync_sidecars = _load(REPO / ".agents" / "scripts" / "sync_sidecars.py")
verify_system = _load(REPO / ".agents" / "skills" / "system-validation" / "scripts" / "verify_system.py")

def test_sync_sidecars_resolves_relative_script_and_placeholders(tmp_path, monkeypatch):
    monkeypatch.setattr(sync_sidecars.ce_config, "get", lambda key, *args, **kwargs: "/custom/bugs/dir" if key == "bug_scan_dir" else None)
    
    agents_dir = tmp_path / ".agents"
    agents_dir.mkdir()
    
    # 1. Mock sidecar template 1
    sc1_dir = agents_dir / "closed-loop-listener"
    sc1_dir.mkdir()
    sc1_config = {
        "builtin": "schedule",
        "args": [
            "*/15 * * * *",
            "python3",
            ".agents/skills/closed-loop-learning/scripts/bug_to_lesson_processor.py",
            "--scan-dir",
            "{{bug_scan_dir}}"
        ]
    }
    with open(sc1_dir / "sidecar.json", "w") as f:
        json.dump(sc1_config, f)
        
    # 2. Mock sidecar template 2
    sc2_dir = agents_dir / "codelab-cleanup"
    sc2_dir.mkdir()
    sc2_config = {
        "builtin": "schedule",
        "args": [
            "0 * * * *",
            "python3",
            ".agents/skills/codelab-cleanup/scripts/sweeper.py"
        ]
    }
    with open(sc2_dir / "sidecar.json", "w") as f:
        json.dump(sc2_config, f)
        
    dest_root = tmp_path / "dest"
    dest_root.mkdir()
    
    monkeypatch.setattr(sync_sidecars, "repo_root", str(tmp_path))
    monkeypatch.setattr(os.path, "expanduser", lambda path: str(dest_root) if "sidecars" in path else path)
    
    sync_sidecars.main()
    
    sc1_dest = dest_root / "closed-loop-listener" / "sidecar.json"
    assert sc1_dest.exists()
    with open(sc1_dest, "r") as f:
        sc1_data = json.load(f)
    assert sc1_data["args"][2] == str(tmp_path / ".agents/skills/closed-loop-learning/scripts/bug_to_lesson_processor.py")
    assert sc1_data["args"][4] == "/custom/bugs/dir"
    
    sc2_dest = dest_root / "codelab-cleanup" / "sidecar.json"
    assert sc2_dest.exists()
    with open(sc2_dest, "r") as f:
        sc2_data = json.load(f)
    assert sc2_data["args"][2] == str(tmp_path / ".agents/skills/codelab-cleanup/scripts/sweeper.py")

def test_verify_system_sidecar_validation(tmp_path, monkeypatch):
    agents_dir = tmp_path / ".agents"
    agents_dir.mkdir()
    sc_dir = agents_dir / "my-test-sidecar"
    sc_dir.mkdir()
    with open(sc_dir / "sidecar.json", "w") as f:
        json.dump({"args": ["*", "python3", ".agents/scripts/valid.py"]}, f)
        
    dest_root = tmp_path / "dest"
    dest_root.mkdir()
    
    sc_dest_dir = dest_root / "my-test-sidecar"
    sc_dest_dir.mkdir()
    dest_config = {
        "args": [
            "*",
            "python3",
            "/fake/nonexistent/script.py"
        ]
    }
    with open(sc_dest_dir / "sidecar.json", "w") as f:
        json.dump(dest_config, f)
        
    monkeypatch.setattr(verify_system, "REPO_ROOT", str(tmp_path))
    monkeypatch.setattr(os.path, "expanduser", lambda path: str(dest_root) if "sidecars" in path else path)
    
    # 1. Validation should FAIL due to nonexistent script path
    ok, msg = verify_system.check_sidecar_sync()
    assert ok is False
    assert "script does not exist" in msg
    
    # 2. Validation should FAIL if synced config doesn't exist
    os.remove(sc_dest_dir / "sidecar.json")
    ok, msg = verify_system.check_sidecar_sync()
    assert ok is False
    assert "is not synchronized" in msg
    
    # 3. Validation should PASS when script path exists
    script_file = tmp_path / "valid.py"
    script_file.touch()
    
    valid_dest_config = {
        "args": [
            "*",
            "python3",
            str(script_file)
        ]
    }
    with open(sc_dest_dir / "sidecar.json", "w") as f:
        json.dump(valid_dest_config, f)
        
    ok, msg = verify_system.check_sidecar_sync()
    assert ok is True
    assert "Verified 1 background sidecar" in msg
