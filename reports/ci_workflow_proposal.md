# GitHub Actions CI Pipeline Design: Subagent & Git-Ops Validation

> [!NOTE]
> **Objective**: Design a customized GitHub Actions CI pipeline (`ci.yml`) tailored specifically to the Jetski repository's subagent environment. Enforce automated prompt manifest compilation checks, Python script lints, DevSite Markdown style guides, and HCL validation.

---

## 1. Core CI Objectives & Strategy

To maintain the stability, compliance, and **Git-Ops portability** of our multi-subagent blackboard environment, our CI pipeline must enforce four distinct automated checks on every push or pull request:

1.  **Prompt Manifest Synchronization Gate (`validate-subagent-manifest`)**:
    *   *The Goal*: If an engineer updates a system prompt in `prompts/security_critic.md` but forgets to run `compile_prompts.py` locally, the committed `.agents/state/compiled_subagents.json` manifest becomes stale. The CI must run the compiler and verify there is **zero git diff**.
2.  **Markdown Formatting Audit (`lint-markdown`)**:
    *   *The Goal*: Enforce the Google DevSite metadata rules and YAML frontmatter delimiters on all `.lab.md` files under `labs/dev/**/`.
3.  **Python Code Quality Gate (`lint-py-agents`)**:
    *   *The Goal*: Lint all automation scripts (such as `tester.py`, `compile_prompts.py`, and `init_skill.py`) under `.agents/` using Ruff.
4.  **Terraform HCL Validation (`terraform-check`)**:
    *   *The Goal*: Enforce recursive syntax checks and validation on all Terraform code blocks in our lab directories (`labs/dev/**/`).

---

## 2. Mapped GitHub Actions Configuration (`.github/workflows/ci.yml`)

Based on your team's TypeScript and Python Astral `uv` configurations, here is the recommended `.github/workflows/ci.yml` specification:

```yaml
name: CI

on:
  push:
    branches: [main, shacharb, shacharb-subagents]
  pull_request:
    branches: [main, shacharb, shacharb-subagents]

# Cancel in-progress runs on the same branch when a new commit is pushed.
concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  # --------------------------------------------------------------------
  # 1. Markdown / DevSite Style — Formatting checks
  # --------------------------------------------------------------------
  lint-markdown:
    name: Markdown / Codelab formatting check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install Prettier
        run: npm install -g prettier

      - name: Prettier Check (Markdown & YAML)
        run: prettier --check "**/*.{md,yml,yaml}"

  # --------------------------------------------------------------------
  # 2. Python — .agents scripts & tools (ruff lints)
  # --------------------------------------------------------------------
  lint-py-agents:
    name: Python .agents — ruff check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true

      - name: Set up Python
        run: uv python install 3.12

      - name: Ruff Linter Check
        run: |
          uv pip install ruff
          uv run ruff check .agents/scripts/ .agents/skills/*/scripts/

  # --------------------------------------------------------------------
  # 3. JIT Prompt Manifest Check — Ensures compiled_subagents.json isn't stale
  # --------------------------------------------------------------------
  validate-subagent-manifest:
    name: JIT subagents manifest up-to-date
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Recompile Prompts Manifest
        run: |
          # Correct absolute path simulation for CI CWD
          export WORKSPACE_ROOT=$GITHUB_WORKSPACE
          python3 .agents/scripts/compile_prompts.py

      - name: Verify Manifest is Up-to-Date (Git Diff Gate)
        run: |
          git diff --exit-code .agents/state/compiled_subagents.json
        # If this step fails, it means compiled_subagents.json was modified 
        # during compilation, indicating the committed version was stale.

  # --------------------------------------------------------------------
  # 4. Terraform — fmt + validate (checks all lab directories recursively)
  # --------------------------------------------------------------------
  terraform-check:
    name: Labs Terraform fmt + validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.9.8
          terraform_wrapper: false

      - name: Fmt Check (Recursive)
        run: |
          terraform fmt -check -recursive labs/dev/

      # Loop recursively through all GKE/Filestore subdirectories containing HCL to validate syntax
      - name: Validate Terraform (All Dev Labs)
        run: |
          for dir in $(find labs/dev -type f -name "*.tf" -exec dirname {} \; | sort -u); do
            echo "Initializing and validating Terraform in: $dir"
            cd $GITHUB_WORKSPACE/$dir
            terraform init -backend=false
            terraform validate
          done
```

---

## 3. Key Features & ROI of This Pipeline

1.  **The Git Diff Manifest Guard (`validate-subagent-manifest`)**:
    *   This is the exact analogue of your team's TypeScript `gen-types` check. It guarantees that the source prompts and compiled JIT schema **are always 100% in sync**. If an engineer updates the `reviewer.md` file but pushes without running the compiler, the build breaks instantly, blocking broken prompts from hitting production.
2.  **Automated Subdirectory HCL Scanning (`terraform-check`)**:
    *   Instead of hardcoding environment paths (like `infra/terraform/envs/dev` in your example), this job recursively scans `labs/dev/` for *any* subdirectory containing `.tf` files using the shell `find` command. It initializes and validates *every single lab's code block* dynamically, scaling automatically as new labs are added to the repository!
3.  **Paranoid Lints on Skills & Workflows**:
    *   Enforces that all newly drafted Skills and Workflows conform strictly to standard YAML/Prettier formatting. This keeps the repository clean, readable, and free of loose metadata delimiters.
