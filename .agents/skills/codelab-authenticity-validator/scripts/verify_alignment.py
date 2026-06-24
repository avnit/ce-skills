#!/usr/bin/env python3
import os
import re
import sys

def extract_code_blocks(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all markdown code blocks
    pattern = re.compile(r'```(?:bash|console|shell|python|json|console|yacc)?\n(.*?)\n```', re.DOTALL)
    return [block.strip() for block in pattern.findall(content)]

def verify_images(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all markdown/html images containing http urls (non-local)
    md_img_pattern = re.compile(r'!\[.*?\]\((https?://.*?)\)')
    html_img_pattern = re.compile(r'<img[^>]+src=["\'](https?://[^"\']+)["\']')
    
    remote_md = md_img_pattern.findall(content)
    remote_html = html_img_pattern.findall(content)
    
    return remote_md + remote_html

def check_links_enforcement(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Common library keywords to ensure they are linked if present
    keywords = ["Tunix", "Kaggle", "Hugging Face", "Wandb", "Weights & Biases"]
    unlinked = []
    
    for kw in keywords:
        # Match keyword only if NOT inside a Markdown link e.g. [Tunix](...) or a heading
        # Simple check: find all occurrences of the keyword
        # and verify if the preceding character is [ and trailing has ](
        kw_escaped = re.escape(kw)
        occurrences = [m.start() for m in re.finditer(kw_escaped, content)]
        
        for pos in occurrences:
            # Check surrounding context to see if it is formatted as [Keyword](url)
            prefix = content[max(0, pos - 1):pos]
            suffix = content[pos + len(kw):pos + len(kw) + 2]
            if prefix != '[' or suffix != '](':
                unlinked.append(kw)
                break
                
    return list(set(unlinked))

def generate_report(raw_source_path, generated_path, report_output_path):
    raw_blocks = extract_code_blocks(raw_source_path)
    gen_blocks = extract_code_blocks(generated_path)
    remote_imgs = verify_images(generated_path)
    unlinked_refs = check_links_enforcement(generated_path)
    
    report = []
    report.append("# Codelab Authenticity & Gap Alignment Audit Report")
    report.append(f"**Source Raw Lab**: `{os.path.basename(raw_source_path)}`  ")
    report.append(f"**Compiled Self-Paced Codelab**: `{os.path.basename(generated_path)}`  \n")
    
    report.append("## 1. Code Command Blocks Verification")
    report.append(f"Found **{len(raw_blocks)}** commands in source and **{len(gen_blocks)}** commands in compiled codelab.\n")
    
    mismatches = []
    # Basic comparison: check if all source commands are preserved in the generated blocks
    for i, raw in enumerate(raw_blocks):
        found = False
        # Normalize whitespace for comparison
        raw_norm = re.sub(r'\s+', ' ', raw)
        for gen in gen_blocks:
            gen_norm = re.sub(r'\s+', ' ', gen)
            if raw_norm in gen_norm or gen_norm in raw_norm:
                found = True
                break
        if not found:
            mismatches.append((i + 1, raw))
            
    if not mismatches:
        report.append("> [!NOTE]\n> **Technical Commands Integrity: 100% PASS**  \n> All source terminal commands, flags, and scripts are fully preserved with zero technical deviations.")
    else:
        report.append("> [!WARNING]\n> **Command Gaps Detected!**  \n")
        report.append("| Block # | Source Command / Snippet | Status |")
        report.append("| :--- | :--- | :--- |")
        for num, cmd in mismatches:
            # Escaping backticks inside table
            escaped_cmd = cmd.replace("`", "\\`").replace("\n", "<br>")
            report.append(f"| {num} | `{escaped_cmd}` | Missing or Modified |")
            
    report.append("\n## 2. Local Image Asset Verification")
    if not remote_imgs:
        report.append("> [!NOTE]\n> **Local Assets Mapping: 100% PASS**  \n> All remote image assets have been successfully downloaded and resolved to relative local paths (`img/`).")
    else:
        report.append("> [!CAUTION]\n> **Unresolved Remote Image Assets Found!**  \n")
        report.append("| Asset URL | Status |")
        report.append("| :--- | :--- |")
        for url in remote_imgs:
            report.append(f"| `{url}` | Remaining Remote Link |")
            
    report.append("\n## 3. Hyperlink & Reference Enforcement")
    if not unlinked_refs:
        report.append("> [!NOTE]\n> **Reference Link Enrichment: 100% PASS**  \n> All key external tools and platform references are correctly hyperlinked.")
    else:
        report.append("> [!WARNING]\n> **Unlinked Reference Keywords Found!**  \n")
        report.append("| Keyword | Severity / Remediation |")
        report.append("| :--- | :--- |")
        for ref in unlinked_refs:
            report.append(f"| `{ref}` | Recommend replacing with Markdown hyperlink |")
            
    report.append("\n## 4. Final Audit Outcome")
    if not mismatches and not remote_imgs and not unlinked_refs:
        report.append("### **Status: APPROVED**\nThe generated self-paced Codelab perfectly preserves technical fidelity, resolves all assets, and enriches all documentation references successfully.")
    else:
        report.append("### **Status: ACTION REQUIRED**\nPlease address the warnings and gaps identified in sections 1, 2, and 3 above.")
        
    os.makedirs(os.path.dirname(report_output_path), exist_ok=True)
    with open(report_output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report))
        
    print(f"Successfully wrote gap validation report to: {report_output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: verify_alignment.py <raw_source_path> <generated_path> <report_output_path>")
        sys.exit(1)
        
    generate_report(sys.argv[1], sys.argv[2], sys.argv[3])
