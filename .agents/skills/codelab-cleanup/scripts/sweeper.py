#!/usr/bin/env python3
import argparse
import datetime
import json
import os
import subprocess
import sys
import time

CONFIG_FILE = "gcp_config.txt"

def parse_config(config_path):
    """Parses the simple key=value config file."""
    config = {}
    if not os.path.exists(config_path):
        print(f"Error: Config file '{config_path}' not found.")
        sys.exit(1)
        
    with open(config_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip().strip('"').strip("'")
    return config

def run_command(cmd_args):
    """Runs a system command safely without shell."""
    try:
        result = subprocess.run(
            cmd_args, 
            shell=False, 
            capture_output=True, 
            text=True,
            encoding='utf-8'
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def get_config():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    search_dirs = [
        os.getcwd(), 
        script_dir, 
        os.path.dirname(script_dir),
        os.path.dirname(os.path.dirname(script_dir))
    ]
    config_path = None
    for d in search_dirs:
        p = os.path.join(d, CONFIG_FILE)
        if os.path.exists(p):
            config_path = p
            break
            
    if not config_path:
         print(f"❌ Error: Config file '{CONFIG_FILE}' not found in search paths.")
         sys.exit(1)
              
    return parse_config(config_path)

def get_active_projects(folder_id):
    """Fetches all active projects in folder using structured JSON output."""
    cmd = [
        "gcloud", "projects", "list",
        f"--filter=parent.id:{folder_id} AND lifecycleState:ACTIVE",
        "--format=json"
    ]
    success, stdout, stderr = run_command(cmd)
    if not success:
        print(f"❌ Error listing projects in folder {folder_id}: {stderr}", file=sys.stderr)
        return []
    try:
        return json.loads(stdout)
    except Exception as e:
        print(f"❌ Error parsing projects JSON: {e}", file=sys.stderr)
        return []

def delete_project(project_id):
    """Quietly deletes project non-interactively."""
    print(f"🔥 Sweeper: Deleting expired project: {project_id}")
    cmd = ["gcloud", "projects", "delete", project_id, "--quiet"]
    success, stdout, stderr = run_command(cmd)
    if success:
        print(f"✅ Successfully deleted {project_id}.")
        return True
    else:
        print(f"❌ Failed to delete {project_id}: {stderr}", file=sys.stderr)
        return False

def sweep_expired_projects(folder_id, age_hours=4, dry_run=True):
    print(f"🧹 Sweeper: Scanning folder [{folder_id}] for sandbox projects older than {age_hours} hours...")
    projects = get_active_projects(folder_id)
    if not projects:
        print("🧹 Sweeper: No active projects found.")
        return
        
    now = datetime.datetime.now(datetime.timezone.utc)
    expired_count = 0
    
    for p in projects:
        pid = p.get("projectId")
        create_time_str = p.get("createTime")
        if not pid or not create_time_str:
            continue
            
        # Parse gcloud timestamp format: "2026-05-19T01:27:31.256Z" or "2026-05-19T01:27:31Z"
        # Standard ISO format parsing
        try:
            # Stripping microsecond decimal points to allow simple datetime parsing
            clean_time_str = re.sub(r'\.\d+Z$', 'Z', create_time_str)
            create_time = datetime.datetime.strptime(clean_time_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
        except Exception:
            try:
                # Fallback: handle complete ISO parser
                create_time = datetime.datetime.fromisoformat(create_time_str.replace("Z", "+00:00"))
            except Exception as parse_err:
                print(f"⚠️ Warning: Failed to parse creation time '{create_time_str}' for project {pid}: {parse_err}")
                continue
                
        age = now - create_time
        age_in_hours = age.total_seconds() / 3600.0
        
        if age_in_hours > age_hours:
            expired_count += 1
            print(f"⚠️ Expired Resource Found: `{pid}` | Created: {create_time_str} | Run Time: {age_in_hours:.2f} hours")
            if not dry_run:
                delete_project(pid)
        else:
            print(f"🟢 Active Resource (Safe): `{pid}` | Created: {create_time_str} | Run Time: {age_in_hours:.2f} hours")
            
    print(f"\n🧹 Sweeper Run Complete. Found {expired_count} expired projects.")

def main():
    # Simple inline regex support without third party dependencies
    global re
    import re
    
    parser = argparse.ArgumentParser(description="Automated GCP sandbox project leak sweeper.")
    parser.add_argument("--age", type=int, default=4, help="Age limit in hours (default: 4).")
    parser.add_argument("--force", action="store_true", help="Execute deletion without dry-run safety checks.")
    
    args = parser.parse_args()
    
    config = get_config()
    folder_id = config.get("folder_id")
    if not folder_id:
        print("❌ Error: 'folder_id' not configured in gcp_config.txt.")
        sys.exit(1)
        
    sweep_expired_projects(folder_id, age_hours=args.age, dry_run=not args.force)

if __name__ == "__main__":
    main()
