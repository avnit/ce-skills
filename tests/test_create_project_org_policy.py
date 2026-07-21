import importlib.util
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

def _load(module_path):
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

create_project = _load(REPO / ".agents" / "skills" / "gcp-provisioning" / "scripts" / "create_project.py")


class DummyProcess:
    def __init__(self, returncode=0, stdout_lines=None):
        self.returncode = returncode
        self.stdout = stdout_lines if stdout_lines is not None else ["Disabling Org Policies...\n", "Org Policies disabled successfully.\n"]

    def wait(self):
        return self.returncode


def test_create_project_invokes_disabler_after_billing(monkeypatch):
    """Verifies disable_org_policies.sh is invoked with the new project ID after billing link confirmation."""
    popen_calls = []

    def mock_parse_config(config_path):
        return {"folder_id": "123456789", "billing_account": "000000-111111-222222"}

    def mock_run_command(cmd, dry_run=False, capture_output=False, check_return=True):
        if "billing projects describe" in cmd:
            return (True, "billingEnabled: true\n", "") if capture_output else True
        return (True, "", "") if capture_output else True

    def mock_popen(cmd, **kwargs):
        popen_calls.append(cmd)
        return DummyProcess(returncode=0)

    monkeypatch.setattr(create_project, "parse_config", mock_parse_config)
    monkeypatch.setattr(create_project, "run_command", mock_run_command)
    monkeypatch.setattr("os.path.exists", lambda path: True)
    monkeypatch.setattr("time.sleep", lambda secs: None)
    monkeypatch.setattr("subprocess.Popen", mock_popen)
    monkeypatch.setattr("sys.argv", ["create_project.py", "my-lab", "101"])

    create_project.main()

    disabler_calls = [c for c in popen_calls if "disable_org_policies.sh" in c[1]]
    assert len(disabler_calls) == 1
    assert disabler_calls[0][2] == "my-lab-101"


def test_create_project_skips_disabler_flag(monkeypatch):
    """Verifies disable_org_policies.sh is NOT invoked when --skip-org-policies is passed."""
    popen_calls = []

    def mock_parse_config(config_path):
        return {"folder_id": "123456789", "billing_account": "000000-111111-222222"}

    def mock_run_command(cmd, dry_run=False, capture_output=False, check_return=True):
        if "billing projects describe" in cmd:
            return (True, "billingEnabled: true\n", "") if capture_output else True
        return (True, "", "") if capture_output else True

    def mock_popen(cmd, **kwargs):
        popen_calls.append(cmd)
        return DummyProcess(returncode=0)

    monkeypatch.setattr(create_project, "parse_config", mock_parse_config)
    monkeypatch.setattr(create_project, "run_command", mock_run_command)
    monkeypatch.setattr("os.path.exists", lambda path: True)
    monkeypatch.setattr("time.sleep", lambda secs: None)
    monkeypatch.setattr("subprocess.Popen", mock_popen)
    monkeypatch.setattr("sys.argv", ["create_project.py", "my-lab", "101", "--skip-org-policies"])

    create_project.main()

    disabler_calls = [c for c in popen_calls if "disable_org_policies.sh" in c[1]]
    assert len(disabler_calls) == 0


def test_create_project_disabler_nonzero_warning_path(monkeypatch):
    """Verifies non-zero exit of disabler produces a loud warning with enforced policies and exits 0."""
    def mock_parse_config(config_path):
        return {"folder_id": "123456789", "billing_account": "000000-111111-222222"}

    def mock_run_command(cmd, dry_run=False, capture_output=False, check_return=True):
        if "billing projects describe" in cmd:
            return (True, "billingEnabled: true\n", "") if capture_output else True
        return (True, "", "") if capture_output else True

    def mock_popen(cmd, **kwargs):
        return DummyProcess(returncode=1, stdout_lines=["Error: API service did not become ready\n"])

    monkeypatch.setattr(create_project, "parse_config", mock_parse_config)
    monkeypatch.setattr(create_project, "run_command", mock_run_command)
    monkeypatch.setattr("os.path.exists", lambda path: True)
    monkeypatch.setattr("time.sleep", lambda secs: None)
    monkeypatch.setattr("subprocess.Popen", mock_popen)
    monkeypatch.setattr("sys.argv", ["create_project.py", "my-lab", "101"])

    captured_output = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured_output)

    # Should exit 0 without raising SystemExit exception
    create_project.main()

    out = captured_output.getvalue()
    assert "WARNING: Org-policy disabler failed (exit code 1)." in out
    assert "Project my-lab-101 is usable, but the following org policies remain enforced:" in out
    assert "compute.requireShieldedVm" in out
    assert "iam.disableServiceAccountKeyCreation" in out
    assert "compute.vmExternalIpAccess" in out
    assert "SUCCESS: Project my-lab-101 setup complete." in out
