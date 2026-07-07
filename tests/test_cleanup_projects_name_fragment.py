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

cleanup_projects = _load(REPO / ".agents" / "skills" / "codelab-cleanup" / "scripts" / "cleanup_projects.py")

def test_delete_all_parses_real_project_id_not_fragment(monkeypatch):
    simulated_list_stdout = (
        "NAME                PROJECT_ID     PROJECT_NUMBER  CREATE_TIME  STATE\n"
        "My First Project    my-proj-123    123456789012    2026-07-01   ACTIVE\n"
        "Simple-Project      simple-proj-1  234567890123    2026-07-01   ACTIVE\n"
    )

    deleted_pids = []

    def mock_run_command(cmd, capture_output=False, check_return=True):
        if "projects list" in cmd:
            if "value(projectId)" in cmd:
                # If the code retrieves list of IDs safely using value(projectId):
                return (True, "my-proj-123\nsimple-proj-1\n", "") if capture_output else True
            return (True, simulated_list_stdout, "") if capture_output else True
        elif "projects delete" in cmd:
            parts = cmd.split()
            pid = parts[3]
            deleted_pids.append(pid)
            return (True, "", "") if capture_output else True
        elif "projects describe" in cmd:
            return (True, "9876543210\n", "") if capture_output else True
        return (True, "", "") if capture_output else True

    monkeypatch.setattr(cleanup_projects, "run_command", mock_run_command)
    
    class MockCompletedProcess:
        def __init__(self):
            self.stdout = ""
            self.stderr = ""
            self.returncode = 0
            
    def mock_subprocess_run(args, **kwargs):
        return MockCompletedProcess()
        
    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)
    monkeypatch.setattr(cleanup_projects, "get_config", lambda: {"folder_id": "129578293542"})
    monkeypatch.setattr("sys.argv", ["cleanup_projects.py", "--delete-all", "--force"])

    cleanup_projects.main()

    assert "my-proj-123" in deleted_pids
    assert "simple-proj-1" in deleted_pids
    assert "First" not in deleted_pids
