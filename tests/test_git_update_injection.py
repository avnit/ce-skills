import importlib.util
import subprocess
from pathlib import Path
import pytest
import sys

REPO = Path(__file__).resolve().parents[1]

def _load(module_path):
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

git_update = _load(REPO / ".agents" / "skills" / "git-update" / "scripts" / "git_update.py")

def test_git_update_uses_argv_and_prevents_injection(monkeypatch):
    recorded_runs = []

    def mock_subprocess_run(args, **kwargs):
        recorded_runs.append((args, kwargs))
        class DummyCompletedProcess:
            def __init__(self):
                # Return standard outputs to let flow proceed
                if isinstance(args, list):
                    cmd_str = " ".join(args)
                else:
                    cmd_str = args
                
                if "branch --show-current" in cmd_str:
                    self.stdout = "feature-branch\n"
                elif "status --porcelain" in cmd_str:
                    self.stdout = "M modified_file.py\n"
                elif "merge-base" in cmd_str:
                    self.stdout = "abc123ancestor\n"
                elif "diff --name-only" in cmd_str:
                    self.stdout = "modified_file.py\n"
                else:
                    self.stdout = ""
                self.stderr = ""
                self.returncode = 0
        return DummyCompletedProcess()

    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)
    monkeypatch.setattr(git_update, "ask_permission", lambda prompt: True)
    
    # Hostile inputs with shell injection payload
    hostile_msg = 'pwn"; touch PWNED; #'
    hostile_path = 'some/path'
    
    monkeypatch.setattr(sys, "argv", [
        "git_update.py",
        "-m", hostile_msg,
        "--path", hostile_path,
        "-y"
    ])
    
    try:
        git_update.main()
    except SystemExit:
        pass

    assert len(recorded_runs) > 0
    
    # Verify that shell=False was used on every run and args are lists
    for args, kwargs in recorded_runs:
        assert isinstance(args, list), f"Expected list args, got: {args}"
        assert not kwargs.get("shell", False), f"Expected shell=False, got shell=True for: {args}"

    # Verify that the commit command has exact argv mapping
    commit_calls = [run for run in recorded_runs if "commit" in run[0]]
    assert len(commit_calls) == 1
    commit_args, commit_kwargs = commit_calls[0]
    
    # Verify exact element match without shell escaping/interpolation issues
    assert commit_args == ["git", "commit", "-m", hostile_msg]

    # Verify that git add uses '--' separator to safely handle paths
    add_calls = [run for run in recorded_runs if "add" in run[0]]
    assert len(add_calls) == 1
    add_args, add_kwargs = add_calls[0]
    assert add_args == ["git", "add", "--", hostile_path]
