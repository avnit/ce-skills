<!-- disableFinding(all) -->
<!-- mdlint off -->

# Standardized Skill Review Report Template

When instructed to output a complete, standalone, or comprehensive review report
artifact for an agent skill or skill CL, reviewers MUST structure their output
according to this exact Markdown layout.

*Note for Reviewers on Fast-Track vs. Full-Review and Dynamic Output
Adaptation*:

*   **Fast-Track Protocol**: If the target skill is a minor revision or has <3
    checklist failures, **Section 4 (`Technical & UX Deep-Dives`) below is
    OPTIONAL**. Provide only Sections 1 (`Executive Summary`), 2 (`Scorecard`),
    3 (`Remediation Matrix`), and 5 (`Refactoring Blueprint`) to protect
    reviewer velocity and throughput.
*   **Full-Review Protocol**: ONLY generate Section 4 (`Deep-Dives`) when
    diagnosing complex runtime gotchas, severe attention dilution (`lost in the
    middle`), or major architectural refactorings. When generating Section 4,
    populate `{placeholder_text}` with concrete technical evidence, line
    citations (`file://...#L...`), and causal rationale. Omit or mark `NA` for
    non-applicable sub-sections.
*   **Dynamic Output Adaptation (`Google3 vs. GitHub/OSS`)**: When rendering
    this report in **GitHub / OSS Mode (`Open Source / Git PRs`)**,
    automatically **OMIT** Google-only infrastructure rows (`blaze test`,
    `OWNERS file`, `$CRITIQUE/$SPONGE aliases`, `canonical google3/ paths`, and
    `Buganizer footer`) from Section 2 tables so the open-source report stays
    100% clean (`zero internal noise`). Replace Section 2.3 (`Critique CL
    Table`) with a **GitHub PR & Test Verification Checklist** (`e.g., verify PR
    description links to issue/prompt, verify CI output / pytest HTML report is
    linked, verify zero internal Google URLs or proprietary paths leak into
    GitHub`).

--------------------------------------------------------------------------------

# Skill Reviewer & Central Skills Review Report

**Target Name**: `{skill-name}` \
**CL / Target Path**: `[{cl_or_depot_path}]({url})` \
**Review Date**: `{YYYY-MM-DD}` \
**Reviewer Persona**: Skill Reviewer & Central Skills (`skill_creator`) Agent \
**Overall Verdict**: **`[APPROVE / REQUEST_CHANGES]`**

--------------------------------------------------------------------------------

## 1. Executive Summary & Scope

{Provide a crisp 2–3 paragraph executive summary evaluating the target skill
across two core dimensions:

1.  **Engineering Objective & Value**: What developer journey or cloud workflow
    does this skill accelerate, and why is an opinionated golden path necessary?
2.  **Review Synthesis (`Signal vs Noise`)**: What is working well
    (`strengths`), and what are the primary structural blockers, attention
    mechanics issues (`MUST/ALWAYS smells, duplicating across levels`), UX traps
    (`open-ended Phase 1 questionnaires, combinatorial menus`), or domain
    mechanics gotchas discovered during the review.}

--------------------------------------------------------------------------------

## 2. Objective Metrics Summary (`check_skill_links`)

| Metric            | Measured Value     | Benchmark Target         | Status  |
| :---------------- | :----------------: | :----------------------: | :-----: |
| **Description     | `{n} chars`        | $\le 1024$ chars; `Use   | `[✓/✗]` |
: Length**          :                    : when` present            :         :
| **Main Body Size  | `{n} lines / ~{t}  | $< 200$ lines best ($\le | `[✓/✗]` |
: (`SKILL.md`)**    : tokens`            : 500$ max)                :         :
| **Reference Files | `{n} files / ~{t}  | Linked exactly 1 level   | `[✓/✗]` |
: (`references/`)** : tokens`            : deep                     :         :
| **Long Reference  | `{n}/{n} docs >100 | $100\%$ contain Table of | `[✓/✗]` |
: TOC Check**       : lines`             : Contents                 :         :
| **Static          | `{e} errors / {w}  | $0$ errors (`no          | `[✓/✗]` |
: Verification      : warnings`          : secrets/broken links`)   :         :
: (`check_skill`)** :                    :                          :         :

--------------------------------------------------------------------------------

