import argparse
import subprocess
import sys
import os

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

def run_command(command, capture_output=False, check_return=True):
    """Runs a shell command."""
    try:
        print(f"Executing: {command}")
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=capture_output, 
            text=True,
            check=check_return,
            encoding='utf-8'
        )
        if capture_output:
            return True, result.stdout, result.stderr
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return False, e.stdout, e.stderr if capture_output else False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False, "", "" if capture_output else False

def get_config():
    # Search for config file in current dir, script dir, or parent dirs
    script_dir = os.path.dirname(os.path.abspath(__file__))
    search_dirs = [
        os.getcwd(), 
        script_dir, 
        os.path.dirname(script_dir),
        # Also check gcp-provisioning directory specifically
        os.path.join(os.path.dirname(os.path.dirname(script_dir)), "gcp-provisioning")
    ]
    config_path = None
    for d in search_dirs:
        p = os.path.join(d, CONFIG_FILE)
        if os.path.exists(p):
            config_path = p
            break
            
    if not config_path:
         print(f"Error: Config file '{CONFIG_FILE}' not found in search paths.")
         print("Please create it or ensure it exists in one of the expected locations.")
         sys.exit(1)
             
    return parse_config(config_path)

def list_projects(folder_id, markdown=False):
    print(f"Listing projects in folder: {folder_id}")
    # Using filter for parent folder. Note: parent.id might need to be checked depending on gcloud version
    cmd = f"gcloud projects list --filter='parent.id:{folder_id}' --format='table(name, projectId, projectNumber, createTime, state)'"
    success, stdout, stderr = run_command(cmd, capture_output=True, check_return=False)
    if success:
        lines = stdout.strip().split('\n')
        if lines:
            if markdown:
                print(f"# Projects to Cleanup (Folder: {folder_id})")
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 2:
                        name = parts[0]
                        pid = parts[1]
                        state = parts[-1] if len(parts) >= 5 else "Unknown"
                        print(f"- [ ] `{pid}` (Name: {name}, State: {state})")
            else:
                print(f"{'[#]':<5} {lines[0]}")
                for i, line in enumerate(lines[1:], start=1):
                    print(f"[{i}]".ljust(5) + f" {line}")
        return stdout
    else:
        print(f"Failed to list projects: {stderr}")
        return None

def delete_project(project_id, force=False):
    if not force:
        confirm = input(f"Are you sure you want to delete project '{project_id}'? (y/N): ")
        if confirm.lower() != 'y':
            print("Deletion cancelled.")
            return False
            
    print(f"🔍 Checking for safety liens on project {project_id}...")
    res = subprocess.run(["gcloud", "alpha", "resource-manager", "liens", "list", f"--filter=parent=projects/{project_id}", "--format=value(name)"], capture_output=True, text=True)
    for lien in res.stdout.strip().split("\n"):
        if lien:
            bare_id = lien.split("/")[-1]
            print(f"🔓 Removing blocking lien: {bare_id}...")
            subprocess.run(["gcloud", "alpha", "resource-manager", "liens", "delete", bare_id, "--quiet"], check=False)

    print(f"🗑️ Deleting project: {project_id}")
    cmd = f"gcloud projects delete {project_id} --quiet"
    return run_command(cmd)

def main():
    parser = argparse.ArgumentParser(description="Cleanup GCP projects for Codelab Creator.")
    parser.add_argument("--list", action="store_true", help="List projects in the configured folder.")
    parser.add_argument("--delete", type=str, help="Delete the specified project ID.")
    parser.add_argument("--delete-all", action="store_true", help="Delete ALL projects in the configured folder.")
    parser.add_argument("--force", action="store_true", help="Force deletion without confirmation.")
    parser.add_argument("--markdown", action="store_true", help="Output list in Markdown checkbox format.")
    
    args = parser.parse_args()
    
    config = get_config()
    folder_id = config.get('folder_id')
    
    if not folder_id:
        print("Error: 'folder_id' not found in config.")
        sys.exit(1)
        
    if args.list:
        list_projects(folder_id, markdown=args.markdown)
    elif args.delete:
        delete_project(args.delete, args.force)
    elif args.delete_all:
        projects_output = list_projects(folder_id)
        if not projects_output:
            print("No projects found or failed to list.")
            return
            
        lines = projects_output.strip().split('\n')
        if len(lines) <= 1:
             print("No projects found to delete.")
             return
             
        project_ids = []
        for line in lines[1:]: # Skip header
             parts = line.split()
             if parts and len(parts) >= 2:
                 project_ids.append(parts[1])
                 
        print(f"Found {len(project_ids)} projects to delete.")
        
        if not args.force:
            confirm = input(f"Are you sure you want to delete ALL {len(project_ids)} projects listed above? This is irreversible. (yes/NO): ")
            if confirm.lower() != 'yes':
                print("Operation cancelled.")
                return
                
        for pid in project_ids:
             delete_project(pid, force=True) # Force individual deletions after bulk confirmation
             
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
