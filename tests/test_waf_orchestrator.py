import importlib.util
import os
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

def _load(module_path):
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

orchestrator = _load(REPO / ".agents" / "skills" / "agent-waf-system" / "orchestrator.py")

def test_unconfigured_cwd_raises_value_error(monkeypatch):
    """Verifies that if waf_mcp_cwd is missing/None and use_mock is False, ValueError is raised."""
    # Mock ce_config.get on the imported orchestrator's module namespace
    monkeypatch.setattr(orchestrator.ce_config, "get", lambda key, *args, **kwargs: None)
    
    with pytest.raises(ValueError) as excinfo:
        orchestrator.StdioWafMcpClient(use_mock=False)
    assert "WAF MCP working directory (waf_mcp_cwd) is not configured" in str(excinfo.value)

def test_configured_cwd_is_used(monkeypatch):
    """Verifies that the configured waf_mcp_cwd value is correctly mapped to the client's cwd property."""
    monkeypatch.setattr(orchestrator.ce_config, "get", lambda key, *args, **kwargs: "/custom/waf/path" if key == "waf_mcp_cwd" else None)
    
    client = orchestrator.StdioWafMcpClient(use_mock=False)
    assert client.cwd == "/custom/waf/path"

def test_unreachable_blaze_fails_loudly(monkeypatch):
    """Verifies that if use_mock is False and Blaze launch fails, get_questionnaire_tree raises RuntimeError."""
    monkeypatch.setattr(orchestrator.ce_config, "get", lambda key, *args, **kwargs: "/custom/waf/path" if key == "waf_mcp_cwd" else None)
    
    # Mock subprocess.Popen to fail
    def mock_popen(*args, **kwargs):
        raise FileNotFoundError("[Mock] blaze command not found")
    monkeypatch.setattr(subprocess, "Popen", mock_popen)
    
    client = orchestrator.StdioWafMcpClient(use_mock=False)
    
    with pytest.raises(RuntimeError) as excinfo:
        client.get_questionnaire_tree("NETWORKING", "ENTERPRISE_SCALE", "SECURITY")
    assert "Fatal: WAF MCP stdio server connection failure" in str(excinfo.value)

def test_mock_mode_opt_in_runs_fallback_and_adds_stamp(tmp_path, monkeypatch):
    """Verifies that WafClientOrchestrator in mock mode runs fallback and stamps ADR output."""
    # When mock mode is active, no cwd is required
    monkeypatch.setattr(orchestrator.ce_config, "get", lambda key, *args, **kwargs: None)
    
    orc = orchestrator.WafClientOrchestrator(use_mock=True)
    
    # Check that questionnaire tree resolves mock data successfully without throwing
    tree = orc.mcp.get_questionnaire_tree("NETWORKING", "ENTERPRISE_SCALE", "SECURITY")
    assert tree["area_of_tech"] == "NETWORKING"
    assert len(tree["decision_groups"]) > 0
    
    # Verify that ADR template generation prepends mock warning stamp
    temp_template = tmp_path / "ADR_TEMPLATE.md"
    temp_template.write_text("# ADR Report for {{customer_name}}")
    monkeypatch.setattr(orchestrator, "_script_dir", str(tmp_path))
    
    # Setup dummy session state
    dummy_state = {
        "customer_name": "Mock Test Customer",
        "industry_vertical": "FinTech",
        "area_of_tech": "NETWORKING",
        "deployment_size": "ENTERPRISE_SCALE",
        "customer_priority": "SECURITY",
        "completed_questions": {
            "TOPOLOGY": {
                "selected_option_id": "HUB_AND_SPOKE",
                "selected_option_text": "Hub and Spoke Architecture",
                "rules": ["WAF-NET-01"],
                "cons": "Cost",
                "justification": "Test justification",
                "is_override": False,
                "warning_triggered": False,
                "warning_text": ""
            }
        }
    }
    orc.session_state = dummy_state
    
    # Mock exists check to point to our temp template file
    real_exists = os.path.exists
    def mock_exists(path):
        if "ADR_TEMPLATE.md" in path:
            return True
        return real_exists(path)
    monkeypatch.setattr(os.path, "exists", mock_exists)
    
    # Mock template file open to use temp_template
    real_open = open
    def mock_open(file, mode="r", *args, **kwargs):
        if "ADR_TEMPLATE.md" in str(file):
            return real_open(temp_template, mode, *args, **kwargs)
        return real_open(file, mode, *args, **kwargs)
    monkeypatch.setattr("builtins.open", mock_open)
    
    # Execute adr generation
    res = orc.generate_final_adr(ciso_approved=True, ciso_report="Passed")
    assert res
    
    # Resolve expected file path: reports/customer/mock_test_customer/adr/WAF_ADR.md relative to mocked _script_dir
    repo_root = Path(os.path.abspath(os.path.join(str(tmp_path), "..", "..", "..")))
    expected_adr_path = repo_root / "reports" / "customer" / "mock_test_customer" / "adr" / "WAF_ADR.md"
    
    assert expected_adr_path.exists()
    try:
        adr_content = expected_adr_path.read_text()
        assert adr_content.startswith("⚠️ MOCK DATA — NOT A VERIFIED WAF REVIEW")
    finally:
        # Clean up generated file
        if expected_adr_path.exists():
            os.remove(expected_adr_path)
            try:
                os.rmdir(expected_adr_path.parent)
                os.rmdir(expected_adr_path.parents[1])
                os.rmdir(expected_adr_path.parents[2])
            except OSError:
                pass