## 3. Cold Trigger Simulation (`Phase 2 Hit Rate Matrix`)

| \#  | Prompt     | Simulated Prompt | Should   | Triggers? | Root Cause  |
:     : Type       :                  : Trigger? :           : Diagnosis   :
| --- | ---------- | ---------------- | :------: | :-------: | ----------- |
| 1   | **Explicit | `{names exact    | `YES`    | `[Y/N]`   | `{Diagnosis |
:     : Positive** : skill/capability :          :           : from        :
:     :            : directly}`       :          :           : metadata}`  :
| 2   | **Explicit | `{names exact    | `YES`    | `[Y/N]`   | `{...}`     |
:     : Positive** : tool/task}`      :          :           :             :
| 3   | **Implicit | `{user's need in | `YES`    | `[Y/N]`   | `{...}`     |
:     : Positive** : natural          :          :           :             :
:     :            : phrasing, zero   :          :           :             :
:     :            : jargon}`         :          :           :             :
| 4   | **Implicit | `{user's need in | `YES`    | `[Y/N]`   | `{...}`     |
:     : Positive** : natural          :          :           :             :
:     :            : phrasing, zero   :          :           :             :
:     :            : jargon}`         :          :           :             :
| 5   | **Adjacent | `{task belonging | `NO`     | `[Y/N]`   | `{...}`     |
:     : Negative** : to sibling       :          :           :             :
:     :            : skill}`          :          :           :             :
| 6   | **Adjacent | `{general        | `NO`     | `[Y/N]`   | `{...}`     |
:     : Negative** : reasoning or     :          :           :             :
:     :            : unrelated task}` :          :           :             :

*   **Hit Rate**: `{n}/6` (`if < 6, state diagnosis: e.g., 'Invisible Expert
    profile — description lacks natural synonyms/verbs'`).

--------------------------------------------------------------------------------

## 4. Official Central Scorecard (`reviewing.md`)

### 4.1 Structural Validation Checklist

Target                       | Command                                                                                                                                                             | Status           | Failure Details & Impact
:--------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :--------------: | :-----------------------
**Directory & Header Rules** | `blaze test {package_path}:validate_{name}_skill_test`                                                                                                              | `[PASS/FAIL/NA]` | {In Google3, verify `BUILD` exists with `agent_skill(...)` and `validate_skill_test(...)` (`mark P0 Blocker: FAIL if missing`). In GitHub/OSS mode, mark `NA`.}
**Link & Path Verification** | `blaze run //experimental/users/shacharb/skills/skill_review/scripts:check_skill_links -- --skill_path={path}` *(or `python3 scripts/check_skill_links.py` in OSS)* | `[PASS/FAIL]`    | {Verifies zero broken links across files and zero ephemeral cloud workspace paths (`/google/src/cloud/<user>/...`).}

### 4.2 Skill Content Criteria (`reviewing.md: lines 43-64`)

