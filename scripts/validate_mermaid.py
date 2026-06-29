#!/usr/bin/env python3
import re
import sys
import os
import tempfile
import subprocess

def validate_mermaid_syntax(markdown_path):
    """Parses a markdown file, extracts Mermaid code blocks, and validates syntax rules and CLI rendering."""
    if not os.path.exists(markdown_path):
        print(f"Error: File not found: {markdown_path}")
        return False

    with open(markdown_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract all mermaid code blocks
    mermaid_blocks = re.findall(r'```mermaid\s*([\s\S]*?)```', content)
    
    if not mermaid_blocks:
        print("No Mermaid blocks found to validate.")
        return True

    has_errors = False

    for idx, block in enumerate(mermaid_blocks):
        lines = block.strip().split('\n')
        print(f"\nChecking Mermaid block #{idx + 1}...")
        
        # Perform regex rules first (as rapid local checks)
        for line_num, line in enumerate(lines, 1):
            line_str = line.strip()
            if not line_str or line_str.startswith('%%'):
                continue

            # Rule 1: Detect invalid bidirectional arrows like <--> or <==>
            if '<-->' in line_str or '<==>' in line_str:
                print(f"  [REGEX ERROR] Line {line_num}: Invalid bidirectional arrow '<-->' or '<==>'. Use standard link connections ('---', '-->', '==>') instead.")
                has_errors = True

            # Rule 2: Detect raw parentheses inside subgraph declarations
            if line_str.startswith('subgraph'):
                if '(' in line_str or ')' in line_str:
                    if '"' not in line_str and '[' not in line_str:
                        print(f"  [REGEX ERROR] Line {line_num}: Raw parentheses in subgraph title. Use double quotes or explicit labels: `subgraph id [\"Title (Detail)\"]`.")
                        has_errors = True

            # Rule 3: Detect raw parentheses in node assignments without quotes
            if '(' in line_str or ')' in line_str or '[' in line_str or ']' in line_str:
                if ('(' in line_str and '"' not in line_str) or ('[' in line_str and '"' not in line_str and ']' in line_str and ('(' in line_str or ')' in line_str)):
                    print(f"  [REGEX ERROR] Line {line_num}: Raw parentheses or special characters in node label. Ensure labels with spaces or parentheses are double-quoted: `node_id[\"Label (Detail)\"]`.")
                    has_errors = True

        # Perform official mmdc CLI compilation check
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as temp_in:
            temp_in.write(block)
            temp_in_path = temp_in.name

        temp_out_path = temp_in_path + '.png'
        
        try:
            # Execute the Mermaid CLI via npx
            cmd = ["npx", "-y", "@mermaid-js/mermaid-cli", "-i", temp_in_path, "-o", temp_out_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"  [CLI ERROR] Compilation failed for block #{idx + 1}:")
                stderr_lines = result.stderr.strip().split('\n')
                for err_line in stderr_lines:
                    if err_line.strip():
                        print(f"    {err_line}")
                has_errors = True
            else:
                print("  [CLI SUCCESS] Rendered successfully to a temporary PNG.")
                
        except Exception as e:
            print(f"  [CLI ERROR] Failed to execute mmdc validator: {e}")
            has_errors = True
        finally:
            # Cleanup temp files
            if os.path.exists(temp_in_path):
                os.remove(temp_in_path)
            if os.path.exists(temp_out_path):
                os.remove(temp_out_path)

    if has_errors:
        print("\n❌ Mermaid validation failed with syntax/compilation errors.")
        return False
    
    print("\n✅ All Mermaid blocks passed pre-delivery and compiler validation successfully.")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 validate_mermaid.py <path_to_markdown_file>")
        sys.exit(1)
    
    success = validate_mermaid_syntax(sys.argv[1])
    sys.exit(0 if success else 1)
