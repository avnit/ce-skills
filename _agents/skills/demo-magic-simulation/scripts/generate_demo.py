#!/usr/bin/env python3
import os
import sys
import argparse
import re
from pathlib import Path

DEMO_MAGIC_ENGINE = r"""#!/usr/bin/env bash
###############################################################################
# Generated Demo-Magic Presentation Script
# Compiles codelab instructions into interactive humanized typing flows.
###############################################################################

# Configuration
TYPE_SPEED={speed}
DEMO_PROMPT="{prompt}"

# Core System Parameters & Variables
# Automatically resolves to active Google Cloud Shell project context if set
PROJECT_ID=${{PROJECT_ID:-$GOOGLE_CLOUD_PROJECT}}
REGION=${{REGION:-"{region}"}}
ZONE=${{ZONE:-"{zone}"}}
{custom_vars_block}

DEMO_CMD_COLOR="\033[1;36m"      # Bold Cyan
DEMO_COMMENT_COLOR="\033[0;90m" # Grey
COLOR_RESET="\033[0m"

function wait_for_enter() {{
  read -rs
}}

function simulate_typing() {{
  local text="$1"
  local color="$2"
  local len=${{#text}}
  
  local delay=0.05
  if [[ "$TYPE_SPEED" -gt 0 ]]; then
    if [[ "$TYPE_SPEED" -ge 40 ]]; then delay=0.02
    elif [[ "$TYPE_SPEED" -ge 30 ]]; then delay=0.03
    elif [[ "$TYPE_SPEED" -ge 25 ]]; then delay=0.04
    elif [[ "$TYPE_SPEED" -ge 20 ]]; then delay=0.05
    elif [[ "$TYPE_SPEED" -ge 15 ]]; then delay=0.06
    elif [[ "$TYPE_SPEED" -ge 10 ]]; then delay=0.10
    else delay=0.15
    fi
  else
    delay=0
  fi

  for (( i=0; i<len; i++ )); do
    echo -ne "${{color}}${{text:$i:1}}${{COLOR_RESET}}"
    if [[ "$delay" != "0" ]]; then
      sleep "$delay"
    fi
  done
}}

function pe() {{
  local cmd="$1"
  echo -ne "${{DEMO_PROMPT}}"
  simulate_typing "$cmd" "${{DEMO_CMD_COLOR}}"
  wait_for_enter
  echo ""
  eval "$cmd"
  echo ""
}}

function p() {{
  local cmd="$1"
  echo -ne "${{DEMO_PROMPT}}"
  simulate_typing "$cmd" "${{DEMO_COMMENT_COLOR}}"
  wait_for_enter
  echo ""
}}

# Clear screen at start for pristine presentation canvas
clear
echo -e "${{DEMO_COMMENT_COLOR}}# Starting interactive demonstration session...${{COLOR_RESET}}\n"
"""

def normalize_command_variables(cmd_text: str) -> str:
    """Normalize typical textual prose placeholders into standard environment variables."""
    res = re.sub(r'<PROJECT_ID>', '$PROJECT_ID', cmd_text, flags=re.IGNORECASE)
    res = re.sub(r'\[PROJECT_ID\]', '$PROJECT_ID', res, flags=re.IGNORECASE)
    res = re.sub(r'\bYOUR_PROJECT_ID\b', '$PROJECT_ID', res, flags=re.IGNORECASE)
    
    res = re.sub(r'<REGION>', '$REGION', res, flags=re.IGNORECASE)
    res = re.sub(r'\[REGION\]', '$REGION', res, flags=re.IGNORECASE)
    res = re.sub(r'\bYOUR_REGION\b', '$REGION', res, flags=re.IGNORECASE)
    
    res = re.sub(r'<ZONE>', '$ZONE', res, flags=re.IGNORECASE)
    res = re.sub(r'\[ZONE\]', '$ZONE', res, flags=re.IGNORECASE)
    res = re.sub(r'\bYOUR_ZONE\b', '$ZONE', res, flags=re.IGNORECASE)
    return res

