import argparse
import subprocess
import sys
import os
import re
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

def run_command(command, dry_run=False, capture_output=False, check_return=True):
    """Runs a shell command."""
    if dry_run:
        print(f"[DRY RUN] Executing: {command}")
        return True, "", "" if capture_output else True
    
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


def is_billing_enabled(project_id, dry_run=False):
    """Checks if billing is enabled for the given project."""
    if dry_run:
        print(f"[DRY RUN] Checking billing status for {project_id}")
        return False
        
    cmd = f"gcloud beta billing projects describe {project_id}"
    success, stdout, stderr = run_command(cmd, dry_run=dry_run, capture_output=True, check_return=False)
    if not success:
        print(f"Warning: Could not describe billing for {project_id}: {stderr}")
        return False
    return "billingEnabled: true" in stdout

def main():
    parser = argparse.ArgumentParser(description="Create a Google Cloud Project for Codelab testing.")
    parser.add_argument("lab_name", help="The name of the lab (e.g., ncc-vpc).")
    parser.add_argument("round_number", nargs="?", help="A unique round number (e.g., 101). If omitted, a random one is generated.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them.")
    
    args = parser.parse_args()
    
    # 1. Read Config
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Search for config file
    config_path = None
    search_dirs = [os.getcwd(), script_dir, os.path.dirname(script_dir)]
    for d in search_dirs:
        p = os.path.join(d, CONFIG_FILE)
        if os.path.exists(p):
            config_path = p
            break
            
    if not config_path:
         print(f"Error: Config file '{CONFIG_FILE}' not found. Please create it.")
         sys.exit(1)

    config = parse_config(config_path)
    
    required_keys = ['folder_id', 'billing_account']
    for key in required_keys:
        if key not in config:
             print(f"Error: Missing required config key '{key}' in {config_path}")
             sys.exit(1)
            
    # 2. Construct Project ID
    lab_name = re.sub(r'[^a-z0-9-]', '', args.lab_name.lower())[:19].rstrip('-')
    
    if args.round_number:
        round_number = re.sub(r'[^0-9]', '', args.round_number)
    else:
        round_number = str(int(time.time())) 
        print(f"No round number provided. Generated: {round_number}")
    
    project_id = f"{lab_name}-{round_number}"
    
    print(f"Preparing to create project: {project_id}")
    print(f"Folder ID: {config['folder_id']}")
    print(f"Billing Account: {config['billing_account']}")
    
    # 3. Create Project
    create_cmd = f"gcloud projects create {project_id} --folder={config['folder_id']} --name={project_id}"
    if not run_command(create_cmd, args.dry_run):
        print(f"Failed to create project {project_id}.")
        sys.exit(1)
    
    print(f"Waiting 30 seconds for project {project_id} to become active...")
    if not args.dry_run:
        time.sleep(30)

    # 4. Link Billing with Retries and Verification
    billing_linked = False
    retries = 5
    for i in range(retries):
        if is_billing_enabled(project_id, dry_run=args.dry_run):
            print(f"Billing already enabled for {project_id}.")
            billing_linked = True
            break
            
        print(f"Attempting to link billing account (attempt {i+1}/{retries})...")
        billing_cmd = f"gcloud beta billing projects link {project_id} --billing-account={config['billing_account']}"
        if run_command(billing_cmd, args.dry_run):
            print("Successfully ran billing link command. Waiting 10 seconds for propagation...")
            if not args.dry_run:
                time.sleep(10)
            if is_billing_enabled(project_id, dry_run=args.dry_run):
                print("Billing account linked and verified successfully.")
                billing_linked = True
                break
        else:
            print(f"Warning: Billing link command failed for {project_id}. Retrying...")
        
        if not args.dry_run and i < retries - 1:
            time.sleep(10)

    if not billing_linked:
        print(f"Error: Failed to link billing account to project {project_id} after {retries} attempts.")
        sys.exit(1)
        
    # 5. Enable Core APIs
    print("Enabling core APIs...")
    apis = [
        "compute.googleapis.com",
        "iap.googleapis.com",
        "networkconnectivity.googleapis.com",
        "logging.googleapis.com",
        "artifactregistry.googleapis.com",
        "pubsub.googleapis.com",
        "cloudresourcemanager.googleapis.com",
        "orgpolicy.googleapis.com"
    ]
    apis_cmd = f"gcloud services enable {' '.join(apis)} --project={project_id}"
    if not run_command(apis_cmd, args.dry_run):
        print(f"Failed to enable APIs for project {project_id}.")
        sys.exit(1)
        
    print(f"\nSUCCESS: Project {project_id} setup complete.")

    print(f"\nProject {project_id} is ready for use.")

if __name__ == "__main__":
    main()
