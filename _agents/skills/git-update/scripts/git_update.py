import argparse
import subprocess
import sys

def run_command(command, check=True, cwd=None):
    try:
        result = subprocess.run(command, check=check, shell=True, text=True, capture_output=True, cwd=cwd)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        sys.exit(1)

def ask_permission(prompt):
    while True:
        response = input(f"{prompt} [y/N]: ").strip().lower()
        if response in ['y', 'yes']:
            return True
        if response in ['n', 'no', '']:
            return False
        print("Please answer 'y' or 'n'.")

def main():
    parser = argparse.ArgumentParser(description="Commit, push, and merge changes with confirmation.")
    parser.add_argument("-m", "--message", required=True, help="Commit message")
    parser.add_argument("--main-branch", default="main", help="Main branch name (default: main)")
    parser.add_argument("--path", default=".", help="Path to stage and commit (default: .)")
    args = parser.parse_args()

    # Get current branch
    res = run_command("git branch --show-current")
    current_branch = res.stdout.strip()
    if not current_branch:
        print("Error: Could not determine current branch.", file=sys.stderr)
        sys.exit(1)

    print(f"Current branch: {current_branch}")

    # Step 1: Local Changes
    print("\n--- Step 1: Local Changes ---")
    status_res = run_command("git status --porcelain")
    if not status_res.stdout.strip():
        print("No local changes to commit.")
    else:
        print("Local changes:")
        print(status_res.stdout)
        
        if ask_permission(f"Do you want to add and commit changes in '{args.path}'?"):
            print(f"Adding changes in '{args.path}'...")
            run_command(f"git add {args.path}")
            print("Committing changes...")
            run_command(f'git commit -m "{args.message}"')
            
            # Step 2: Push
            print("\n--- Step 2: Push Changes ---")
            if ask_permission(f"Do you want to push {current_branch} to origin?"):
                print(f"Pushing {current_branch} to origin...")
                run_command(f"git push origin {current_branch}")
        else:
            print("Skipping commit and push.")

    # Step 3: Fetch and Show Incoming Changes
    print("\n--- Step 3: Fetch and Compare ---")
    print("Fetching from origin...")
    run_command("git fetch origin")
    
    # Find common ancestor
    try:
        base_res = run_command(f"git merge-base HEAD origin/{args.main_branch}")
        base_commit = base_res.stdout.strip()
    except SystemExit:
        print(f"Error: Could not find common ancestor with origin/{args.main_branch}. Make sure the branch exists.")
        sys.exit(1)
        
    print(f"Common ancestor: {base_commit}")
    
    # Changes in current branch
    diff_current = run_command(f"git diff --name-only {base_commit}..HEAD")
    print(f"\nFiles changed in {current_branch} (since divergence):")
    if diff_current.stdout.strip():
        print(diff_current.stdout)
    else:
        print("No changes.")
        
    # Changes in main branch
    diff_main = run_command(f"git diff --name-only {base_commit}..origin/{args.main_branch}")
    print(f"\nFiles changed in origin/{args.main_branch} (since divergence):")
    if diff_main.stdout.strip():
        print(diff_main.stdout)
    else:
        print("No changes.")
        
    # Step 4: Merge
    print("\n--- Step 4: Merge ---")
    if ask_permission(f"Do you want to merge origin/{args.main_branch} into {current_branch}?"):
        print(f"Merging origin/{args.main_branch} into {current_branch}...")
        merge_res = subprocess.run(f"git merge origin/{args.main_branch}", shell=True, text=True, capture_output=True)
        
        print(merge_res.stdout)
        if merge_res.returncode != 0:
            print(f"Merge conflict or error occurred. Please resolve manually.", file=sys.stderr)
            print(merge_res.stderr, file=sys.stderr)
            sys.exit(merge_res.returncode)
        print("Merge completed successfully.")
    else:
        print("Skipping merge.")

    print("\nGit update process finished.")

if __name__ == "__main__":
    main()
