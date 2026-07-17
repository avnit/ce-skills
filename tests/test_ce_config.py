import pathlib
import pytest
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
LIB_DIR = REPO / ".agents" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

# Import the loader under test (we'll load it dynamically since it doesn't exist yet)
def _load_ce_config():
    import importlib.util
    module_path = LIB_DIR / "ce_config.py"
    spec = importlib.util.spec_from_file_location("ce_config", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["ce_config"] = module
    spec.loader.exec_module(module)
    return module

def test_config_loader_resolution(tmp_path, monkeypatch):
    """Verifies that config loader respects env override -> file -> default order."""
    # Write a dummy config file
    config_file = tmp_path / "gcp_config.txt"
    config_file.write_text(
        "# This is a comment\n"
        "folder_id=file-folder-id\n"
        "billing_account=\"file-billing-account\"\n"
        "\n"
        "pricing_table='file-pricing-table'\n"
    )

    monkeypatch.setenv("CE_CONFIG_PATH", str(config_file))
    
    # Now load the module
    ce_config = _load_ce_config()
    
    # 1. Verify default values when key is missing everywhere
    assert ce_config.get("missing_key", "my-default") == "my-default"
    
    # 2. Verify file values are parsed and normalized (quotes stripped)
    assert ce_config.get("folder_id") == "file-folder-id"
    assert ce_config.get_secret("billing_account") == "file-billing-account"
    assert ce_config.get("pricing_table") == "file-pricing-table"
    
    # 3. Verify security policy blocks sensitive keys in get()
    with pytest.raises(ValueError) as excinfo:
        ce_config.get("billing_account")
    assert "Sensitive credential key 'billing_account' must be retrieved via get_secret()" in str(excinfo.value)
    
    # 3. Verify environment overrides
    monkeypatch.setenv("FOLDER_ID", "env-folder-id")
    assert ce_config.get("folder_id") == "env-folder-id"

    # 4. Verify required constraint check raises ValueError
    with pytest.raises(ValueError) as excinfo:
        ce_config.get("required_key", required=True)
    assert "Required configuration key 'required_key' is missing" in str(excinfo.value)

def test_onboarding_writes_all_documented_keys(tmp_path, monkeypatch):
    """Verifies that onboard.py writes all 15 configuration keys (including persona) to gcp_config.txt."""
    import importlib.util
    import getpass
    import subprocess
    
    # Load onboard.py dynamically
    onboard_path = REPO / ".agents" / "skills" / "onboarding" / "scripts" / "onboard.py"
    spec = importlib.util.spec_from_file_location("onboard", onboard_path)
    onboard = importlib.util.module_from_spec(spec)
    sys.modules["onboard"] = onboard
    spec.loader.exec_module(onboard)
    
    # Mock subprocess checks and shutil.which
    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0, stdout='[{"account": "test@google.com", "status": "ACTIVE"}]')

    monkeypatch.setattr(subprocess, "run", mock_run)
    monkeypatch.setattr("shutil.which", lambda cmd: f"/usr/bin/{cmd}")
    monkeypatch.setattr(getpass, "getuser", lambda: "test-user")
    
    # Direct output to tmp_path
    monkeypatch.setenv("BUILD_WORKING_DIRECTORY", str(tmp_path))
    
    # Setup argv parameters for onboarding
    monkeypatch.setattr(sys, "argv", [
        "onboard.py",
        "--persona", "Practice CE",
        "--folder-id", "test-folder-123",
        "--billing-account", "test-billing-acct-abc",
        "--billing-project", "test-billing-project-id",
        "--billing-table", "custom-billing-table",
        "--pricing-table", "custom-pricing-table",
        "--knowledge-project", "custom-knowledge-proj",
        "--rag_project", "custom-rag-project",
        "--rag_location", "us-east1",
        "--rag_corpus", "custom-rag-corpus-id",
        "--closed_loop_account", "custom-closed-loop-acct",
        "--closed_loop_vertex_project", "custom-closed-loop-vertex-proj",
        "--closed_loop_firestore_project", "custom-closed-loop-firestore-proj",
        "--cloudtop-host", "custom-cloudtop-host",
        "--piper-workspace", "custom-piper-ws"
    ])
    
    # Mock open implementation to capture file content but fallback to real_open for local translation libraries
    written_configs = {}
    real_open = open
    def mock_open_impl(file, mode="r", *args, **kwargs):
        if "gcp_config.txt" in str(file):
            # Create a mock file write handler to capture output
            from io import StringIO
            mock_file = StringIO()
            original_close = mock_file.close
            def mock_close():
                # Store the content before closing
                written_configs["content"] = mock_file.getvalue()
                original_close()
            mock_file.close = mock_close
            return mock_file
        return real_open(file, mode, *args, **kwargs)
        
    monkeypatch.setattr("builtins.open", mock_open_impl)
    
    # Run main onboarding flow
    onboard.main()
    
    # Parse written config lines
    lines = [raw_line.strip() for raw_line in written_configs["content"].split("\n") if raw_line.strip()]
    parsed = {}
    for line in lines:
        k, v = line.split("=", 1)
        parsed[k] = v
        
    # Verify expected keys exist
    expected_keys = [
        "persona", "folder_id", "billing_account", "billing_project", "billing_table",
        "pricing_table", "knowledge_project", "rag_project", "rag_location", "rag_corpus",
        "closed_loop_account", "closed_loop_vertex_project", "closed_loop_firestore_project",
        "cloudtop_host", "piper_workspace", "USE_GKE_GCLOUD_AUTH_PLUGIN"
    ]
    for k in expected_keys:
        assert k in parsed, f"Expected key '{k}' was not written to gcp_config.txt"
        
    # Verify specific mapped values
    assert parsed["persona"] == "Practice CE"
    assert parsed["folder_id"] == "test-folder-123"
    assert parsed["billing_account"] == "test-billing-acct-abc"
    assert parsed["billing_project"] == "test-billing-project-id"
    assert parsed["billing_table"] == "custom-billing-table"
    assert parsed["pricing_table"] == "custom-pricing-table"
    assert parsed["knowledge_project"] == "custom-knowledge-proj"
    assert parsed["rag_project"] == "custom-rag-project"
    assert parsed["rag_location"] == "us-east1"
    assert parsed["rag_corpus"] == "custom-rag-corpus-id"
    assert parsed["closed_loop_account"] == "custom-closed-loop-acct"
    assert parsed["closed_loop_vertex_project"] == "custom-closed-loop-vertex-proj"
    assert parsed["closed_loop_firestore_project"] == "custom-closed-loop-firestore-proj"
    assert parsed["cloudtop_host"] == "custom-cloudtop-host"
    assert parsed["piper_workspace"] == "custom-piper-ws"

