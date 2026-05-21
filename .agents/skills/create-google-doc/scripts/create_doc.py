#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import sys

def find_onedoc_binary():
    """Dynamically locates the compiled OneDoc par file in the user's CITC workspaces."""
    user = os.environ.get('USER') or os.environ.get('LOGNAME')
    if not user:
        return None
    cloud_dir = f"/google/src/cloud/{user}"
    if not os.path.exists(cloud_dir):
        return None
    for client in os.listdir(cloud_dir):
        client_dir = os.path.join(cloud_dir, client)
        if os.path.isdir(client_dir):
            onedoc_path = os.path.join(client_dir, "google3/blaze-bin/geo/gestalt/experimental/onedoc/onedoc.par")
            if os.path.exists(onedoc_path):
                return onedoc_path
    return None

def create_google_doc_api(src_path, title):
    """Creates a Google Doc from a local Markdown file using OneDoc (go/onedoc)."""
    if not os.path.exists(src_path):
        print(f"❌ Error: Source file not found at [{src_path}]", file=sys.stderr)
        return None
        
    onedoc_path = find_onedoc_binary()
    if not onedoc_path:
        print("❌ Error: OneDoc binary (onedoc.par) is not compiled or verified in any CITC workspace.", file=sys.stderr)
        print("Please run system validation or build it inside a Google3 workspace first by running:", file=sys.stderr)
        print("    blaze build //geo/gestalt/experimental/onedoc", file=sys.stderr)
        return None
        
    print(f"⚡ Deploying document via OneDoc binary at: {onedoc_path}")
    try:
        result = subprocess.run(
            [onedoc_path, "create", src_path, "--title", title],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        output = result.stdout + "\n" + result.stderr
        print(output)
        
        if result.returncode != 0:
            print(f"❌ OneDoc execution failed with exit code {result.returncode}", file=sys.stderr)
            return None
            
        # Parse the created GDoc URL from stdout/stderr
        url_match = re.search(r"https://docs\.google\.com/document/d/[a-zA-Z0-9\-_]+", output)
        if url_match:
            doc_url = url_match.group(0)
            if not doc_url.endswith("/edit"):
                doc_url += "/edit"
                
            # Automatically push the Markdown content to populate the created blank document
            print(f"⚡ Synchronizing local Markdown content via OneDoc push...")
            push_result = subprocess.run(
                [onedoc_path, "push", src_path],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            if push_result.returncode != 0:
                print(f"⚠️ Warning: OneDoc push failed with exit code {push_result.returncode}", file=sys.stderr)
                print(push_result.stdout + "\n" + push_result.stderr, file=sys.stderr)
                
            print(f"🚀 Success! Google Doc successfully generated and populated via OneDoc:\n{doc_url}")
            return doc_url
        else:
            print("❌ Error: Could not parse Google Doc URL from OneDoc execution output.", file=sys.stderr)
            return None
            
    except Exception as e:
        print(f"❌ Unexpected exception executing OneDoc: {e}", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser(description="Generate Google Doc natively on Cloudtop using OneDoc (go/onedoc).")
    parser.add_argument("--src", required=True, help="Path to local Markdown source file.")
    parser.add_argument("--title", required=True, help="Title of the target Google Doc.")
    args = parser.parse_args()
    
    create_google_doc_api(args.src, args.title)

if __name__ == "__main__":
    main()