| \#  | Criterion        | Verdict          | Notes against Central   |
:     :                  :                  : Skills Specification    :
| --- | ---------------- | :--------------: | ----------------------- |
| 1   | **Actual need**  | `[PASS/FAIL]`    | {Addresses a real,      |
:     :                  :                  : recurring,              :
:     :                  :                  : high-friction user      :
:     :                  :                  : workflow.}              :
| 2   | **Agent can't    | `[PASS/FAIL]`    | {The agent genuinely    |
:     : already do it**  :                  : fails without this      :
:     :                  :                  : specific guidance;      :
:     :                  :                  : prevents hallucination  :
:     :                  :                  : or bad defaults.}       :
| 3   | **No bundled     | `[PASS/FAIL]`    | {CLIs live in `clis/`,  |
:     : library code**   :                  : not in the skill.       :
:     :                  :                  : Static helper templates :
:     :                  :                  : live under `assets/`.}  :
| 4   | **Description    | `[PASS/FAIL]`    | {Uses folded string     |
:     : triggers         :                  : `>-`, begins in third   :
:     : correctly**      :                  : person, includes `Use   :
:     :                  :                  : when...` / `Don't use   :
:     :                  :                  : for...`, and is <1024   :
:     :                  :                  : chars.}                 :
| 5   | **Concise body** | `[PASS/FAIL]`    | {Deep schemas moved to  |
:     :                  :                  : `references/`. No       :
:     :                  :                  : duplication across      :
:     :                  :                  : `SKILL.md` and          :
:     :                  :                  : reference checklists or :
:     :                  :                  : `assets/`.}             :
| 6   | **No unnecessary | `[PASS/FAIL]`    | {No extraneous          |
:     : files**          :                  : `README.md`,            :
:     :                  :                  : `CHANGELOG.md`,         :
:     :                  :                  : `INSTALLATION_GUIDE.md` :
:     :                  :                  : files in the            :
:     :                  :                  : directory.}             :
| 7   | **Instructions   | `[PASS/FAIL]`    | {Non-obvious commands   |
:     : explain why**    :                  : and security rules pair :
:     :                  :                  : directives with         :
:     :                  :                  : engineering rationale   :
:     :                  :                  : (`Explain the Why`)     :
:     :                  :                  : rather than caps-lock   :
:     :                  :                  : shouting (`MUST/ALWAYS  :
:     :                  :                  : Smell`).}               :
| 8   | **Tested with    | `[PASS/FAIL]`    | {Prompts in             |
:     : natural          :                  : `EVAL.txtpb` mirror     :
:     : prompts**        :                  : natural developer       :
:     :                  :                  : phrasing rather than    :
:     :                  :                  : artificial keyword      :
:     :                  :                  : triggers.}              :
| 9   | **No             | `[PASS/FAIL]`    | {No unresolved `TODO`   |
:     : TODO/placeholder :                  : or `FIXME` banners      :
:     : text**           :                  : across modified paths.} :
| 10  | **OWNERS file**  | `[PASS/FAIL/NA]` | {Check against boundary |
:     :                  :                  : rules\: mandatory for   :
:     :                  :                  : `learning/` and         :
:     :                  :                  : `third_party/skills/`;  :
:     :                  :                  : MUST NOT exist for      :
:     :                  :                  : `experimental/users/`.} :
| 11  | **EVAL.txtpb     | `[PASS/FAIL]`    | {Automated evaluation   |
:     : present**        :                  : cases exist (`task      :
:     :                  :                  : tests`, minimum 5 cases :
:     :                  :                  : per `eval_creator`).}   :

### 4.2b Syntax, Formatting & Path Hygiene (`[writing-guide.md](google3/learning/gemini/agents/skills/skill_creator/references/writing-guide.md)` & `SKILL.md`)

\#  | Criterion                        | Verdict          | Notes against Central Writing Specification
--- | -------------------------------- | :--------------: | -------------------------------------------
12  | **Imperative form**              | `[PASS/FAIL]`    | {Instructions use imperative form (`Run the validator`, not `You should run...`).}
13  | **`{snake_case}` placeholders**  | `[PASS/FAIL]`    | {Placeholders strictly use `{snake_case}` (`--path={output_dir}`).}
14  | **Language specifiers & tables** | `[PASS/FAIL]`    | {Code blocks include explicit language specifiers (`bash`, `python`); flag/option documentation uses Markdown tables.}
15  | **`$VAR` alias preservation**    | `[PASS/FAIL]`    | {Commands preserve environment variable aliases (`$CRITIQUE`, `$SPONGE`) rather than hardcoding precompiled binary paths.}
16  | **Canonical link paths**         | `[PASS/FAIL]`    | {File references use stable `google3/...` or `/google/src/files/...` paths rather than transient cloud paths (`/google/src/cloud/<user>/...`).}
17  | **No universal generic advice**  | `[PASS/FAIL]`    | {Removes universal zero-signal advice (`'Read docs before proceeding'`, `'Handle errors appropriately'`, `'Test your changes'`).}
18  | **Reporting Issues footer**      | `[PASS/FAIL/NA]` | {Permanent skills (`learning/`, `third_party/skills/`) include a `## Reporting Issues` link to a Buganizer hotlist (`http://b/hotlists/...`). Omit for experimental directories.}

### 4.2c Evaluation Quality & Structure (`[eval_creator](google3/learning/gemini/agents/skills/eval_creator/SKILL.md)`)

