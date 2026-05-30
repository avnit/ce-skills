#!/usr/bin/env python3
"""E2E Prompt Evaluation Script for CI/CD PR Gating and Quality Verification."""

import argparse
import json
import os
import re
import sys
import difflib

def calculate_string_similarity(str1, str2):
    """Calculates basic Levenshtein-based ratio for textual similarity."""
    if not str1 or not str2:
        return 0.0
    return difflib.SequenceMatcher(None, str1, str2).ratio()

def compute_dict_diff(dict_a, dict_b):
    """Computes exact key differences and changes between two dictionaries recursively."""
    diff = {
        "dictionary_item_added": [],
        "dictionary_item_removed": [],
        "values_changed": {}
    }
    
    def compare(a, b, path=""):
        if isinstance(a, dict) and isinstance(b, dict):
            # Added keys
            for k in b:
                if k not in a:
                    diff["dictionary_item_added"].append(f"{path}[{repr(k)}]")
                else:
                    compare(a[k], b[k], f"{path}[{repr(k)}]")
            # Removed keys
            for k in a:
                if k not in b:
                    diff["dictionary_item_removed"].append(f"{path}[{repr(k)}]")
        elif isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                diff["values_changed"][path] = {
                    "new_value": f"List of length {len(b)}",
                    "old_value": f"List of length {len(a)}"
                }
            else:
                for idx, (item_a, item_b) in enumerate(zip(a, b)):
                    compare(item_a, item_b, f"{path}[{idx}]")
        else:
            if a != b:
                diff["values_changed"][path] = {
                    "new_value": str(b),
                    "old_value": str(a)
                }
                
    compare(dict_a, dict_b)
    # Clean up empty diff categories
    return {k: v for k, v in diff.items() if v}

def calculate_trajectory_score(workspace_path):
    """Calculates Process Uptime and Trajectory score based on logs & bugs defensively."""
    try:
        if not workspace_path or not os.path.exists(workspace_path):
            return 1.0, 0, 1.0 # Default if not provided
            
        bugs_dir = os.path.join(workspace_path, "bugs")
        bugs_count = 0
        if os.path.exists(bugs_dir):
            bugs_count = len([f for f in os.listdir(bugs_dir) if f.endswith(".json")])
            
        # Calculate Efficiency: 1.0 / (1.0 + 0.2 * bugs_count)
        efficiency = 1.0 / (1.0 + 0.2 * bugs_count)
        
        # Calculate Stability (if progress.json step count is available)
        stability = 1.0
        progress_file = os.path.join(workspace_path, ".tester_state", "progress.json")
        if os.path.exists(progress_file):
            try:
                with open(progress_file, 'r') as f:
                    prog = json.load(f)
                # Mock stability check
                if bugs_count > 0:
                    stability = max(0.3, 1.0 - (0.1 * bugs_count))
            except Exception as inner_err:
                print(f"⚠️ Warning: Trajectory inner parser encountered error: {inner_err}")
                stability = 0.5 # Default penalty on malformed logs
                
        # Compliance check: Default high
        compliance = 1.0
        
        t_score = (0.3 * compliance) + (0.4 * efficiency) + (0.3 * stability)
        return t_score, bugs_count, efficiency
    except Exception as e:
        print(f"⚠️ Warning: Defensive trajectory parser triggered due to fatal file system read error: {e}")
        # Assign default penalty trajectory score on critical error instead of crashing the runner
        return 0.5, 0, 0.5

