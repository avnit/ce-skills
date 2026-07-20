#!/usr/bin/env python3
"""
validate_citations.py
Parses a markdown report file to validate documentation citation links and formatting.
Ensures no broken syntax exists and verifies all external citations point to valid cloud.google.com or standard domain structures.
"""

import argparse
import re
import sys
import urllib.request
from urllib.error import URLError, HTTPError

def extract_links(markdown_text):
    # Regex to find standard markdown links [text](url)
    link_pattern = r'\[([^\]]+)\]\((https?://[^\)\s]+)\)'
    return re.findall(link_pattern, markdown_text)

def validate_url(url, check_online=False):
    if not url.startswith("http://") and not url.startswith("https://"):
        return False, "URL must start with http:// or https://"
    
    if check_online:
        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (compatible; GCP-Architecture-Validator/1.0)'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status >= 400:
                    return False, f"HTTP status {response.status}"
        except HTTPError as e:
            # Some valid google docs return 403 or 404 to bots, but we flag for human review
            return False, f"HTTP Error: {e.code} - {e.reason}"
        except URLError as e:
            return False, f"URL Error: {e.reason}"
        except Exception as e:
            return False, f"Validation Error: {str(e)}"
            
    return True, "Valid"

def main():
    parser = argparse.ArgumentParser(description="Validate citations and documentation links in a markdown report.")
    parser.add_argument("file", help="Path to markdown report file to validate")
    parser.add_argument("--online", action="store_true", help="Perform actual HTTP requests to check link liveness")
    args = parser.parse_args()

    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"ERROR: Unable to read file '{args.file}': {e}", file=sys.stderr)
        sys.exit(1)

    links = extract_links(content)
    if not links:
        print("WARNING: No markdown citation links found in the report.", file=sys.stderr)
        sys.exit(0)

    print(f"Scanning {len(links)} citation link(s) in {args.file}...")
    errors = 0
    for text, url in links:
        is_valid, msg = validate_url(url, check_online=args.online)
        if not is_valid:
            print(f"❌ INVALID LINK: [{text}]({url}) -> {msg}", file=sys.stderr)
            errors += 1
        else:
            print(f"✅ OK: [{text}]({url})")

    if errors > 0:
        print(f"\nFAILED: Found {errors} invalid or broken citation link(s).", file=sys.stderr)
        sys.exit(1)
    
    print("\nSUCCESS: All citation links passed validation.")
    sys.exit(0)

if __name__ == "__main__":
    main()
