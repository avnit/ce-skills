#!/usr/bin/env python3
"""Phase 3.5 Pre-Flight Code Audit Gate for Codelab Validation."""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Tuple

# Resolve script directory and append to sys.path for modular imports
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_script_dir)

from codelab_parser import (  # noqa: E402
    _extract_command_blocks as _extract_command_blocks,
    classify_block as classify_block,
)


def scan_unresolved_placeholders(
    unit: str, variables: Dict[str, Any] | None = None
) -> List[str]:
    """Scans execution unit for bracketed <...> placeholders not satisfied by variables."""
    placeholder_pattern = re.compile(r"(?<!<)<([A-Za-z0-9_][A-Za-z0-9_ -]*)>")
    matches = placeholder_pattern.findall(unit)

    var_keys = set()
    if variables:
        for k in variables.keys():
            var_keys.add(k)
            var_keys.add(k.strip("<>"))

    unresolved = []
    for match in matches:
        match_clean = match.strip()
        if not match_clean:
            continue
        # Filter out bash operators, assignments, or comparisons
        if any(char in match_clean for char in ["=", ";", "|", "&", "$", "/"]):
            continue
        if match_clean in var_keys or f"<{match_clean}>" in var_keys:
            continue
        if match_clean not in unresolved:
            unresolved.append(match_clean)

    return unresolved


def check_syntax(unit: str) -> Tuple[bool, str]:
    """Runs bash -n on the execution unit to check for syntax errors."""
    try:
        res = subprocess.run(
            ["bash", "-n"],
            input=unit,
            text=True,
            capture_output=True,
            check=False,
        )
        if res.returncode == 0:
            return True, ""
        return False, res.stderr.strip() or "Syntax error detected by bash -n"
    except Exception as e:
        return False, f"Failed to execute bash -n: {e}"


def check_interactive_traps(unit: str) -> List[str]:
    """Checks execution unit for interactive traps and anti-patterns."""
    warnings = []
    unit_lower = unit.lower()

    # Trap 1: gcloud auth login / ADC login
    if (
        "gcloud auth login" in unit_lower
        or "gcloud auth application-default login" in unit_lower
        or "adc login" in unit_lower
    ):
        warnings.append(
            "Interactive authentication prompt detected (`gcloud auth login` / `ADC login`). "
            "Automated runs require non-interactive service account or environment credentials."
        )

    # Trap 2: gcloud compute ssh without --command
    if "gcloud compute ssh" in unit_lower and "--command" not in unit_lower:
        warnings.append(
            "Interactive SSH session (`gcloud compute ssh` without `--command`). "
            "Non-interactive subshell execution will hang waiting for terminal interaction."
        )

    # Trap 3: VM / Template creation without explicit image flags (Gotcha #2)
    if (
        "gcloud compute instances create" in unit_lower
        or "gcloud compute instance-templates create" in unit_lower
    ):
        has_family = "--image-family" in unit_lower
        has_project = "--image-project" in unit_lower
        has_image = "--image" in unit_lower or "--image=" in unit_lower
        if not ((has_family and has_project) or has_image):
            warnings.append(
                "VM/Template creation missing explicit `--image-family` and `--image-project` (or `--image`) flags. "
                "Default image families may drift or require interactive prompts (Gotcha #2)."
            )

    # Trap 4: sudo usage
    if re.search(r"\bsudo\b", unit):
        warnings.append(
            "Interactive `sudo` prompt detected. Requires non-interactive privilege escalation or passwordless sudo."
        )

    return warnings


def extract_gcloud_group_paths(unit: str) -> List[List[str]]:
    """Extracts gcloud subcommand group paths from the unit."""
    groups = []
    lines = unit.splitlines()
    for line in lines:
        line_clean = line.strip()
        if not line_clean or line_clean.startswith("#"):
            continue
        parts = line_clean.split()
        for i, word in enumerate(parts):
            if word == "gcloud":
                cmd_tokens = []
                for token in parts[i + 1 :]:
                    if token.startswith("-") or any(
                        c in token for c in ["=", ";", "|", "&", "$", "<", ">"]
                    ):
                        break
                    cmd_tokens.append(token)
                if cmd_tokens:
                    groups.append(cmd_tokens)
    return groups


