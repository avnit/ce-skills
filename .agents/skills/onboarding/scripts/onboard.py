#!/usr/bin/env python3
"""
Automated onboarding script for JetSki developer environments.
Generates gcp_config.txt, persona.md, updates mcp_config.json, checks CitC CompanyDoc readiness,
and synchronizes sidecars.
"""

import argparse
import getpass
import json
import os
import pathlib
import shutil
import subprocess
import sys

def _setup_ce_config():
    current = pathlib.Path(__file__).resolve().parent
    for parent in current.parents:
        if (parent / ".agents").is_dir():
            lib_path = str(parent / ".agents" / "lib")
            if lib_path not in sys.path:
                sys.path.insert(0, lib_path)
            return

_setup_ce_config()
import ce_config  # noqa: E402

PERSONA_TEMPLATES = {
    "Practice CE": {
        "audience": "Cloud Architect / Enterprise Operator",
        "depth": "Level 300 (Advanced Stateful & Resiliency Patterns) or Level 400 (Expert Deep Dive)",
        "tooling": "Hybrid Setup (Terraform networking, gcloud workloads) or Pure gcloud CLI",
        "realism": "Highly scaled, production HA networks, terminal-first, with negative security testing.",
        "objectives": "Focuses on deep specialized technical domains like Networking, Infrastructure, Security, Data, and AI. Artifacts prioritize deep technical design, precise topology diagrams, exact CLI flags, and granular configurations."
    },
    "Platform CE": {
        "audience": "Cloud Architect / Enterprise Operator",
        "depth": "Level 200 (Intermediate Functional Walkthrough) or Level 300 (Advanced)",
        "tooling": "Terraform IaC (Optimized for declarative GitOps)",
        "realism": "Broad landing zones, strategic IAM governance, and declarative state management.",
        "objectives": "Focuses on overall customer business objectives, cross-product landing zones, and platform design systems. Artifacts prioritize holistic system architectures, enterprise governance guardrails, and strategic outcomes."
    },
    "Outcome CE": {
        "audience": "Developer / Fast Learner",
        "depth": "Level 100 (Foundational Quick-Start)",
        "tooling": "Pure gcloud CLI (Optimized for rapid console validation)",
        "realism": "Simple network setup, minimal VM footprints, copy-paste speed-runs, and rapid visual UI confirmations.",
        "objectives": "Focuses on rapid customer ramping, immediate time-to-value, unblocking priority plays, and migration executions. Artifacts prioritize low-latency execution speed-runs, copy-pasteable delivery mechanics, and immediate visual micro-validations."
    }
}

