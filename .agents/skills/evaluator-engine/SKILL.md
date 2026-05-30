---
name: evaluator-engine
description: >
  Performs E2E Prompt Quality, Determinism, and Reliability Evaluation across twin execution pipelines. 
  Ingests output files and logs from two staging system runs, computes differential scoring metrics, 
  and generates standard JSON/Markdown regression reports for CI/CD gating.
---

# Prompt Evaluation Engine

This skill provides tools and instructions to automatically run, score, and gate generative prompt execution behaviors. It acts as a quality check and regression detector inside the pull-request pipeline.

## Unified Scoring & Validation

You **MUST** invoke the unified `evaluator.py` script to evaluate the output of any golden prompt executions. It parses structured outputs, executes syntax/security lints, computes logical & textual similarity vectors, and produces a deterministic regression verdict.

### How to Run

```bash
python3 .agents/skills/evaluator-engine/scripts/evaluator.py \
  --system-a-dir="/path/to/staging_a_outputs" \
  --system-b-dir="/path/to/staging_b_outputs" \
  --metrics-output="/path/to/workspace/doc/eval_report.json" \
  --fail-on-regression=true \
  --min-quality=0.95 \
  --min-determinism=0.85
```

## Differential Scoring Formulas

The skill evaluates execution along three parallel tracks:

1. **Quality Rating ($Q$)**: Checks syntactic validity (JSON/YAML parsing), architectural security constraints, and compliance to core templates.
2. **Determinism Coefficient ($D$)**: Calculates AST (Abstract Syntax Tree) structural similarity and cosine embedding distances to measure drift.
3. **Execution Uptime ($R$)**: Measures step-level reliability (fails vs successes).

## Output Schema

The script writes a structured JSON output to the path specified in `--metrics-output`. The CI/CD system reads this output to print pull request reviews and dynamically block unsafe code merges.

## Operational Rules

1. **Identical Staging Context**: Ensure the control (System A) and variable (System B) directories share identical prompt suites and step-file counts.
2. **Strict Verification Limits**: Failures in provisioning or execution immediately reduce the Uptime Rating ($R$) to `< 100%`, triggering an automated CI block.
3. **Hermetic Running**: Running this evaluation must have no side effects on production environments. Always use transient sandboxes.
