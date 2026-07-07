import importlib.util
import subprocess
from pathlib import Path
import pytest

REPO = Path(__file__).resolve().parents[1]

def _load(module_path):
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

create_project = _load(REPO / ".agents" / "skills" / "gcp-provisioning" / "scripts" / "create_project.py")
cleanup_projects = _load(REPO / ".agents" / "skills" / "codelab-cleanup" / "scripts" / "cleanup_projects.py")

def test_create_project_run_command_failure_precedence(monkeypatch):
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=args[0],
            output="mocked stdout",
            stderr="mocked stderr"
        )
    monkeypatch.setattr(subprocess, "run", mock_run)

    res_false = create_project.run_command("dummy cmd", dry_run=False, capture_output=False)
    assert res_false is False

    res_true = create_project.run_command("dummy cmd", dry_run=False, capture_output=True)
    assert isinstance(res_true, tuple)
    assert res_true[0] is False
    assert res_true[1] == "mocked stdout"
    assert res_true[2] == "mocked stderr"

def test_cleanup_projects_run_command_failure_precedence(monkeypatch):
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=args[0],
            output="mocked stdout",
            stderr="mocked stderr"
        )
    monkeypatch.setattr(subprocess, "run", mock_run)

    res_false = cleanup_projects.run_command("dummy cmd", capture_output=False)
    assert res_false is False

    res_true = cleanup_projects.run_command("dummy cmd", capture_output=True)
    assert isinstance(res_true, tuple)
    assert res_true[0] is False
    assert res_true[1] == "mocked stdout"
    assert res_true[2] == "mocked stderr"
