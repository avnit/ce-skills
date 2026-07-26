import getpass
import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Mock vertexai before executing imports
sys.modules["vertexai"] = MagicMock()
sys.modules["vertexai.preview.rag"] = MagicMock()

REPO = Path(__file__).resolve().parents[1]

def _load(module_path):
    name = module_path.stem
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def test_closed_loop_learning_no_shacharb_fallbacks(monkeypatch):
    """Verifies closed-loop learning scripts use env overrides for account resolution."""
    publisher = _load(REPO / ".agents" / "skills" / "closed-loop-learning" / "scripts" / "mcp_publisher.py")

    monkeypatch.delenv("CLOSED_LOOP_ACCOUNT", raising=False)
    monkeypatch.delenv("CE_CLOSED_LOOP_ACCOUNT", raising=False)

    monkeypatch.setenv("CLOSED_LOOP_ACCOUNT", "test-user@google.com")
    assert publisher.resolve_submitted_by() == "test-user@google.com"

def test_pricing_estimator_configurable_table_and_tempfile(monkeypatch):
    """Verifies pricing estimator uses env/tempfile and does not fallback to shacharb."""
    billing_client = _load(REPO / ".agents" / "skills" / "codelab-pricing-estimator" / "scripts" / "billing_client.py")
    cache = _load(REPO / ".agents" / "skills" / "codelab-pricing-estimator" / "scripts" / "cache.py")

    # Verify BQ pricing table falls back gracefully to static catalog rates when CE_PRICING_TABLE is unset
    monkeypatch.delenv("CE_PRICING_TABLE", raising=False)
    bq_val = billing_client.fetch_price_from_bq("Compute Engine", "E2 Instance", "us-central1")
    assert bq_val == 0.0
    
    # Assert that it successfully retrieves a static rate fallback for e2-medium
    static_val = billing_client.get_compute_price("e2-medium", "us-central1")
    assert static_val > 0.0
    assert static_val == 0.0335  # static fallback rate defined in billing_client.py

    # Verify CatalogCache falls back to tempdir when env is missing instead of /usr/local/google/home/shacharb
    monkeypatch.delenv("ANTIGRAVITY_EXECUTABLE_DATA_DIR", raising=False)
    
    # Mocking os.path.exists to return False for standard paths
    real_exists = os.path.exists
    def mock_exists(path):
        if "sidecar_data" in path or "sku_cache" in path:
            return False
        return real_exists(path)
    monkeypatch.setattr(os.path, "exists", mock_exists)

    cc = cache.CatalogCache()
    # Check that it uses the user's temp directory
    assert tempfile.gettempdir() in cc.cache_dir
    assert "shacharb" not in cc.cache_dir

def test_onboarding_no_author_argparse_defaults(monkeypatch):
    """Verifies onboarding onboard.py doesn't contain hardcoded argparse defaults."""
    # Point ce_config to a nonexistent temp file to prevent loading real workspace credentials
    monkeypatch.setenv("CE_CONFIG_PATH", "/nonexistent/gcp_config.txt")
    import ce_config
    ce_config._cached_config = None
    
    # Force reload of onboard.py after resetting ce_config so its parser evaluates clean defaults
    if "onboard" in sys.modules:
        del sys.modules["onboard"]
    onboard = _load(REPO / ".agents" / "skills" / "onboarding" / "scripts" / "onboard.py")

    monkeypatch.delenv("USER", raising=False)
    monkeypatch.delenv("LOGNAME", raising=False)
    monkeypatch.setattr(getpass, "getuser", lambda: "test-onboard-user")
    
    real_open = open
    from unittest.mock import mock_open
    def mock_open_impl(file, mode="r", *args, **kwargs):
        if any(x in str(file) for x in ["gcp_config.txt", "persona.md", "mcp_config.json"]):
            return mock_open()()
        return real_open(file, mode, *args, **kwargs)
        
    monkeypatch.setattr("builtins.open", mock_open_impl)
    monkeypatch.setattr(os, "makedirs", lambda *args, **kwargs: None)
    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0, stdout='[{"account": "test@google.com", "status": "ACTIVE"}]')

    monkeypatch.setattr(subprocess, "run", mock_run)
    monkeypatch.setattr("shutil.which", lambda cmd: f"/usr/bin/{cmd}")

    monkeypatch.setattr(sys, "argv", [
        "onboard.py",
        "--persona", "Practice CE",
        "--folder-id", "12345",
        "--billing-account", "abc-123"
    ])
    
    with pytest.raises(ValueError) as excinfo:
        onboard.main()
    assert "Billing project is required" in str(excinfo.value)

    # Now pass it
    monkeypatch.setattr(sys, "argv", [
        "onboard.py",
        "--persona", "Practice CE",
        "--folder-id", "12345",
        "--billing-account", "abc-123",
        "--billing-project", "custom-billing-proj"
    ])
    onboard.main()
