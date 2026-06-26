#!/usr/bin/env python3
"""
g3doc Markdown Formatter Script
Transforms standard Markdown and Codelab files into strict g3doc/G3Mark compliance.
Insects freshness headers, TOC macros, and converts GitHub alerts to bold G3Mark callouts.
"""

import argparse
import datetime
import os
import re
import sys

ALERT_MAPPINGS = {
    r">\s*\[!NOTE\]": "> **Note:**",
    r">\s*\[!TIP\]": "> **Tip:**",
    r">\s*\[!WARNING\]": "> **Warning:**",
    r">\s*\[!IMPORTANT\]": "> **Important:**",
    r">\s*\[!CAUTION\]": "> **Caution:**",
}

def format_content(content: str, owner: str) -> str:
    lines = content.splitlines()
    formatted_lines = []
    
    # 1. Convert GitHub Alerts to G3Mark Callouts
    for line in lines:
        new_line = line
        for pattern, replacement in ALERT_MAPPINGS.items():
            new_line = re.sub(pattern, replacement, new_line, flags=re.IGNORECASE)
        formatted_lines.append(new_line)
        
    full_text = "\n".join(formatted_lines)
    
    # 2. Check & Inject Freshness Tag and TOC
    has_freshness = "<!--* freshness:" in full_text
    has_toc = "[TOC]" in full_text
    
    if not has_freshness or not has_toc:
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        freshness_tag = f"<!--* freshness: {{ owner: '{owner}' reviewed: '{today_str}' }} *-->"
        
        insert_block = []
        if not has_freshness:
            insert_block.append("")
            insert_block.append(freshness_tag)
        if not has_toc:
            insert_block.append("")
            insert_block.append("[TOC]")
        insert_str = "\n".join(insert_block) + "\n"
        
        # Locate first H1 header (# Title)
        h1_match = re.search(r"^#\s+.+", full_text, flags=re.MULTILINE)
        if h1_match:
            end_pos = h1_match.end()
            full_text = full_text[:end_pos] + insert_str + full_text[end_pos:]
        else:
            full_text = insert_str.lstrip() + full_text
            
    return full_text

def main():
    parser = argparse.ArgumentParser(description="g3doc Markdown Formatter")
    parser.add_argument("--file", required=True, help="Path to markdown file")
    parser.add_argument("--owner", required=True, help="Owner LDAP or team name")
    parser.add_argument("--in-place", action="store_true", help="Modify file in place")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found.", file=sys.stderr)
        sys.exit(1)
        
    with open(args.file, "r", encoding="utf-8") as f:
        content = f.read()
        
    formatted = format_content(content, args.owner)
    
    if args.in_place:
        with open(args.file, "w", encoding="utf-8") as f:
            f.write(formatted)
        print(f"✅ Successfully formatted '{args.file}' in place for g3doc.")
    else:
        print(formatted)

if __name__ == "__main__":
    main()
