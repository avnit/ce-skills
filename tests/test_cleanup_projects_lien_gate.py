import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

def _load(module_path):
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

cleanup_projects = _load(REPO / ".agents" / "skills" / "codelab-cleanup" / "scripts" / "cleanup_projects.py")

def test_delete_project_aborts_on_lien_denial(monkeypatch):
    recorded_commands = []
    
    def mock_run_command(cmd, capture_output=False, check_return=True):
        recorded_commands.append(cmd)
        if "projects describe" in cmd:
            # Mock return of projectNumber
            return (True, "9876543210\n", "") if capture_output else True
        elif "liens list" in cmd:
            # Assert correct query: must have project target and correct parent filter
            assert "--project=test-project" in cmd
            assert "parent=projects/9876543210" in cmd
            # Return dummy lien
            dummy_lien = "policies/liens/123456789   DoNotDeleteReason"
            return (True, dummy_lien + "\n", "") if capture_output else True
        return (True, "", "") if capture_output else True

    monkeypatch.setattr(cleanup_projects, "run_command", mock_run_command)
    
    # Mock builtins.input to refuse lien deletion (user inputs 'n')
    monkeypatch.setattr("builtins.input", lambda prompt: "n")

    # Run deletion (even with force=True, it should prompt/fail on liens under new rule!)
    result = cleanup_projects.delete_project("test-project", force=True)
    
    assert result is False
    # Verify no delete commands were executed
    assert not any("projects delete" in c for c in recorded_commands)
    assert not any("liens delete" in c for c in recorded_commands)

def test_delete_project_removes_lien_on_approval(monkeypatch):
    recorded_commands = []
    
    def mock_run_command(cmd, capture_output=False, check_return=True):
        recorded_commands.append(cmd)
        if "projects describe" in cmd:
            return (True, "9876543210\n", "") if capture_output else True
        elif "liens list" in cmd:
            assert "--project=test-project" in cmd
            assert "parent=projects/9876543210" in cmd
            dummy_lien = "policies/liens/123456789   DoNotDeleteReason"
            return (True, dummy_lien + "\n", "") if capture_output else True
        elif "liens delete" in cmd:
            assert "123456789" in cmd
            return (True, "", "") if capture_output else True
        elif "projects delete" in cmd:
            assert "test-project" in cmd
            return (True, "", "") if capture_output else True
        return (True, "", "") if capture_output else True

    monkeypatch.setattr(cleanup_projects, "run_command", mock_run_command)
    
    # Mock builtins.input to approve lien deletion (user inputs 'y')
    monkeypatch.setattr("builtins.input", lambda prompt: "y")

    result = cleanup_projects.delete_project("test-project", force=True)
    
    assert result is True
    # Verify delete commands were indeed executed
    assert any("liens delete 123456789" in c for c in recorded_commands)
    assert any("projects delete test-project" in c for c in recorded_commands)
