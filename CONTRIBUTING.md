# ce-skills — Operating Model & Contribution Rules

This repository is developed by **three agents and one human owner** working a
strict issue → PR → review → merge pipeline. This file is the single source of
truth for how we operate. **Every agent reads this file before acting.**

---

## Roles & lanes

| Role                   | Who        | Does                                                                              | Must NOT                                             |
| ---------------------- | ---------- | --------------------------------------------------------------------------------- | ---------------------------------------------------- |
| 🐛 **Bug Hunter**      | agent      | Finds & reproduces bugs; opens GitHub issues with repro, evidence, `file:line`.   | Fix code, open PRs, change severity of others.       |
| 🔧 **Developer**       | agent      | Takes an issue; writes the fix **plus a regression test**; opens a PR.            | Self-merge; touch unrelated code; skip the test.     |
| 🏛️ **Arch / Reviewer** | agent      | Triages severity; reviews every PR; gates on green CI; keeps the system coherent. | Merge (unless explicitly delegated); write features. |
| 👤 **Owner**           | shacharbob | Sets priorities; **merges**; final authority.                                     | —                                                    |

---

## The pipeline

```text
Bug Hunter                Developer                 Arch/Reviewer         Owner
   │  gh issue create        │                          │                   │
   ├────────────────────────▶│  branch fix/<#>-slug      │                   │
   │                         ├─ fix + red→green test ───▶│  review PR         │
   │                         │  PR "Fixes #<n>"          ├─ CI must be green  │
   │                         │                           ├─ approve / block ─▶│ merge
   │                         │                           │                   │ (issue auto-closes)
```

1. **Issue first.** No code changes without a GitHub issue. The issue is the ledger.
2. **Branch** off `pre-main`: `fix/<issue#>-short-slug` (or `ci/`, `chore/`, `docs/`).
3. **Fix + regression test** in the same PR. The test must fail before the fix and pass after.
4. **PR** references the issue with `Fixes #<n>` and targets `pre-main`.
5. **CI** (format + lint + unit tests) must be green. A red gate is a hard stop.
6. **Review** by the Arch. Approve or request changes.
7. **Owner merges** (squash). The issue closes automatically.

---

## Commit rules

- **Never attribute commits to Claude.** No `Co-Authored-By: Claude` trailer, no
  Claude author or committer — ever, by any agent.
- **Author identity is always** `Shachar Bobrovskye <shacharb@google.com>`. Verify
  with `git config --local user.email` before committing.
- **Never commit directly to `pre-main` or `main`.** Everything goes through a PR.
- **Conventional commits:** `fix:`, `feat:`, `test:`, `ci:`, `docs:`, `chore:`,
  `refactor:`. Reference the issue in the body (`Refs #12` / `Fixes #12`).
- **One issue ↔ one PR ↔ one focused change.** No drive-by edits; open a new issue
  for anything you notice in passing.

---

## Branch model

- **`main`** — protected release branch. No direct pushes. Promoted from `pre-main`.
- **`pre-main`** — integration branch. All fix/feature PRs target this.
- **`fix/*`, `ci/*`, `docs/*`, `chore/*`** — short-lived; deleted after merge.

---

## Testing requirements

- **Every bug fix ships a regression test** that fails on the pre-fix code and
  passes on the fixed code. No test, no merge.
- Tests live under `tests/` and run in CI via `pytest`. Keep them **hermetic** — no
  live GCP calls, no network, no real `gcloud`/`bq`. Stub or inject instead.
- When a fix touches a script that has no tests yet, add the minimal harness needed
  to test the changed behavior (don't retrofit the whole file).

---

## CI gates (all must pass before merge)

1. **Format** — Prettier on Markdown/YAML.
2. **Lint** — Ruff across `.agents/` and `scripts/`.
3. **Prompt manifest** — `compile_prompts.py` runs and emits a valid 7-subagent manifest.
4. **Unit tests** — `pytest tests/`.

CI runs on `push`/`pull_request` for `main` and `pre-main`. If CI is red, the fix is
not done — do not merge, do not override.

---

## Issues — the bug ledger (GitHub, not Buganizer)

Bugs are tracked as **GitHub issues**. (The `open-bug` skill targets an internal
Buganizer component and is **not** used for this workflow.)

**Bug Hunter files with `gh issue create`** using this body shape (templates in the
web UI don't apply to the CLI, so include the sections yourself):

```text
### Severity
critical | high | medium | low

### Location
path/to/file.py:LINE

### What's wrong
One or two sentences.

### Reproduction
Exact steps / input that triggers it.

### Expected vs actual
Expected: …
Actual: …

### Evidence
Short snippet, command output, or trace.
```

Apply labels: `bug` + one `sev:*`. Start every new issue at `status:triage`; the
Arch confirms or adjusts severity.

**Labels:** `bug`, `sev:critical`, `sev:high`, `sev:medium`, `sev:low`,
`status:triage`, `status:in-progress`, `status:needs-review`.

---

## Pull requests

- Title: conventional-commit style, e.g. `fix: force-delete parses project name fragment`.
- Body must include `Fixes #<n>`, a one-line summary, and how the regression test
  proves the fix (red→green).
- Keep the diff scoped to the issue. Unrelated cleanups get their own issue.

---

## Definition of Done (per fix)

- [ ] Linked issue exists and is referenced (`Fixes #<n>`).
- [ ] Root cause fixed (not just the symptom).
- [ ] Regression test added; fails before, passes after.
- [ ] All CI gates green.
- [ ] No Claude attribution; authored as `Shachar Bobrovskye <shacharb@google.com>`.
- [ ] Diff scoped to this one issue.
- [ ] Arch approved.

---

## Severity taxonomy

- **critical** — data loss, deletes/mutates the wrong cloud resources, security-boundary
  failure, or silently certifies broken work as passing.
- **high** — code execution / injection, financially misleading output, or a broken
  safety net (tests/CI) that hides other bugs.
- **medium** — wrong output, crash on a common input, or docs that misdescribe the code.
- **low** — edge-case robustness, hygiene, cosmetic drift.

---

## Arch review checklist

When reviewing a PR, the Arch confirms:

1. The linked issue's root cause is actually fixed — not just the reported symptom.
2. The regression test genuinely covers it (would fail on `pre-main`).
3. No scope creep; the diff maps to exactly one issue.
4. No new injection surface (`shell=True` + interpolation, unescaped HTML, raw SQL).
5. No author-machine hardcoding (`shacharb`, `skynet`, `/usr/local/google/...`).
6. Errors surface (no bare `except` that turns failure into success/`$0.00`/`DONE`).
7. Docs/SKILL.md updated if behavior or flags changed.
