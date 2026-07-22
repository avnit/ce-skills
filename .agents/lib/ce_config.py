"""Centralized configuration loader for Customer Engineering agent skills."""

import os
import pathlib
import sys
from typing import Dict, Any, Optional

_cached_config: Optional[Dict[str, str]] = None

def get_repo_root() -> pathlib.Path:
    """Finds the root of the repository by walking up to locate the .agents sentinel."""
    current = pathlib.Path(__file__).resolve().parent
    for parent in current.parents:
        if (parent / ".agents").is_dir():
            return parent
    return current

def setup_sys_path() -> None:
    """Ensures .agents/lib is at the front of sys.path for child scripts."""
    root = get_repo_root()
    lib_path = str(root / ".agents" / "lib")
    if lib_path not in sys.path:
        sys.path.insert(0, lib_path)

def load_config() -> Dict[str, str]:
    """Locates and parses the key=value formatted gcp_config.txt file."""
    global _cached_config
    if _cached_config is not None:
        return _cached_config

    config_path_env = os.environ.get("CE_CONFIG_PATH")
    if config_path_env:
        paths_to_check = [pathlib.Path(config_path_env)]
    else:
        root = get_repo_root()
        paths_to_check = [
            root / "gcp_config.txt",
            pathlib.Path.cwd() / "gcp_config.txt",
        ]

    config_file: Optional[pathlib.Path] = None
    for p in paths_to_check:
        if p.exists() and p.is_file():
            config_file = p
            break

    config_dict: Dict[str, str] = {}
    if not config_file:
        _cached_config = config_dict
        return config_dict

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                # Skip comments and blank lines
                if not stripped or stripped.startswith("#"):
                    continue
                # Parse key=value
                if "=" in stripped:
                    key, val = stripped.split("=", 1)
                    config_dict[key.strip()] = val.strip("'\" \t")
    except Exception as e:
        sys.stderr.write(f"⚠️ Warning: Failed to parse configuration file at {config_file}: {e}\n")

    _cached_config = config_dict
    return config_dict

ENV_ALIASES = {
    "pricing_table": ["CE_PRICING_TABLE"],
    "billing_project": ["CE_BILLING_PROJECT"],
    # TODO(#90): Remove rag_project/rag_location/rag_corpus plumbing during W4-4 onboarding cleanup.
    "rag_project": ["CE_RAG_PROJECT_ID"],
    "rag_location": ["CE_RAG_LOCATION"],
    "rag_corpus": ["CE_RAG_CORPUS_NAME"],
    "closed_loop_account": ["CLOSED_LOOP_CREDENTIAL_ACCOUNT"],
    "closed_loop_vertex_project": ["CLOSED_LOOP_VERTEX_PROJECT"],
    "closed_loop_firestore_project": ["CLOSED_LOOP_FIRESTORE_PROJECT"],
    "waf_mcp_cwd": ["CE_WAF_MCP_CWD"],
    "bug_scan_dir": ["CE_BUG_SCAN_DIR"],
}

SECRET_KEYS = {"billing_account", "closed_loop_account"}

def get(key: str, default: Any = None, required: bool = False) -> Any:
    """Resolves metadata value using precedence: Environment Override -> config file -> default."""
    if key in SECRET_KEYS:
        raise ValueError(
            f"Security Policy: Sensitive credential key '{key}' must be retrieved via get_secret() "
            f"to isolate taint propagation from non-sensitive metadata configurations."
        )

    # 1. Check environment overrides (aliases first, then standard overrides)
    aliases = ENV_ALIASES.get(key, [])
    for alias in aliases:
        val = os.environ.get(alias)
        if val is not None:
            return val

    val = os.environ.get(f"CE_{key.upper()}") or os.environ.get(key.upper()) or os.environ.get(key)
    if val is not None:
        return val

    # 2. Check parsed configuration file
    cfg = load_config()
    val = cfg.get(key)
    if val is not None and val != "":
        return val

    # 3. Use default
    if val is None or val == "":
        val = default

    # 4. Check required constraint
    if required and (val is None or val == ""):
        raise ValueError(
            f"Required configuration key '{key}' is missing. Please configure it in gcp_config.txt "
            f"or run the onboarding workflow to populate the workspace configuration."
        )

    return val

def get_secret(key: str, default: Any = None, required: bool = False) -> Any:
    """Resolves sensitive credential value using precedence: Environment Override -> config file -> default."""
    # 1. Check environment overrides (aliases first, then standard overrides)
    aliases = ENV_ALIASES.get(key, [])
    for alias in aliases:
        val = os.environ.get(alias)
        if val is not None:
            return val

    val = os.environ.get(f"CE_{key.upper()}") or os.environ.get(key.upper()) or os.environ.get(key)
    if val is not None:
        return val

    # 2. Check parsed configuration file
    cfg = load_config()
    val = cfg.get(key)
    if val is not None and val != "":
        return val

    # 3. Use default
    if val is None or val == "":
        val = default

    # 4. Check required constraint
    if required and (val is None or val == ""):
        raise ValueError(
            f"Required credential key '{key}' is missing. Please configure it in gcp_config.txt "
            f"or run the onboarding workflow to populate the workspace configuration."
        )

    return val

# Automatically populate sys.path on import to help sibling imports
setup_sys_path()