| \#  | Criterion    | Verdict          | Notes against Central        |
:     :              :                  : `eval_creator` Specification :
| --- | ------------ | :--------------: | ---------------------------- |
| 19  | **Exact      | `[PASS/FAIL]`    | {`suite_name` strictly       |
:     : `suite_name` :                  : matches the `snake_case`     :
:     : match**      :                  : skill directory name         :
:     :              :                  : (`eval_creator\:L321`). No   :
:     :              :                  : unsupported `skills\:` or    :
:     :              :                  : `user_simulator\:` blocks    :
:     :              :                  : exist.}                      :
| 20  | **Tasks vs.  | `[PASS/FAIL]`    | {Cases test capabilities     |
:     : quizzes**    :                  : (`DO work, reason, call      :
:     :              :                  : tools`) rather than recall   :
:     :              :                  : (`explain how X works` or    :
:     :              :                  : `how do I use X`)            :
:     :              :                  : (`eval_creator\:L20-36`).}   :
| 21  | **Zero tool  | `[PASS/FAIL]`    | {Prompts NEVER mention tool  |
:     : names in     :                  : names, CLI commands,         :
:     : prompts**    :                  : subcommands, or flags        :
:     :              :                  : (`eval_creator\:L95`).       :
:     :              :                  : Prompts read like natural    :
:     :              :                  : user requests.}              :
| 22  | **Outcome    | `[PASS/FAIL]`    | {Expectations assert WHAT    |
:     : vs. process  :                  : was achieved (`outcomes`),   :
:     : assertions** :                  : not HOW (`implementation     :
:     :              :                  : details/CLI execution        :
:     :              :                  : paths`)                      :
:     :              :                  : (`eval_creator\:L216-295`).} :
| 23  | **Hermetic   | `[PASS/FAIL/NA]` | {Isolated `setup.commands` / |
:     : fixture      :                  : `cleanup.commands` per case  :
:     : setup**      :                  : when write paths or temp     :
:     :              :                  : files (`Strategy A`) are     :
:     :              :                  : exercised                    :
:     :              :                  : (`eval_creator\:L186-215`).} :

### 4.3 CL Review Checklist (`reviewing.md: lines 129-138`)

*(Output NA if reviewing a local directory outside an active Critique CL).* | #
| Required Item | Verdict | Notes against Central Review Standard |
|---|---|:---:|---| | 1 | **Creation prompt** | `[PASS/FAIL/NA]` | {CL
description must contain `### Skill creation prompt` linking to the
prompt/conversation.} | | 2 | **Trajectory links** | `[PASS/FAIL/NA]` | {CL
description must contain `### Trajectories using skill:` listing `go/traj/`
execution logs.} | | 3 | **Good prompts** | `[PASS/FAIL/NA]` | {Evaluated
prompts across trajectories mirror real user journeys.} | | 4 | **OWNERS file**
| `[PASS/FAIL/NA]` | {Checked and valid for permanent paths.} | | 5 |
**`MARKDOWN=true`** | `[PASS/FAIL/NA]` | {Mandatory `MARKDOWN=true` tag must be
present in the CL description footer.} | | 6 | **`EVALIN_REPORT` tag** |
`[PASS/FAIL/NA]` | {Mandatory `EVALIN_REPORT=<url>` tag linking to an evalin
ablation report must be present.} |

--------------------------------------------------------------------------------

## 5. Prioritized Remediation Action Matrix

The following action table sorts all identified findings by Priority (`P0` to
`P2`), linking each remediation to exact CL targets, authoritative
`skill_creator` citations, underlying machine learning/runtime mechanics, and
prescriptive developer fixes:

Priority             | Action Item & Summary                                             | Target CL Reference (`Depot File & Lines`)              | Authoritative Central Citation (`skill_creator`)        | Underlying Mechanics & Logic                                                                                                                 | Concrete Recommended Fix
:------------------: | :---------------------------------------------------------------- | :------------------------------------------------------ | :------------------------------------------------------ | :------------------------------------------------------------------------------------------------------------------------------------------- | :-----------------------
🚨 **P0** (`Blocker`) | **{Short Title of Missing Build/Hygiene/Runtime Gotcha}**         | `[path.md:L...](file:///path#L...)` or `CL Description` | `[SKILL.md:L...](file:///path)` or `reviewing.md`       | {Explain why this halts compilation, blocks validation testing, or introduces broken network/API runtime behavior.}                          | {Prescribe exact, actionable steps or code changes required for approval.}
⚠️ **P1** (`High`)   | **{Short Title of Caps-Lock/Menu/Questionnaire/Bloat Violation}** | `[path.md:L...](file:///path#L...)`                     | `[writing-guide.md:L...](file:///path)` / `Principle N` | {Explain the exact attention dilution (`lost in the middle`), combinatorial explosion ($2^N$ variance), or UX interview fatigue root cause.} | {Prescribe exact refactoring: e.g., lock default path, colonize Phase 1 to 2 questions, delete redundant checklists.}
💡 **P2** (`Medium`)  | **{Short Title of Prompt Overfitting or Driver Ambiguity}**       | `[path.md:L...](file:///path#L...)`                     | `writing-guide.md` / `SKILL.md`                         | {Explain how micromanaging syntax (`overfitting`) or leaving connection strings ambiguous creates developer friction.}                       | {Prescribe precise cleanup or recommended inline comment guidance.}