def test_verify_system_uses_loader(tmp_path, monkeypatch):
    """Verifies that verify_system.py uses ce_config loader and handles required configuration validation checks."""
    import importlib.util
    
    # Load verify_system.py dynamically
    verify_path = REPO / ".agents" / "skills" / "system-validation" / "scripts" / "verify_system.py"
    spec = importlib.util.spec_from_file_location("verify_system", verify_path)
    verify_system = importlib.util.module_from_spec(spec)
    sys.modules["verify_system"] = verify_system
    spec.loader.exec_module(verify_system)
    
    # Point verify_system's REPO_ROOT to tmp_path
    monkeypatch.setattr(verify_system, "REPO_ROOT", str(tmp_path))
    
    # 1. Verification fails when gcp_config.txt file doesn't exist
    cfg_file = tmp_path / "gcp_config.txt"
    ok, msg = verify_system.check_gcp_config()
    assert not ok
    assert "gcp_config.txt does not exist" in msg
    
    # 2. Verification fails when required keys are missing or invalid
    cfg_file.write_text("billing_account=abc-123\n")
    # Tell ce_config to use this temp file
    monkeypatch.setenv("CE_CONFIG_PATH", str(cfg_file))
    
    # Reset ce_config cache to parse the new file
    import ce_config
    ce_config._cached_config = None
    
    ok, msg = verify_system.check_gcp_config()
    assert not ok
    assert "Validation failed" in msg or "Required configuration key" in msg or "Required credential key" in msg
    
    # 3. Verification succeeds when required keys are present
    cfg_file.write_text(
        "folder_id=123456\n"
        "billing_account=abc-123\n"
        "billing_project=project-xyz\n"
    )
    ce_config._cached_config = None
    
    ok, msg = verify_system.check_gcp_config()
    assert ok
    assert "gcp_config.txt verified" in msg