def export_markdown_report(report, md_path):
    """Exports the evaluation report as a formatted Markdown file."""
    status_emoji = "✅ PASSED" if report["status"] == "PASSED" else "❌ FAILED"
    
    md_content = f"""# Prompt Quality & Regression Evaluation Report

## Overall Status: {status_emoji}

### Metric Verdicts
| Metric | System A (Base) | System B (Workspace) | Delta | Verdict |
| :--- | :---: | :---: | :---: | :---: |
| **Quality Grade ($Q$)** | {report["system_a"]["quality"]*100:.1f}% | {report["system_b"]["quality"]*100:.1f}% | {report["delta"]["quality"]*100:+.1f}% | {report["verdicts"]["quality"]} |
| **Reliability Uptime ($R$)** | {report["system_a"]["reliability"]*100:.1f}% | {report["system_b"]["reliability"]*100:.1f}% | {report["delta"]["reliability"]*100:+.1f}% | {report["verdicts"]["reliability"]} |
| **Process Trajectory ($T_s$)** | {report["system_a"]["trajectory"]*100:.1f}% | {report["system_b"]["trajectory"]*100:.1f}% | {report["delta"]["trajectory"]*100:+.1f}% | {report["verdicts"]["trajectory"]} |
| **Uptime Efficiency** | {report["system_a"]["efficiency"]*100:.1f}% | {report["system_b"]["efficiency"]*100:.1f}% | - | - |
| **Determinism Alignment** | - | {report["system_b"]["determinism"]*100:.1f}% | - | {report["verdicts"]["determinism"]} |

---

## Structural Differences Found

"""
    if report["structural_diff"]:
        for fname, diff in report["structural_diff"].items():
            md_content += f"### File: `{fname}`\n\n"
            if "dictionary_item_added" in diff and diff["dictionary_item_added"]:
                md_content += "#### Added Properties:\n"
                for item in diff["dictionary_item_added"]:
                    md_content += f"- `{item}`\n"
                md_content += "\n"
            if "dictionary_item_removed" in diff and diff["dictionary_item_removed"]:
                md_content += "#### Removed Properties:\n"
                for item in diff["dictionary_item_removed"]:
                    md_content += f"- `{item}`\n"
                md_content += "\n"
            if "values_changed" in diff and diff["values_changed"]:
                md_content += "#### Modified Values:\n"
                for path, val in diff["values_changed"].items():
                    md_content += f"- `{path}`:\n"
                    md_content += f"  - **Old Value**: `{val['old_value']}`\n"
                    md_content += f"  - **New Value**: `{val['new_value']}`\n"
                md_content += "\n"
    else:
        md_content += "*No structural configuration drift detected between System A and System B.*\n\n"
        
    md_content += f"""---

## Execution Findings Summary
{report["summary_findings"]}

*Report generated locally inside JetSki sandbox environment.*
"""
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

def check_syntax(content, extension):
    """Validates file content syntax based on file type."""
    if not content:
        return 0.0
    
    content_stripped = content.strip()
    if extension in ['.json', 'json']:
        try:
            json.loads(content_stripped)
            return 1.0
        except json.JSONDecodeError:
            return 0.0
    elif extension in ['.yaml', '.yml', 'yaml', 'yml']:
        # Simple check: YAML shouldn't raise parser errors
        # (in a real setup we'd import PyYAML, but standard library check is safe)
        if ":" in content_stripped:
            return 1.0
        return 0.5
    elif extension in ['.md', 'md']:
        # Markdown checking (headings, formatting)
        if content_stripped.startswith("#") or "\n#" in content_stripped:
            return 1.0
        return 0.7
    return 1.0

def scan_security(content):
    """Scans output for potential security policy breaches (mocking scanner)."""
    if not content:
        return 1.0
    
    score = 1.0
    # Check for hardcoded private keys or passwords
    if re.search(r'(?i)(private_key|password|secret|passwd|auth_token)\s*[:=]\s*["\'][a-zA-Z0-9/+=]{10,}', content):
        score -= 0.4
    # Check for broad firewalls like 0.0.0.0/0 without IAP or restriction
    if "0.0.0.0/0" in content and "allow" in content.lower():
        score -= 0.3
    
    return max(0.0, score)

def parse_directory_runs(dir_path):
    """Scans staging output directory and builds execution stats."""
    files_data = {}
    failures = 0
    successes = 0
    
    if not os.path.exists(dir_path):
        return None, 0, 0
    
    for filename in sorted(os.listdir(dir_path)):
        if filename.startswith('.') or filename.endswith('.tmp'):
            continue
            
        file_path = os.path.join(dir_path, filename)
        if os.path.isdir(file_path):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Infer extension/format
            _, ext = os.path.splitext(filename)
            if not ext:
                ext = 'json' if 'json' in filename else 'txt'
                
            # Determine step reliability based on file prefix/contents
            is_fail = False
            if "fail" in filename.lower() or "error" in filename.lower():
                is_fail = True
            elif ext == '.json':
                try:
                    js = json.loads(content)
                    if js.get("status") == "FAILED" or js.get("error_logs"):
                        is_fail = True
                except:
                    pass
            
            if is_fail:
                failures += 1
            else:
                successes += 1
                
            files_data[filename] = {
                "content": content,
                "extension": ext,
                "is_failure": is_fail
            }
        except Exception as e:
            failures += 1
            files_data[filename] = {
                "content": "",
                "extension": "",
                "is_failure": True,
                "error": str(e)
            }
            
    return files_data, successes, failures