def parse_codelab(lab_path: Path, output_path: Path, speed: int, prompt: str, region: str, zone: str, extra_vars: list):
    content = lab_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    
    negative_signatures = [
        r"Output:", r"Credentialed accounts:", r"ACTIVE", r"STATUS", 
        r"Created [a-zA-Z0-9]", r"Updated [a-zA-Z0-9]",
        r"^\d+\.\d+\.\d+\.\d+"  # Matches blocks starting with standalone IP addresses (sample outputs)
    ]
    
    script_instructions = []
    
    in_code_block = False
    skip_current_section = False
    code_block_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        
        # Check if it's a markdown header outside of a code block
        if not in_code_block and line_stripped.startswith('#'):
            header_text = line_stripped.lstrip('#').strip()
            # Check if header indicates cleanup or deletion
            if re.search(r'\b(clean\s*up|cleanup|delete|dismantle)\b', header_text, re.IGNORECASE):
                skip_current_section = True
            else:
                skip_current_section = False
                
        # Check for fenced code block boundaries
        if line_stripped.startswith('```'):
            if not in_code_block:
                # Starting a fenced block
                lang = line_stripped.lstrip('```').strip()
                if lang in ('bash', 'console'):
                    in_code_block = True
                    code_block_lines = []
            else:
                # Ending the active fenced block
                in_code_block = False
                if skip_current_section:
                    # Completely discard blocks found inside cleanup/deletion sections!
                    code_block_lines = []
                    continue
                    
                block_text = "\n".join(code_block_lines)
                clean_block = block_text.strip()
                
                # Negative filtering check
                is_output = False
                for sig in negative_signatures:
                    if re.search(sig, clean_block, re.IGNORECASE):
                        is_output = True
                        break
                        
                if not is_output and clean_block:
                    # Process commands inside block
                    block_lines = clean_block.split('\n')
                    current_cmd = []
                    
                    for bline in block_lines:
                        bline_str = bline.strip()
                        if not bline_str:
                            continue
                        if bline_str.startswith('#'):
                            if current_cmd:
                                cmd_text = " ".join(current_cmd).replace('"', '\\"')
                                cmd_text = normalize_command_variables(cmd_text)
                                script_instructions.append(f'pe "{cmd_text}"')
                                current_cmd = []
                            safe_comment = bline_str.replace('"', '\\"')
                            script_instructions.append(f'p "{safe_comment}"')
                        elif bline_str.endswith('\\'):
                            current_cmd.append(bline_str[:-1].strip())
                        else:
                            current_cmd.append(bline_str)
                            cmd_text = " ".join(current_cmd).replace('"', '\\"')
                            cmd_text = normalize_command_variables(cmd_text)
                            script_instructions.append(f'pe "{cmd_text}"')
                            current_cmd = []
                            
                    if current_cmd:
                        cmd_text = " ".join(current_cmd).replace('"', '\\"')
                        cmd_text = normalize_command_variables(cmd_text)
                        script_instructions.append(f'pe "{cmd_text}"')
                        
                code_block_lines = []
        elif in_code_block:
            code_block_lines.append(line)
            
    # Build custom vars block string
    custom_vars_list = []
    for var_pair in extra_vars:
        if "=" in var_pair:
            k, v = var_pair.split("=", 1)
            k_clean = k.strip()
            v_clean = v.strip().replace('"', '\\"')
            custom_vars_list.append(f"{k_clean}=${{{k_clean}:-\"{v_clean}\"}}")
            
    custom_vars_block = "\n".join(custom_vars_list)
    
    # Compile full output script
    header = DEMO_MAGIC_ENGINE.format(
        speed=speed, 
        prompt=prompt.replace('"', '\\"'),
        region=region.replace('"', '\\"'),
        zone=zone.replace('"', '\\"'),
        custom_vars_block=custom_vars_block
    )
    body = "\n".join(script_instructions)
    
    full_script = f"{header}\n{body}\n\necho -e \"${{DEMO_COMMENT_COLOR}}# Demonstration complete.${{COLOR_RESET}}\"\n"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(full_script, encoding="utf-8")
    
    # Make executable directly via chmod
    try:
        output_path.chmod(0o755)
    except Exception as e:
        pass
        
    # Compile secondary side-by-side Cloud Shell copy-paste launcher block inside the same demo folder
    target_script_name = output_path.name
    launcher_path = output_path.parent / f"{output_path.stem}_cloudshell_launcher.sh"
    
    launcher_content = f"""cat << 'EOF' > {target_script_name}
{full_script}EOF
chmod +x {target_script_name}
./{target_script_name}
"""
    launcher_path.write_text(launcher_content, encoding="utf-8")
    
    print(f"Successfully generated standalone demonstration script: {output_path}")
    print(f"Successfully generated Cloud Shell copy-paste launcher: {launcher_path}")

def main():
    parser = argparse.ArgumentParser(description="Compile Codelab instructions into embedded demo-magic presentation scripts.")
    parser.add_argument("--lab", required=True, type=Path, help="Path to source .lab.md file.")
    parser.add_argument("--output", type=Path, help="Custom destination path for output bash script.")
    parser.add_argument("--speed", type=int, default=20, help="Simulated typing speed (characters per second).")
    parser.add_argument("--prompt", type=str, default="$ ", help="Terminal prompt prefix string.")
    parser.add_argument("--region", type=str, default="us-central1", help="Default GCP region parameter.")
    parser.add_argument("--zone", type=str, default="us-central1-a", help="Default GCP zone parameter.")
    parser.add_argument("--vars", nargs="*", default=[], help="Additional system parameter overrides in KEY=VALUE format.")
    
    args = parser.parse_args()
    
    if not args.lab.exists():
        print(f"Error: Source lab file not found: {args.lab}", file=sys.stderr)
        sys.exit(1)
        
    output = args.output
    if not output:
        base = args.lab.stem
        if base.endswith('.lab'):
            base = base[:-4]
        # Save inside a dedicated demo/ subfolder directly under the lab directory
        output = args.lab.parent / "demo" / f"{base}_demo.sh"
        
    parse_codelab(args.lab, output, args.speed, args.prompt, args.region, args.zone, args.vars)

if __name__ == "__main__":
    main()