--------------------------------------------------------------------------------

## 6. Technical, UX & Framework Deep-Dives (`Optional / As Needed`)

*(Skip this section under Fast-Track Protocol when failures are minor or
straightforward. Generate only the required diagnostic blocks below when
detailing complex runtime gotchas or architectural refactorings).*

### 6.1 Domain Mechanics & Architectural Gotchas (`Code & API Audit`)

*   **Gotcha Target**: `[depot_path:L...](file:///path#L...)`
*   **Underlying Mechanics**:
    {Explain the exact networking, DNS, API discovery, or authentication behavior when this code runs in a live Google Cloud or Google3 workspace.}
*   **The Engineering Fix**:
    {Provide the precise code modification or template update required to fix the runtime issue.}

### 6.2 Agent Ergonomics & UX Mechanics (`Intake & Token Budget`)

*   **Questionnaire Intake vs. Defaults (`Phase 1`)**:
    {If the agent is told to ask 4+ open-ended questions, explain how multi-turn interrogations cause user abandonment or attention-degraded fast-forward hallucinations. Prescribe `Colonizing Phase 1` down to 2–3 mandatory forks.}
*   **Output Token Bloat (`max_tokens`)**:
    {If the skill demands overlapping deliverables (`IaC + CLI + custom scripts + reports`), explain how exceeding 4,000–6,000 tokens forces internal sampling compression and syntax truncation. Enforce `One Job Well` to keep one primary deliverable.}

### 6.3 Central Framework Anti-Patterns (`writing-guide.md`)

*   **MUST/ALWAYS Caps-Lock Smells & Duplication**:
    `[path:L...](file:///path#L...)` —
    {Explain how repeating caps-lock rules across `SKILL.md` and check-list files consumes active context (`over-conditioning`) and causes middle-token attention dropping. Enforce hardcoding rules inside working code (`assets/main.tf`).}
*   **Combinatorial Explosion (`One Default, One Escape Hatch`)**:
    `[path:L...](file:///path#L...)` —
    {Explain how presenting a branching menu ($2^N$ options) without locking down a default causes trajectory non-determinism during `evalin` ablation trials. Prescribe an opinionated baseline default.}

--------------------------------------------------------------------------------

## 7. Recommended Golden Path Refactoring Blueprint (Summary for Author)

{Summarize the mandatory remediation steps into a copy-pasteable 4-point roadmap
that the author can immediately apply to bring the CL into strict compliance and
secure approval:}

```markdown
1. Structural & CL Hygiene (`blaze test` & Metadata)
   - {Action: e.g., Create BUILD file with agent_skill & validate_skill_test rules.}
   - {Action: e.g., Add ### Skill creation prompt, ### Trajectories, MARKDOWN=true to CL description.}

2. Code as the Single Source of Truth (`assets/...`)
   - {Action: e.g., Hardcode the non-negotiable security/networking blocks directly inside assets/main.tf with comments.}
   - {Action: e.g., DELETE redundant reference checklist files completely to keep SKILL.md under 150 lines.}

3. Phase 1 Pruning & Sensible Defaults (`One Default, One Escape Hatch`)
   - {Action: e.g., Lock down an opinionated 80% baseline by default. Only ask 2 optional disambiguation questions.}

4. Eliminate Output Token Bloat (`One Job Well`)
   - {Action: e.g., Remove instructions requiring redundant CLI equivalents or custom verification scripts. Require strictly the core deliverable.}
```
