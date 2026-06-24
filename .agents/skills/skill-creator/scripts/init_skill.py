#!/usr/bin/env python3
import argparse
import os
import sys

def to_snake_case(name):
    return name.lower().replace("-", "_")

def create_skill(skill_name):
    # Standard validation: name should be kebab-case
    if not all(c.isalnum() or c == '-' for c in skill_name):
        print("❌ Error: Skill name must be in kebab-case (e.g., 'my-new-skill').", file=sys.stderr)
        sys.exit(1)
        
    dir_name = to_snake_case(skill_name)
    
    # Dynamically resolve repository root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(script_dir, "../../../.."))
    skills_root = os.path.join(repo_root, ".agents/skills")
    
    skill_dir = os.path.join(skills_root, dir_name)
    if os.path.exists(skill_dir):
        print(f"❌ Error: A skill directory already exists at [{skill_dir}].", file=sys.stderr)
        sys.exit(1)
        
    # Create structural folders
    os.makedirs(os.path.join(skill_dir, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(skill_dir, "references"), exist_ok=True)
    os.makedirs(os.path.join(skill_dir, "assets"), exist_ok=True)
    
    # Pre-populate SKILL.md
    skill_md_content = f"""---
name: {skill_name}
description: >-
  [Provide a third-person capability statement. Use terms the LLM knows. 
  Describe what a user would be trying to do. List triggers using "Use when..." 
  Keep under 1024 characters.]
---

# Skill: [Human-Readable Skill Title]

[A short, terse cheatsheet overview. Senior engineer's notes: "do this, not that" and "watch out for X". Keep it under 500 lines.]

## Execution Guide

Run the main utility directly inside your Cloudtop terminal:
```bash
python3 .agents/skills/{dir_name}/scripts/your_script.py --arg value
```

***

## CLI Parameters

*   `--param`: (Type, default/required) [Describe argument]

***

## 🔗 Inter-Skill Programmatic Integration

Other skills or scripts can import the API natively:

```python
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[3] # Dynamically resolve root
sys.path.append(str(repo_root / '.agents/skills/{dir_name}/scripts'))
from your_script import your_api_function
```
"""
    
    with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(skill_md_content)
        
    print(f"🚀 Success! Pre-populated skill directory initialized at:")
    print(f"   {skill_dir}/")
    print(f"   ├── SKILL.md")
    print(f"   ├── scripts/")
    print(f"   ├── references/")
    print(f"   └── assets/")

def main():
    parser = argparse.ArgumentParser(description="Initialize a clean, pre-populated skill directory under .agents/skills/")
    parser.add_argument("--name", required=True, help="Name of the new skill in kebab-case (e.g., 'rotate-pdfs').")
    args = parser.parse_args()
    
    create_skill(args.name)

if __name__ == "__main__":
    main()
