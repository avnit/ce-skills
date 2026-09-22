#!/usr/bin/env python3
import os
import json

def get_untracked_root_files():
    """Scans the root directory for flat untracked files excluding core system directories."""
    root_dir = os.getcwd()
    all_items = os.listdir(root_dir)
    
    findings = []
    # Core directories that represent valid structural namespaces
    valid_dirs = [".agents", "prompts", "scripts", "resources", "labs", "meeting", "artifacts", "node_modules", "agent_src", "user_deploy", "bin", "references"]
    # Standard repository dotfiles or baseline configuration files
    valid_files = [".gitignore", ".gitmodules", "README.md", "package.json", "package-lock.json", "gcp_config.txt", "agent_metadata.txt", "requirements.txt", "ruff.toml", "ce-scale"]
    
    for item in sorted(all_items):
        path = os.path.join(root_dir, item)
        if os.path.isdir(path):
            if item not in valid_dirs and not item.startswith('.'):
                findings.append({
                    "name": item, 
                    "type": "directory", 
                    "proposed_action": "ignore",
                    "proposed_target": "∅",
                    "reason": "Flat custom directory detected at workspace root."
                })
        else:
            if item not in valid_files and not item.startswith('.'):
                # Classify flat asset mapping appropriate core folder locations
                target = "Unknown"
                action = "move"
                if item.endswith(".py") or item.endswith(".sh"):
                    target = f"scripts/{item}"
                elif item.endswith(".yaml") or item.endswith(".yml") or item.endswith(".json"):
                    target = f"resources/{item}"
                elif item.endswith(".md"):
                    target = f"artifacts/{item}"
                
                findings.append({
                    "name": item,
                    "type": "file",
                    "proposed_action": action,
                    "proposed_target": target,
                    "reason": "Root configuration asset lacks isolated subdirectory mapping."
                })
                
    print(json.dumps({"total_findings": len(findings), "findings": findings}, indent=2))
    return findings

if __name__ == "__main__":
    get_untracked_root_files()