def main():
    parser = argparse.ArgumentParser(description="E2E Prompt Evaluation Gate.")
    parser.add_argument("--system-a-dir", required=True, help="Control run outputs (Base/Main).")
    parser.add_argument("--system-b-dir", required=True, help="PR/Staging run outputs (PR Branch).")
    parser.add_argument("--system-a-workspace", required=False, default=None, help="Base workspace path to count bugs/retries.")
    parser.add_argument("--system-b-workspace", required=False, default=None, help="PR workspace path to count bugs/retries.")
    parser.add_argument("--metrics-output", required=True, help="Where to save JSON metrics.")
    parser.add_argument("--fail-on-regression", type=bool, default=True, help="Should regressions block build?")
    parser.add_argument("--min-quality", type=float, default=0.95, help="Minimum Quality threshold.")
    parser.add_argument("--min-determinism", type=float, default=0.85, help="Minimum Determinism threshold.")
    
    args = parser.parse_args()
    
    print(f"🔍 Starting evaluation: System A ({args.system_a_dir}) vs System B ({args.system_b_dir})")
    
    sys_a_files, sys_a_ok, sys_a_fail = parse_directory_runs(args.system_a_dir)
    sys_b_files, sys_b_ok, sys_b_fail = parse_directory_runs(args.system_b_dir)
    
    if sys_a_files is None:
        print(f"❌ Error: Base System A directory not found: {args.system_a_dir}")
        sys.exit(1)
    if sys_b_files is None:
        print(f"❌ Error: PR System B directory not found: {args.system_b_dir}")
        sys.exit(1)
        
    # 1. Compute Reliability Rating (R)
    total_a = sys_a_ok + sys_a_fail
    total_b = sys_b_ok + sys_b_fail
    
    rel_a = sys_a_ok / total_a if total_a > 0 else 1.0
    rel_b = sys_b_ok / total_b if total_b > 0 else 1.0
    
    # 2. Compute Quality Rating (Q) per system
    def evaluate_quality(files_dict):
        if not files_dict:
            return 1.0
        
        q_scores = []
        for fname, fspec in files_dict.items():
            if fspec["is_failure"]:
                q_scores.append(0.0)
                continue
                
            # Weight structure: Syntax (30%), Security (40%), Completeness (30%)
            s_syntax = check_syntax(fspec["content"], fspec["extension"])
            s_security = scan_security(fspec["content"])
            
            # Completeness - mock: checking for typical empty content or placeholders
            s_completeness = 1.0
            if "[placeholder]" in fspec["content"].lower() or "todo" in fspec["content"].lower():
                s_completeness = 0.5
            elif len(fspec["content"].strip()) < 20:
                s_completeness = 0.2
                
            q_f = (0.3 * s_syntax) + (0.4 * s_security) + (0.3 * s_completeness)
            q_scores.append(q_f)
            
        return sum(q_scores) / len(q_scores) if q_scores else 1.0

    qual_a = evaluate_quality(sys_a_files)
    qual_b = evaluate_quality(sys_b_files)
    
    # 3. Compute exact structural differences using compute_dict_diff
    structural_diff = {}
    shared_files = set(sys_a_files.keys()).intersection(set(sys_b_files.keys()))
    
    for fname in shared_files:
        content_a = sys_a_files[fname]["content"]
        content_b = sys_b_files[fname]["content"]
        ext = sys_a_files[fname]["extension"]
        
        # Only compare JSON/YAML files structurally
        if ext in ['.json', 'json', '.yaml', '.yml', 'yaml', 'yml']:
            try:
                dict_a = json.loads(content_a)
                dict_b = json.loads(content_b)
                diff = compute_dict_diff(dict_a, dict_b)
                if diff:
                    structural_diff[fname] = diff
            except:
                # If parsing fails (e.g. not valid JSON), do a simple line-based similarity check
                cleaned_a = re.sub(r'\s+', ' ', content_a).strip()
                cleaned_b = re.sub(r'\s+', ' ', content_b).strip()
                sim = calculate_string_similarity(cleaned_a, cleaned_b)
                if sim < 1.0:
                    structural_diff[fname] = {
                        "line_similarity_drift": f"Drift detected. Cosine Textual similarity is {sim*100:.1f}%"
                    }
        else:
            # Non-structured file diff comparison
            sim = calculate_string_similarity(content_a, content_b)
            if sim < 1.0:
                structural_diff[fname] = {
                    "textual_similarity": sim
                }
                
    # Determinism Coefficient (D) represents fraction of files with zero structural drift
    total_shared = len(shared_files)
    files_with_drift = len(structural_diff)
    determinism_coef = (total_shared - files_with_drift) / total_shared if total_shared > 0 else 1.0
    
    # 4. Compute Trajectory and Process Efficiency Scores
    traj_a, bugs_a, eff_a = calculate_trajectory_score(args.system_a_workspace)
    traj_b, bugs_b, eff_b = calculate_trajectory_score(args.system_b_workspace)
    
    delta_quality = qual_b - qual_a
    delta_reliability = rel_b - rel_a
    delta_trajectory = traj_b - traj_a
    
    # 5. Determine verdicts
    verdict_quality = "PASSED" if qual_b >= args.min_quality else "FAILED"
    verdict_determinism = "PASSED" if determinism_coef >= args.min_determinism else "FAILED"
    verdict_reliability = "PASSED" if rel_b == 1.0 else "FAILED"
    verdict_trajectory = "PASSED" if delta_trajectory >= -0.15 else "FAILED" # Warn/Fail if trajectory score drops > 15%
    
    regression_gate_status = "PASSED"
    if verdict_quality == "FAILED" or verdict_reliability == "FAILED" or verdict_determinism == "FAILED" or verdict_trajectory == "FAILED":
        regression_gate_status = "FAILED"
        
    # Any drop in quality exceeding 2% or drop in reliability is blocked
    if delta_quality < -0.02:
        regression_gate_status = "FAILED"
        print(f"❌ CRITICAL REGRESSION DETECTED: Quality dropped by {abs(delta_quality)*100:.1f}%!")
        
    if delta_trajectory < -0.15:
        print(f"❌ PROCESS EFFICIENCY DEGRADED: Trajectory score dropped by {abs(delta_trajectory)*100:.1f}% due to excessive self-healing or retries.")
    
    summary_findings = ""
    if regression_gate_status == "PASSED":
        summary_findings = "Parity checks passed. System B achieves high quality and matches execution logic of System A without regression."
    else:
        summary_findings = f"System B exhibits degradations: "
        if verdict_quality == "FAILED":
            summary_findings += f"Quality rating ({qual_b*100:.1f}%) is below target ({args.min_quality*100:.1f}%). "
        if verdict_determinism == "FAILED":
            summary_findings += f"Determinism Coefficient ({determinism_coef*100:.1f}%) indicates structural config changes. "
        if verdict_reliability == "FAILED":
            summary_findings += f"Reliability rating ({rel_b*100:.1f}%) indicates new command/execution failures. "
        if verdict_trajectory == "FAILED":
            summary_findings += f"Process Trajectory ({traj_b*100:.1f}%) denotes excessive trial-and-error cycles (Bugs: {bugs_b})."

    # Compose report payload
    report = {
        "status": regression_gate_status,
        "verdicts": {
            "quality": verdict_quality,
            "determinism": verdict_determinism,
            "reliability": verdict_reliability,
            "trajectory": verdict_trajectory
        },
        "system_a": {
            "quality": qual_a,
            "reliability": rel_a,
            "success_count": sys_a_ok,
            "failure_count": sys_a_fail,
            "trajectory": traj_a,
            "bugs_count": bugs_a,
            "efficiency": eff_a
        },
        "system_b": {
            "quality": qual_b,
            "reliability": rel_b,
            "success_count": sys_b_ok,
            "failure_count": sys_b_fail,
            "determinism": determinism_coef,
            "trajectory": traj_b,
            "bugs_count": bugs_b,
            "efficiency": eff_b
        },
        "delta": {
            "quality": delta_quality,
            "reliability": delta_reliability,
            "trajectory": delta_trajectory
        },
        "structural_diff": structural_diff,
        "summary_findings": summary_findings
    }
    
    # Write to output path
    os.makedirs(os.path.dirname(args.metrics_output), exist_ok=True)
    with open(args.metrics_output, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
        
    # Export Markdown report sharing the same base path
    md_output_path = os.path.splitext(args.metrics_output)[0] + ".md"
    export_markdown_report(report, md_output_path)
        
    print("\n================ EVALUATION SUMMARY ================")
    print(f"STATUS: {regression_gate_status}")
    print(f"System A Quality: {qual_a*100:.1f}%  | System B Quality: {qual_b*100:.1f}% (Delta: {delta_quality*100:+.1f}%)")
    print(f"System A Uptime:  {rel_a*100:.1f}%  | System B Uptime:  {rel_b*100:.1f}% (Delta: {delta_reliability*100:+.1f}%)")
    print(f"System A Process: {traj_a*100:.1f}%  | System B Process: {traj_b*100:.1f}% (Delta: {delta_trajectory*100:+.1f}%)")
    print(f"System B Uptime Efficiency: {eff_b*100:.1f}% (Bugs Triggered: {bugs_b})")
    print(f"Determinism Alignment Coef: {determinism_coef*100:.1f}% (Target: {args.min_determinism*100:.1f}%)")
    if structural_diff:
        print("\nStructural Differences Found:")
        print(json.dumps(structural_diff, indent=2))
    print(f"\nReport saved to: {args.metrics_output}")
    print("====================================================")
    
    if regression_gate_status != "PASSED" and args.fail_on_regression:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
