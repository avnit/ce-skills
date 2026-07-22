import os
import sys
import json
import glob

# Bootstrapping .agents lib path
_script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(_script_dir, "..", ".."))

lib_path = os.path.join(repo_root, ".agents", "lib")
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

import ce_config  # noqa: E402

def main():
    print("🔄 Discovering sidecar templates...")
    
    # Locate all sidecar.json templates in the repository under .agents/
    search_pattern = os.path.join(repo_root, ".agents", "**", "sidecar.json")
    templates = glob.glob(search_pattern, recursive=True)
    
    dest_root = os.path.expanduser("~/.gemini/jetski/sidecars")
    os.makedirs(dest_root, exist_ok=True)
    
    bug_scan_dir = ce_config.get("bug_scan_dir")
    
    for t_path in templates:
        sidecar_id = os.path.basename(os.path.dirname(t_path))
        print(f"📦 Syncing sidecar: {sidecar_id}")
        
        try:
            with open(t_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            print(f"❌ Error loading template {t_path}: {e}")
            continue
            
        args = config.get("args", [])
        
        # 1. Resolve relative script path (args[2])
        if len(args) > 2 and args[1] in ("python", "python3"):
            script_path = args[2]
            if not script_path.startswith("/") and not script_path.startswith("$"):
                abs_script = os.path.abspath(os.path.join(repo_root, script_path))
                args[2] = abs_script
                print(f"   -> Resolved script path: {abs_script}")
                
        # 2. De-hardcode bug_scan_dir
        for i in range(len(args)):
            if "{{bug_scan_dir}}" in str(args[i]):
                if not bug_scan_dir:
                    raise ValueError("Required configuration key 'bug_scan_dir' is missing.")
                args[i] = str(args[i]).replace("{{bug_scan_dir}}", bug_scan_dir)
                print(f"   -> Substituted placeholder bug_scan_dir: {bug_scan_dir}")
            elif args[i] == "--scan-dir" and i + 1 < len(args):
                if not bug_scan_dir:
                    raise ValueError("Required configuration key 'bug_scan_dir' is missing.")
                args[i + 1] = bug_scan_dir
                print(f"   -> Resolved --scan-dir value: {bug_scan_dir}")
                
        config["args"] = args
        
        dest_dir = os.path.join(dest_root, sidecar_id)
        os.makedirs(dest_dir, exist_ok=True)
        dest_file = os.path.join(dest_dir, "sidecar.json")
        
        try:
            with open(dest_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            print(f"   -> Generated sidecar configuration at: {dest_file}")
        except Exception as e:
            print(f"❌ Error writing sidecar configuration to {dest_file}: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