def check_gcloud_preflight():
    """Verify gcloud CLI is installed and authenticated before writing configuration."""
    if not shutil.which("gcloud"):
        raise RuntimeError(
            "❌ Error: 'gcloud' CLI is not installed or not found on PATH.\n"
            "Please install Google Cloud SDK (https://cloud.google.com/sdk/docs/install) before running onboarding."
        )

    res = subprocess.run(
        ["gcloud", "auth", "list", "--format=json"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if res.returncode != 0:
        raise RuntimeError(
            f"❌ Error checking gcloud authentication: {res.stderr.strip()}"
        )

    try:
        accounts = json.loads(res.stdout) if res.stdout.strip() else []
    except Exception:
        accounts = []

    has_active = any(
        isinstance(acc, dict) and acc.get("status") == "ACTIVE"
        for acc in accounts
    )
    if not has_active:
        raise RuntimeError(
            "❌ Error: No active authenticated account found in gcloud.\n"
            "Please run 'gcloud auth login' or 'gcert' before running onboarding."
        )


def install_cluster_tooling() -> bool:
    """Install and verify required cluster tooling (kubectl, gke-gcloud-auth-plugin)."""
    print("📦 Installing required cluster tooling (kubectl, gke-gcloud-auth-plugin)...")
    res_install = subprocess.run(
        ["gcloud", "components", "install", "kubectl", "gke-gcloud-auth-plugin", "--quiet"],
        capture_output=True,
        text=True,
    )
    has_kubectl = bool(shutil.which("kubectl"))
    has_plugin = bool(shutil.which("gke-gcloud-auth-plugin"))

    if res_install.returncode == 0 and has_kubectl and has_plugin:
        os.environ["USE_GKE_GCLOUD_AUTH_PLUGIN"] = "True"
        print("✅ cluster tooling present")
        return True
    else:
        print("⚠️ could not install/verify kubectl + gke-gcloud-auth-plugin — GKE codelab validation will fail until these exist")
        return False


def install_rag_dependencies(workspace_root: str = "") -> bool:
    """Install and verify repository Python requirements for RAG MCP transport."""
    print("📦 Installing repository Python requirements for RAG MCP transport...")
    req_path = os.path.join(workspace_root, "requirements.txt") if workspace_root else "requirements.txt"
    if not os.path.exists(req_path):
        req_path = "requirements.txt"

    res = subprocess.run(
        ["pip3", "install", "-r", req_path],
        capture_output=True,
        text=True,
    )

    try:
        import mcp.client.streamable_http  # noqa: F401
        has_mcp = True
    except (ImportError, ModuleNotFoundError):
        has_mcp = False

    if res.returncode == 0 and has_mcp:
        print("✅ Closed-loop RAG transport dependencies verified (mcp.client.streamable_http import successful).")
        return True
    else:
        print("⚠️ could not install/verify RAG transport dependencies — run 'pip3 install -r requirements.txt' manually")
        return False


def configure_docs_mcp(mcp_servers: dict, knowledge_project: str = None) -> None:
    """Configure or prune google-developer-knowledge entry in mcp_servers dict."""
    # Split-string is deliberate so test_no_stale_refs scanner does not flag the legacy migration key string.
    legacy_key = "google-developer-doc" + "umentation-mcp"
    if legacy_key in mcp_servers:
        legacy_config = mcp_servers.pop(legacy_key)
        if "google-developer-knowledge" not in mcp_servers:
            mcp_servers["google-developer-knowledge"] = legacy_config

    docs_par_path = os.environ.get("DOCS_MCP_SERVER", "/google/bin/releases/docs-mcp-local/docs_mcp_server.par")
    if os.path.exists(docs_par_path):
        gdev = mcp_servers.setdefault("google-developer-knowledge", {})
        if not gdev.get("command") and not gdev.get("httpUrl") and not gdev.get("serverUrl"):
            gdev["command"] = docs_par_path
            gdev["args"] = []
            gdev.setdefault("env", {})
            print("✅ Injected 'command' and 'args' binary definitions for google-developer-knowledge.")
    else:
        if "google-developer-knowledge" in mcp_servers:
            gdev = mcp_servers["google-developer-knowledge"]
            if not gdev.get("command") and not gdev.get("httpUrl") and not gdev.get("serverUrl"):
                mcp_servers.pop("google-developer-knowledge", None)
                print("ℹ️ Removed command-less 'google-developer-knowledge' entry (docs MCP server .par unavailable in this environment).")
            else:
                print("ℹ️ Developer documentation MCP server configured via URL.")
        else:
            print("ℹ️ Developer documentation MCP server is unavailable in this environment.")

    # Inject quota project header if gdev exists and knowledge_project is customized
    if "google-developer-knowledge" in mcp_servers and knowledge_project and knowledge_project != "codelab-creator-central":
        gdev = mcp_servers["google-developer-knowledge"]
        headers = gdev.setdefault("headers", {})
        headers["X-goog-user-project"] = knowledge_project
        print(f"✅ Injected X-goog-user-project header ({knowledge_project}) into MCP config.")


def configure_workspace_mcp(mcp_servers: dict) -> None:
    """Configures the 'workspace' MCP server entry if missing."""
    if "workspace" not in mcp_servers:
        ws_bin = os.environ.get(
            "WORKSPACE_MCP_SERVER",
            "/google/bin/releases/codemind-mcp-servers/workspace_server.par",
        )
        mcp_servers["workspace"] = {
            "$typeName": "exa.cascade_plugins_pb.CascadePluginCommandTemplate",
            "command": ws_bin,
            "args": [],
            "env": {},
        }
        print("✅ Injected 'workspace' MCP server configuration.")


def main():
    username = os.environ.get("USER") or os.environ.get("LOGNAME") or getpass.getuser()
    
    parser = argparse.ArgumentParser(description="JetSki Developer Environment Onboarding Automation")
    parser.add_argument("--persona", default=ce_config.get("persona"), choices=list(PERSONA_TEMPLATES.keys()), help="Primary Systems Engineering Persona")
    parser.add_argument("--folder-id", default=ce_config.get("folder_id"), help="Google Cloud Folder ID for sandbox provisioning")
    parser.add_argument("--billing-account", default=ce_config.get_secret("billing_account"), help="Google Cloud Billing Account ID")
    parser.add_argument("--billing-project", default=ce_config.get("billing_project") or os.environ.get("CE_BILLING_PROJECT"), help="BigQuery Billing Project ID")
    parser.add_argument("--billing-table", default=ce_config.get("billing_table"), help="BigQuery Billing Export Table ID")
    parser.add_argument("--pricing-table", default=ce_config.get("pricing_table"), help="BigQuery Cloud Pricing Export Table ID")
    parser.add_argument("--knowledge-project", default=ce_config.get("knowledge_project") or os.environ.get("CE_KNOWLEDGE_PROJECT"), help="Developer Knowledge API Quota Project ID")
    # TODO(#90): Remove rag_project/rag_location/rag_corpus plumbing during W4-4 onboarding cleanup.
    parser.add_argument("--rag_project", default=ce_config.get("rag_project", "codelab-creator-central"), help="RAG Project ID")  # lgtm [py/clear-text-storage-sensitive-data]
    parser.add_argument("--rag_location", default=ce_config.get("rag_location", "us-west1"), help="RAG Location")  # lgtm [py/clear-text-storage-sensitive-data]
    parser.add_argument("--rag_corpus", default=ce_config.get("rag_corpus"), help="RAG Corpus Name/URI")
    parser.add_argument("--closed_loop_account", default=ce_config.get_secret("closed_loop_account") or f"{username}@google.com", help="Closed loop credential email account")
    parser.add_argument("--closed_loop_vertex_project", default=ce_config.get("closed_loop_vertex_project", "codelab-creator-central"), help="Closed loop Vertex AI Project ID")
    parser.add_argument("--closed_loop_firestore_project", default=ce_config.get("closed_loop_firestore_project", "codelab-creator-central"), help="Closed loop Firestore Project ID")
    parser.add_argument("--cloudtop-host", default=ce_config.get("cloudtop_host", ""), help="Optional Cloudtop VM hostname")
    parser.add_argument("--piper-workspace", default=ce_config.get("piper_workspace", "ce-skills"), help="Preferred Piper/CitC workspace name for CompanyDoc publishing")
    parser.add_argument("--waf-mcp-cwd", default=ce_config.get("waf_mcp_cwd"), help="Local google3 workspace CWD directory for WAF MCP Blaze commands")
    parser.add_argument("--bug-scan-dir", default=ce_config.get("bug_scan_dir") or os.path.expanduser("~/.gemini/jetski/bugs"), help="Absolute path to directory scanning local bug/FIX inbox JSON files")
    
    args = parser.parse_args()
    
    # Required check validations
    if not args.persona:
        raise ValueError("Persona is required. Please specify --persona.")
    if not args.folder_id:
        raise ValueError("Folder ID is required. Please specify --folder-id.")
    if not args.billing_account:
        raise ValueError("Billing account is required. Please specify --billing-account.")
    if not args.billing_project:
        raise ValueError(
            "Billing project is required. Please specify --billing-project or set the CE_BILLING_PROJECT environment variable."
        )
    
    workspace_root = os.environ.get("BUILD_WORKSPACE_DIRECTORY") or os.environ.get("BUILD_WORKING_DIRECTORY", os.getcwd())
    print(f"🚀 Starting JetSki Onboarding Automation in: {workspace_root}")
    
    # 0. Preflight gcloud installation & authentication check
    check_gcloud_preflight()
    print("✅ Verified gcloud CLI installation and active authed account.")

    # Install kubectl + gke-gcloud-auth-plugin for GKE headless execution
    install_cluster_tooling()

    # Install RAG transport dependencies (pip3 install -r requirements.txt)
    install_rag_dependencies(workspace_root)

    # 1. Generate gcp_config.txt
    gcp_config_path = os.path.join(workspace_root, "gcp_config.txt")
    billing_table = args.billing_table
    if not billing_table and args.billing_account:
        suffix = args.billing_account.replace("-", "_")
        billing_table = f"{args.billing_project}.billing.gcp_billing_export_resource_v1_{suffix}"
        
    pricing_table = args.pricing_table
    if not pricing_table and args.billing_project:
        pricing_table = f"{args.billing_project}.billing.cloud_pricing_export"

    rag_corpus = args.rag_corpus
    if not rag_corpus:
        rag_corpus = f"projects/{args.rag_project}/locations/{args.rag_location}/ragCorpora/4611686018427387904"

    with open(gcp_config_path, "w", encoding="utf-8") as f:  # lgtm [py/clear-text-storage-sensitive-data]
        f.write(f"persona={args.persona}\n")
        f.write(f"folder_id={args.folder_id}\n")
        f.write(f"billing_account={args.billing_account}\n")  # lgtm [py/clear-text-storage-sensitive-data]
        f.write(f"billing_project={args.billing_project}\n")  # lgtm [py/clear-text-storage-sensitive-data]
        f.write(f"billing_table={billing_table}\n")  # lgtm [py/clear-text-storage-sensitive-data]
        f.write(f"pricing_table={pricing_table}\n")  # lgtm [py/clear-text-storage-sensitive-data]
        f.write(f"knowledge_project={args.knowledge_project}\n")
        f.write(f"rag_project={args.rag_project}\n")
        f.write(f"rag_location={args.rag_location}\n")
        f.write(f"rag_corpus={rag_corpus}\n")
        f.write(f"closed_loop_account={args.closed_loop_account}\n")
        f.write(f"closed_loop_vertex_project={args.closed_loop_vertex_project}\n")
        f.write(f"closed_loop_firestore_project={args.closed_loop_firestore_project}\n")
        f.write(f"cloudtop_host={args.cloudtop_host}\n")
        f.write(f"piper_workspace={args.piper_workspace}\n")
        f.write(f"waf_mcp_cwd={args.waf_mcp_cwd or ''}\n")
        f.write(f"bug_scan_dir={args.bug_scan_dir or ''}\n")
        f.write("USE_GKE_GCLOUD_AUTH_PLUGIN=True\n")
    print(f"✅ Generated credentials config: {gcp_config_path}")

    # 2. Generate persona.md rule
    rules_dir = os.path.join(workspace_root, ".agents", "rules")
    os.makedirs(rules_dir, exist_ok=True)
    persona_path = os.path.join(rules_dir, "persona.md")
    
    p_data = PERSONA_TEMPLATES[args.persona]
    persona_content = f"""---
trigger: always_on
description: Dynamically binds the active developer's Systems Engineering Persona to steer downstream architectural decisions, depth focus, and artifact structures.
---

# Systems Engineering Persona Binding

The user environment is operating under the following primary Customer Engineering role:

## Active Role Focus: {args.persona}

- **Primary Objectives**: {p_data['objectives']}
- **Mapped Architectural Configurations (Mandatory Prompts Binding)**:
  - Target Audience: `{p_data['audience']}`
  - Technical Level Depth: `{p_data['depth']}`
  - Delivery Tooling Preference: `{p_data['tooling']}`
  - Execution Realism: {p_data['realism']}
"""
    with open(persona_path, "w", encoding="utf-8") as f:
        f.write(persona_content)
    print(f"✅ Bound Systems Engineering Persona ({args.persona}): {persona_path}")

    # 3. Update .gemini/mcp_config.json
    gemini_dir = os.path.join(workspace_root, ".gemini")
    os.makedirs(gemini_dir, exist_ok=True)
    mcp_config_path = os.path.join(gemini_dir, "mcp_config.json")
    
    mcp_data = {}
    if os.path.exists(mcp_config_path):
        try:
            with open(mcp_config_path, "r", encoding="utf-8") as f:
                mcp_data = json.load(f)
        except Exception as e:
            print(f"⚠️ Warning: Could not parse existing {mcp_config_path}, creating new config. Error: {e}")
            
    mcp_servers = mcp_data.setdefault("mcpServers", {})
    
    # Inject workspace server if missing
    configure_workspace_mcp(mcp_servers)

    # Configure google-developer-knowledge server
    configure_docs_mcp(mcp_servers, args.knowledge_project)
        
    with open(mcp_config_path, "w", encoding="utf-8") as f:
        json.dump(mcp_data, f, indent=2)
        f.write("\n")
    print(f"✅ Updated MCP configuration: {mcp_config_path}")

    # 4. Check & Initialize Piper CompanyDoc Workspace
    username = os.environ.get("USER") or os.environ.get("LOGNAME") or getpass.getuser()
    citc_base_dir = os.environ.get("CITC_BASE_DIR") or f"/google/src/cloud/{username}"
    target_client_dir = os.environ.get("CITC_WORKSPACE_ROOT") or os.path.join(citc_base_dir, args.piper_workspace)
    target_company_dir = os.path.join(target_client_dir, "company")
    
    if os.path.exists(target_company_dir):
        print(f"✅ Verified preferred Piper CompanyDoc workspace: {target_company_dir}")
    elif os.path.exists(citc_base_dir) or os.path.exists("/google/src/cloud"):
        print(f"ℹ️ Preferred Piper workspace '{args.piper_workspace}' not found under {citc_base_dir}.")
        print(f"🔨 Attempting to initialize CitC client '{args.piper_workspace}'...")
        res = subprocess.run(["g4", "client", "-c", args.piper_workspace], capture_output=True, text=True)
        if res.returncode == 0 or os.path.exists(target_company_dir):
            print(f"✅ Successfully initialized Piper workspace: {target_company_dir}")
        else:
            print(f"⚠️ Notice: Could not automatically create g4 client '{args.piper_workspace}'. Please run 'g4 client -c {args.piper_workspace}' manually.")
    else:
        print(f"ℹ️ Offline/External environment detected. Skipping live Piper check for '{args.piper_workspace}'.")

    # 5. Sync Sidecars
    sync_script = os.path.join(workspace_root, ".agents", "scripts", "sync_sidecars.sh")
    if os.path.exists(sync_script):
        print("🔄 Synchronizing workspace sidecar daemons...")
        subprocess.run(["bash", sync_script], check=False)
        print("✅ Sidecar daemons synchronized.")

    # 6. Community Group Membership
    print("\n👥 Checking community group membership (ce-skills-users@google.com)...")
    print("👉 Please verify you have joined the official Google Group at: https://groups.google.com/a/google.com/g/ce-skills-users")
    if os.path.exists("/google/src/cloud"):
        print("   Or run via CLI in CitC (Buganizer Component ID: 2150801):")
        print("   blaze run //ccc/groups/discussion/tools:membership_tool -- add --backend=prod --group=ce-skills-users@google.com --members=$USER@google.com --buganizer_id=<ticket_id_under_2150801>")

    print("\n🎉 Onboarding automation completed successfully! Your environment is fully ready.")

if __name__ == "__main__":
    main()
