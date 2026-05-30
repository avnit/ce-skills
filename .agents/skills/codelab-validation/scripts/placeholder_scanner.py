#!/usr/bin/env python3
"""Generic Variable Placeholder Scanner.

Scans codelab markdown files for dynamic placeholder strings (e.g., <your-project-id>,
<your looker instance name>) inside bash/gcloud code blocks to facilitate pre-flight variable mapping.
"""

import argparse
import json
import os
import re
import sys

def scan_placeholders(markdown_path):
    """Parses a markdown file and returns a sorted list of unique bracketed placeholders found in bash blocks."""
    if not os.path.exists(markdown_path):
        print(f"Error: File not found at {markdown_path}", file=sys.stderr)
        return []

    with open(markdown_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find all bash code blocks: ```bash ... ```
    bash_block_pattern = re.compile(r"```bash\n(.*?)\n[ \t]*```", re.DOTALL)
    bash_blocks = bash_block_pattern.findall(content)

    placeholders = set()
    # Regex to match bracketed items like <your project id>, <my-looker-instance>
    # Avoid matching redirection or comparison syntax: check that it doesn't contain standard redirection tokens
    placeholder_pattern = re.compile(r"<([^>]+)>")

    for block in bash_blocks:
        matches = placeholder_pattern.findall(block)
        for match in matches:
            match_clean = match.strip()
            # Filter out common non-placeholder strings or comparative/redirection patterns if needed
            if match_clean and not any(char in match_clean for char in ['=', ';', '|', '&', '$']):
                placeholders.add(match_clean)

    return sorted(list(placeholders))

def main():
    parser = argparse.ArgumentParser(description="Scan markdown files for bracketed variable placeholders.")
    parser.add_argument("markdown_file", help="Path to the codelab markdown guide file.")
    parser.add_argument("--output", help="Path to write output JSON list of placeholders.")
    args = parser.parse_args()

    placeholders = scan_placeholders(args.markdown_file)

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(placeholders, f, indent=2)
        print(f"Saved {len(placeholders)} placeholders to {args.output}")
    else:
        print(json.dumps(placeholders, indent=2))

if __name__ == "__main__":
    main()