def check_gcloud_surface(unit: str, timeout: int = 10) -> List[Tuple[str, str]]:
    """Checks gcloud command group validity via dry-run gcloud <group> --help."""
    failures = []
    group_paths = extract_gcloud_group_paths(unit)
    for tokens in group_paths:
        cmd = ["gcloud"] + tokens + ["--help"]
        try:
            res = subprocess.run(
                cmd,
                timeout=timeout,
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode != 0:
                group_str = " ".join(["gcloud"] + tokens)
                err_msg = res.stderr.strip() or "Unknown or deprecated gcloud command group"
                failures.append((group_str, err_msg))
        except subprocess.TimeoutExpired:
            group_str = " ".join(["gcloud"] + tokens)
            failures.append((group_str, "Command help check timed out after 10s"))
        except Exception as e:
            group_str = " ".join(["gcloud"] + tokens)
            failures.append((group_str, f"Execution failed: {e}"))
    return failures


def audit_codelab(
    markdown_path: str,
    variables_path: str | None = None,
    check_gcloud: bool = False,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Audits codelab markdown file execution units."""
    if not os.path.exists(markdown_path):
        raise FileNotFoundError(f"Codelab file not found: {markdown_path}")

    if check_gcloud and not shutil.which("gcloud"):
        raise RuntimeError(
            "Surface check requested (--check-gcloud-surface), but 'gcloud' binary was not found on PATH."
        )

    variables = None
    if variables_path:
        if not os.path.exists(variables_path):
            raise FileNotFoundError(f"Variables file not found: {variables_path}")
        with open(variables_path, "r", encoding="utf-8") as f:
            variables = json.load(f)

    with open(markdown_path, "r", encoding="utf-8") as f:
        body = f.read()

    blocks = _extract_command_blocks(body)
    unit_reports = []
    unit_index = 0

    pass_count = 0
    warn_count = 0
    fail_count = 0

    for block in blocks:
        tier, units = classify_block(block)
        for unit in units:
            unit_index += 1
            unit_fails = []
            unit_warns = []

            # Substitute resolved variables into eval_unit for syntax/traps evaluation
            eval_unit = unit
            if variables:
                for k, v in variables.items():
                    raw_k = k.strip("<>")
                    eval_unit = eval_unit.replace(f"<{raw_k}>", str(v))

            # Check 1: Syntax (bash -n)
            syntax_ok, syntax_err = check_syntax(eval_unit)
            if not syntax_ok:
                unit_fails.append(f"Syntax Error: {syntax_err}")

            # Check 2: Placeholders
            unresolved = scan_unresolved_placeholders(unit, variables)
            if unresolved:
                unit_fails.append(
                    f"Unresolved Placeholder(s): {', '.join(['<' + p + '>' for p in unresolved])}"
                )

            # Check 3: Traps
            traps = check_interactive_traps(eval_unit)
            if traps:
                unit_warns.extend(traps)

            # Check 4: Gcloud Surface (if opt-in)
            if check_gcloud:
                surface_errs = check_gcloud_surface(eval_unit)
                for grp, err in surface_errs:
                    unit_fails.append(f"Gcloud Surface Error ({grp}): {err}")

            if unit_fails:
                status = "FAIL"
                fail_count += 1
            elif unit_warns:
                status = "WARN"
                warn_count += 1
            else:
                status = "PASS"
                pass_count += 1

            details = []
            if unit_fails:
                details.extend([f"❌ {f}" for f in unit_fails])
            if unit_warns:
                details.extend([f"⚠️ {w}" for w in unit_warns])
            if not details:
                details.append("Clean execution unit")

            unit_reports.append(
                {
                    "index": unit_index,
                    "tier": tier,
                    "unit": unit,
                    "status": status,
                    "details": details,
                }
            )

    verdict = "PASS" if fail_count == 0 else "FAIL"
    summary = {
        "file": markdown_path,
        "total_units": unit_index,
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "verdict": verdict,
    }

    return summary, unit_reports


def generate_report_markdown(
    summary: Dict[str, Any], unit_reports: List[Dict[str, Any]]
) -> str:
    """Generates markdown report string for audit findings."""
    lines = []
    lines.append("# Phase 3.5 Pre-Flight Code Audit Report")
    lines.append("")
    lines.append(f"- **Target Codelab**: `{summary['file']}`")
    lines.append(f"- **Overall Verdict**: **`{summary['verdict']}`**")
    lines.append(
        f"- **Summary**: Total Units: {summary['total_units']} | "
        f"PASS: {summary['pass_count']} | WARN: {summary['warn_count']} | FAIL: {summary['fail_count']}"
    )
    lines.append("")
    lines.append("## Execution Units Audit Table")
    lines.append("")
    lines.append("| Unit # | Tier | Status | Details & Findings |")
    lines.append("|:---:|:---:|:---:|---|")

    for u in unit_reports:
        snippet = u["unit"].replace("\n", " ")
        if len(snippet) > 60:
            snippet = snippet[:57] + "..."
        snippet_escaped = snippet.replace("|", "\\|")
        details_str = "<br>".join(u["details"]).replace("|", "\\|")
        lines.append(
            f"| {u['index']} | `{u['tier']}` | **`{u['status']}`** | `{snippet_escaped}`<br>{details_str} |"
        )

    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Phase 3.5 Pre-Flight Code Audit Gate for Codelab Validation."
    )
    parser.add_argument(
        "markdown_file", help="Path to the codelab markdown file (.lab.md)"
    )
    parser.add_argument(
        "--variables",
        help="Optional path to variables.json file for placeholder resolution",
    )
    parser.add_argument(
        "--report", help="Optional output path to write markdown report"
    )
    parser.add_argument(
        "--check-gcloud-surface",
        action="store_true",
        help="Opt-in runtime check for gcloud command group validity",
    )

    args = parser.parse_args()

    try:
        summary, unit_reports = audit_codelab(
            args.markdown_file,
            variables_path=args.variables,
            check_gcloud=args.check_gcloud_surface,
        )
    except Exception as e:
        print(f"Error during pre-flight audit: {e}", file=sys.stderr)
        sys.exit(1)

    report_md = generate_report_markdown(summary, unit_reports)

    if args.report:
        report_dir = os.path.dirname(os.path.abspath(args.report))
        if report_dir:
            os.makedirs(report_dir, exist_ok=True)
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(report_md)
        print(f"Pre-flight audit report saved to: {args.report}")

    print(report_md)

    if summary["verdict"] == "FAIL":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
