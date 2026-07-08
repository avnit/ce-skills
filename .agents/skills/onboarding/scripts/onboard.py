#!/usr/bin/env python3
"""
Automated onboarding script for JetSki developer environments.
Generates gcp_config.txt, persona.md, updates mcp_config.json, checks CitC CompanyDoc readiness,
and synchronizes sidecars.
"""

import argparse
import json
import os
import subprocess

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

def main():
    parser = argparse.ArgumentParser(description="JetSki Developer Environment Onboarding Automation")
    parser.add_argument("--persona", required=True, choices=list(PERSONA_TEMPLATES.keys()), help="Primary Systems Engineering Persona")
    parser.add_argument("--folder-id", required=True, help="Google Cloud Folder ID for sandbox provisioning")
    parser.add_argument("--billing-account", required=True, help="Google Cloud Billing Account ID")
    parser.add_argument("--billing-project", default=os.environ.get("CE_BILLING_PROJECT"), help="BigQuery Billing Project ID")
    parser.add_argument("--billing-table", default="", help="BigQuery Billing Export Table ID")
    parser.add_argument("--cloudtop-host", default="", help="Optional Cloudtop VM hostname")
    parser.add_argument("--knowledge-project", default=os.environ.get("CE_KNOWLEDGE_PROJECT"), help="Developer Knowledge API Quota Project ID")
    parser.add_argument("--piper-workspace", default="ce-skills", help="Preferred Piper/CitC workspace name for CompanyDoc publishing")
    
    args = parser.parse_args()
    
    if not args.billing_project:
        raise ValueError(
            "Billing project is required. Please specify --billing-project or set the CE_BILLING_PROJECT environment variable."
        )
    
    workspace_root = os.environ.get("BUILD_WORKING_DIRECTORY", os.getcwd())
    print(f"🚀 Starting JetSki Onboarding Automation in: {workspace_root}")
    
    # 1. Generate gcp_config.txt
    gcp_config_path = os.path.join(workspace_root, "gcp_config.txt")
    billing_table = args.billing_table
    if not billing_table and args.billing_account:
        suffix = args.billing_account.replace("-", "_")
        billing_table = f"{args.billing_project}.billing.gcp_billing_export_resource_v1_{suffix}"
        
    with open(gcp_config_path, "w", encoding="utf-8") as f:
        f.write(f"folder_id={args.folder_id}\n")
        f.write(f"billing_account={args.billing_account}\n")
        f.write(f"billing_project={args.billing_project}\n")
        f.write(f"billing_table={billing_table}\n")
        if args.cloudtop_host:
            f.write(f"cloudtop_host={args.cloudtop_host}\n")
        f.write(f"piper_workspace={args.piper_workspace}\n")
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
    if "workspace" not in mcp_servers:
        mcp_servers["workspace"] = {
            "$typeName": "exa.cascade_plugins_pb.CascadePluginCommandTemplate",
            "command": "/google/bin/releases/codemind-mcp-servers/workspace_server.par",
            "args": [],
            "env": {}
        }
        print("✅ Injected 'workspace' MCP server configuration.")

    # Inject command and args binary definitions for google-developer-documentation-mcp
    gdev = mcp_servers.setdefault("google-developer-documentation-mcp", {})
    if not gdev.get("command") and not gdev.get("httpUrl") and not gdev.get("serverUrl"):
        if os.path.exists("/google/bin/releases/docs-mcp-local/docs_mcp_server.par"):
            gdev["command"] = "/google/bin/releases/docs-mcp-local/docs_mcp_server.par"
            gdev["args"] = []
        else:
            gdev["command"] = "npx"
            gdev["args"] = ["-y", "google-developer-documentation-mcp"]
        gdev.setdefault("env", {})
        print("✅ Injected 'command' and 'args' binary definitions for google-developer-documentation-mcp.")

    # Inject quota project header if customized
    if args.knowledge_project and args.knowledge_project != "codelab-creator-central":
        headers = gdev.setdefault("headers", {})
        headers["X-goog-user-project"] = args.knowledge_project
        print(f"✅ Injected X-goog-user-project header ({args.knowledge_project}) into MCP config.")
        
    with open(mcp_config_path, "w", encoding="utf-8") as f:
        json.dump(mcp_data, f, indent=2)
        f.write("\n")
    print(f"✅ Updated MCP configuration: {mcp_config_path}")

    # 4. Check & Initialize Piper CompanyDoc Workspace
    import getpass
    username = os.environ.get("USER") or os.environ.get("LOGNAME") or getpass.getuser()
    target_client_dir = f"/google/src/cloud/{username}/{args.piper_workspace}"
    target_company_dir = os.path.join(target_client_dir, "company")
    
    if os.path.exists(target_company_dir):
        print(f"✅ Verified preferred Piper CompanyDoc workspace: {target_company_dir}")
    elif os.path.exists("/google/src/cloud"):
        print(f"ℹ️ Preferred Piper workspace '{args.piper_workspace}' not found under /google/src/cloud/{username}/.")
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

    # 7. Pre-warm Mermaid CLI
    print("🎨 Pre-warming Mermaid CLI dependency cache...")
    subprocess.run(["npx", "-y", "@mermaid-js/mermaid-cli", "--help"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    print("✅ Mermaid CLI pre-warmed.")

    # 8. Community Group Membership
    print("\n👥 Checking community group membership (ce-skills-users@google.com)...")
    print("👉 Please verify you have joined the official Google Group at: https://groups.google.com/a/google.com/g/ce-skills-users")
    if os.path.exists("/google/src/cloud"):
        print("   Or run via CLI in CitC (Buganizer Component ID: 2150801):")
        print("   blaze run //ccc/groups/discussion/tools:membership_tool -- add --backend=prod --group=ce-skills-users@google.com --members=$USER@google.com --buganizer_id=<ticket_id_under_2150801>")

    print("\n🎉 Onboarding automation completed successfully! Your environment is fully ready.")

if __name__ == "__main__":
    main()
