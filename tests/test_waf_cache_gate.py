import importlib.util
from pathlib import Path
import pytest
import os
import json

REPO = Path(__file__).resolve().parents[1]

def _load(module_path):
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

orchestrator = _load(REPO / ".agents" / "skills" / "agent_waf_system" / "orchestrator.py")

def test_missing_template_does_not_wipe_cache(tmp_path, monkeypatch):
    temp_cache_file = tmp_path / "test_session_cache.json"
    
    dummy_state = {
        "customer_name": "Test Customer",
        "industry_vertical": "FinTech",
        "area_of_tech": "NETWORKING",
        "deployment_size": "ENTERPRISE_SCALE",
        "customer_priority": "SECURITY",
        "completed_questions": {
            "TOPOLOGY": {
                "selected_option_id": "HUB_AND_SPOKE",
                "selected_option_text": "Hub and spoke topology",
                "rules": ["rule1"],
                "cons": "cons1",
                "justification": "Test justification",
                "is_override": False,
                "warning_triggered": False,
                "warning_text": ""
            }
        }
    }
    temp_cache_file.write_text(json.dumps(dummy_state, indent=2))
    
    class MockMcp:
        def __init__(self, *args, **kwargs):
            pass
            
    monkeypatch.setattr(orchestrator, "StdioWafMcpClient", MockMcp)
    
    orc = orchestrator.WafClientOrchestrator()
    orc.session_state = dummy_state
    
    monkeypatch.setattr(orchestrator, "CACHE_FILE", str(temp_cache_file))
    
    def mock_critique(*args, **kwargs):
        return True, "Mock CISO review passed."
    monkeypatch.setattr(orc, "critique_security_agent", mock_critique)
    
    real_exists = os.path.exists
    def mock_exists(path):
        if "ADR_TEMPLATE.md" in path:
            return False
        return real_exists(path)
    monkeypatch.setattr(os.path, "exists", mock_exists)
    
    orc.run_security_agent_governance_loop()
    
    assert temp_cache_file.exists()
    
    with open(temp_cache_file, "r") as f:
        saved_data = json.load(f)
    assert saved_data["customer_name"] == "Test Customer"
