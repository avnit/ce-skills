"""Compiles segmented Markdown system prompts into a JSON manifest for JIT bootstrapping."""

import json
import os
import sys

# Absolute workspace path setup
WORKSPACE_ROOT = "/usr/local/google/home/shacharb/skynet"
PROMPTS_DIR = os.path.join(WORKSPACE_ROOT, "prompts")
OUTPUT_MANIFEST = os.path.join(WORKSPACE_ROOT, ".agents/state/compiled_subagents.json")

# Subagent definitions mapping names to files and descriptions
SUBAGENTS_MAP = {
    "discovery-analyst": {
        "file": "discovery_analyst.md",
        "description": "Ingests meeting notes, parses user requirements, and extracts scope constraints.",
        "enable_write_tools": True,
        "enable_mcp_tools": True
    },
    "cloud-architect": {
        "file": "architect.md",
        "description": "Designs technical foundations, VPC topologies, and writes Terraform HCL.",
        "enable_write_tools": True,
        "enable_mcp_tools": True
    },
    "codelab-writer": {
        "file": "writer.md",
        "description": "Authors instructional tutorial content and structures Markdown lab steps.",
        "enable_write_tools": True,
        "enable_mcp_tools": False
    },
    "security-critic": {
        "file": "reviewer.md",
        "description": "Audits cloud designs and HCL against NIST security policies in a read-only sandbox.",
        "enable_write_tools": False,  # Strict read-only sandbox
        "enable_mcp_tools": True
    },
    "chaos-tester": {
        "file": "tester.md",
        "description": "Executes validation scripts and tests target infrastructure deployments.",
        "enable_write_tools": True,
        "enable_mcp_tools": True
    }
}

def compile_prompts():
  print("Starting system prompt compilation...")
  manifest = {}
  
  # Ensure output directory exists
  os.makedirs(os.path.dirname(OUTPUT_MANIFEST), exist_ok=True)

  for name, meta in SUBAGENTS_MAP.items():
    prompt_path = os.path.join(PROMPTS_DIR, meta["file"])
    if not os.path.exists(prompt_path):
      print(f"Error: Source prompt file missing: {prompt_path}", file=sys.stderr)
      sys.exit(1)

    print(f"Ingesting system prompt for: {name}...")
    with open(prompt_path, "r") as f:
      system_prompt = f.read().strip()

    manifest[name] = {
        "name": name,
        "description": meta["description"],
        "system_prompt": system_prompt,
        "enable_write_tools": meta["enable_write_tools"],
        "enable_mcp_tools": meta["enable_mcp_tools"]
    }

  # Write to destination manifest
  with open(OUTPUT_MANIFEST, "w") as f:
    json.dump(manifest, f, indent=2)

  print(f"Successfully compiled prompts manifest: {OUTPUT_MANIFEST}")

if __name__ == "__main__":
  compile_prompts()
