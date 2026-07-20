<!-- disableFinding(all) -->
<!-- mdlint off -->

# Skill Review Scorecard & Prioritized Action Framework

When conducting an authoritative review on an agent skill CL, skill directory,
or prompt design, reviewers must structure their findings and recommendations
according to this standardized Skill Reviewer and Central Skills framework.

Every review outputs a **Formal Scorecard** (`Section 1`), a **Core Principles
Audit** (`Section 2`), an **Anatomy & Progressive Disclosure Check** (`Section
3`), and an actionable **Prioritized Remediation Action Matrix** (`Section 4`).

*Note on Execution Modes*: By default (`Summary-First Mode`), output only the
Executive Summary and the **Prioritized Remediation Action Matrix (`Section 2
below`)** to prevent table fatigue and reserve attention budget for diagnostics.
ONLY render the full 23-row Formal Scorecard below (`Section 1`) when explicitly
in `Full Scorecard Mode` (`e.g., when the user asks for a complete scorecard or
when posting formal Critique reviews`). *Note on Dynamic Output Adaptation
(`Google3 vs. GitHub/OSS`)*: When rendering scorecards in `GitHub / OSS Mode
(`Open Source / Git PRs`)`, automatically **OMIT** Google-only infrastructure
rows (`blaze test`, `OWNERS file`, `$CRITIQUE/$SPONGE aliases`, `canonical
google3/ paths`, and `Buganizer footer`) from the tables so the open-source
scorecard stays 100% clean and native (`no internal noise`). Replace Section 1.3
(`Critique CL Table`) with a **GitHub PR & Test Verification Checklist** (`e.g.,
check PR description links to issue/prompt, check CI output / pytest HTML report
is linked, check zero internal Google URLs or proprietary paths leak into
GitHub`).

--------------------------------------------------------------------------------

## 1. Formal Scorecard Structure (`reviewing.md`)

When in `Full Scorecard Mode` (`adapted dynamically for Google3 vs.
GitHub/OSS`), output the following structured markdown scorecard verbatim,
marking every applicable item `PASS`, `FAIL`, or `NA` with exact details and
citations:

```markdown
# Skill Review: `{skill-name}`
**CL / Target Path**: `{cl_link_or_depot_path}`
**Reviewer Persona**: Skill Reviewer & Central Skills (`skill_creator`) Agent
**Overall Verdict**: `[APPROVE / REQUEST_CHANGES]`

---

## 1. Official Scorecard against `reviewing.md`

### 1.1 Structural Validation Checklist
| Target | Command | Status | Failure Details |
| :--- | :--- | :---: | :--- |
| **Directory & Header Rules** | `blaze test {package_path}:validate_{skill_name_as_snake_case}_skill_test` | `[PASS/FAIL/NA]` | {In Google3, verify `BUILD` exists with `agent_skill(...)` and `validate_skill_test(...)` (`mark P0 Blocker: FAIL if missing`). In GitHub/OSS mode, mark `NA`.} |
| **Link & Path Verification** | `blaze run //experimental/users/shacharb/skills/skill_review/scripts:check_skill_links -- --skill_path={path}` *(or `python3 scripts/check_skill_links.py` in OSS)* | `[PASS/FAIL]` | {Details. Verifies zero broken links across files and zero ephemeral cloud workspace paths (`/google/src/cloud/<user>/...`).} |

### 1.2 Skill Content Criteria (`reviewing.md: lines 43-64`)
| # | Criterion | Verdict | Notes against Central Skills Specification |
|---|---|:---:|---|
| 1 | **Actual need** | `[PASS/FAIL]` | {Addresses a real, recurring, high-impact user workflow where consistency matters.} |
| 2 | **Agent can't already do it** | `[PASS/FAIL]` | {The agent genuinely fails without this specific guidance; prevents hallucination or bad defaults.} |
| 3 | **No bundled library code** | `[PASS/FAIL]` | {Complex CLIs live in `clis/`, not inside the skill directory. Static helper templates live strictly under `assets/`.} |
| 4 | **Description triggers correctly** | `[PASS/FAIL]` | {Uses folded string `>-`, begins with third-person capability statement, includes explicit `Use when...` / `Don't use for...` triggers, and is <1024 chars.} |
| 5 | **Concise body** | `[PASS/FAIL]` | {Deep content and static schemas moved to `references/`. No duplication across `SKILL.md` and reference checklists or `assets/`.} |
| 6 | **No unnecessary files** | `[PASS/FAIL]` | {No extraneous `README.md`, `CHANGELOG.md`, `INSTALLATION_GUIDE.md` files in the directory.} |
| 7 | **Instructions explain why** | `[PASS/FAIL]` | {Non-obvious commands and security rules pair directives with engineering rationale (`Explain the Why`) rather than caps-lock shouting (`MUST/ALWAYS Smell`).} |
| 8 | **Tested with natural prompts** | `[PASS/FAIL]` | {Prompts in `EVAL.txtpb` mirror natural developer phrasing rather than artificial keyword triggers.} |
| 9 | **No TODO/placeholder text** | `[PASS/FAIL]` | {No unresolved `TODO` or `FIXME` banners across the modified paths.} |
| 10 | **OWNERS file** | `[PASS/FAIL/NA]` | {Verify `OWNERS` exists for permanent skills (`learning/` or `third_party/skills/`). Mark `FAIL` if present under `experimental/users/` (`experimental skills MUST NOT have OWNERS files`).} |
| 11 | **EVAL.txtpb present** | `[PASS/FAIL]` | {Automated evaluation cases exist (`task tests`, minimum 5 cases per `eval_creator`).} |

### 1.2b Syntax, Formatting & Path Hygiene (`[writing-guide.md](google3/learning/gemini/agents/skills/skill_creator/references/writing-guide.md)` & `SKILL.md`)
| # | Criterion | Verdict | Notes against Central Writing Specification |
|---|---|:---:|---|
| 12 | **Imperative form** | `[PASS/FAIL]` | {Instructions use imperative form (`Run the validator`, not `You should run...`).} |
| 13 | **`{snake_case}` placeholders** | `[PASS/FAIL]` | {Placeholders strictly use `{snake_case}` (`--path={output_dir}`).} |
| 14 | **Language specifiers & tables** | `[PASS/FAIL]` | {Code blocks include explicit language specifiers (`bash`, `python`); flag/option documentation uses Markdown tables.} |
| 15 | **`$VAR` alias preservation** | `[PASS/FAIL]` | {Commands preserve environment variable aliases (`$CRITIQUE`, `$SPONGE`) rather than hardcoding precompiled binary paths.} |
| 16 | **Canonical link paths** | `[PASS/FAIL]` | {File references use stable `google3/...` or `/google/src/files/...` paths rather than transient cloud paths (`/google/src/cloud/<user>/...`).} |
| 18 | **Reporting Issues footer** | `[PASS/FAIL/NA]` | {Permanent skills (`learning/`, `third_party/skills/`) include a `## Reporting Issues` link to a Buganizer hotlist (`http://b/hotlists/...`). Omit for experimental directories.} |

### 1.2c Evaluation Quality & Structure (`[eval_creator](google3/learning/gemini/agents/skills/eval_creator/SKILL.md)`)
| # | Criterion | Verdict | Notes against Central `eval_creator` Specification |
|---|---|:---:|---|
| 19 | **Exact `suite_name` match** | `[PASS/FAIL]` | {`suite_name` strictly matches the `snake_case` skill directory name (`eval_creator:L321`). No unsupported `skills:` or `user_simulator:` blocks exist.} |
| 20 | **Tasks vs. quizzes** | `[PASS/FAIL]` | {Cases test capabilities (`DO work, reason, call tools`) rather than recall (`explain how X works` or `how do I use X`) (`eval_creator:L20-36`).} |
| 21 | **Zero tool names in prompts** | `[PASS/FAIL]` | {Prompts NEVER mention tool names, CLI commands, subcommands, or flags (`eval_creator:L95`). Prompts read like natural user requests.} |
| 22 | **Outcome vs. process assertions** | `[PASS/FAIL]` | {Expectations assert WHAT was achieved (`outcomes`), not HOW (`implementation details/CLI execution paths`) (`eval_creator:L216-295`).} |
| 23 | **Hermetic fixture setup** | `[PASS/FAIL/NA]` | {Isolated `setup.commands` / `cleanup.commands` per case when write paths or temp files (`Strategy A`) are exercised (`eval_creator:L186-215`).} |

### 1.3 CL Review Checklist (`reviewing.md: lines 129-138`)
*(Only output if reviewing an active Critique CL. Omit if reviewing local directory only).*
| # | Required Item | Verdict | Notes against Central Review Standard |
|---|---|:---:|---|
| 1 | **Creation prompt** | `[PASS/FAIL]` | {CL description must contain `### Skill creation prompt` linking to the prompt/conversation.} |
| 2 | **Trajectory links** | `[PASS/FAIL]` | {CL description must contain `### Trajectories using skill:` listing `go/traj/` execution logs.} |
| 3 | **Good prompts** | `[PASS/FAIL]` | {Evaluated prompts across trajectories mirror real user journeys.} |
| 4 | **OWNERS file** | `[PASS/FAIL/NA]` | {Checked and valid for permanent paths.} |
| 5 | **`MARKDOWN=true`** | `[PASS/FAIL]` | {Mandatory `MARKDOWN=true` tag must be present in the CL description footer.} |
| 6 | **`EVALIN_REPORT` tag** | `[PASS/FAIL]` | {Mandatory `EVALIN_REPORT=<url>` tag linking to an evalin ablation report must be present.} |

### 1.4 Red Flags (`reviewing.md: lines 139-147`)
* Flag any of the following for immediate escalation or blocking changes:
  * Skill duplicates functionality of an existing central skill (`Check skill_catalog`).
  * Skill contains library code (`py/go`) that belongs in `clis/`.
  * No trajectory evidence of actual usage (`go/traj/`).
  * Skill is overly broad / `One Job Well` violation (`tries to do too many unrelated tasks at once`).
  * Description is too vague or too generic (`e.g., 'Interact with Dapper', 'helper utils'`) to trigger reliably.
  * Skill is team-specific or narrow in scope but placed in the central directory (`learning/gemini/agents/skills/`) rather than the team's codebase (`Strict Central Directory Rule`).

### 1.5 Cold Trigger Simulation Table (`Phase 2 Hit Rate Evaluation`)
Before reading `SKILL.md` body prose, evaluate triggering reliability directly from metadata (`name` + `description` + `Use when` bounds):

| # | Prompt Type | Simulated Prompt | Should Trigger? | Triggers? | Root Cause Diagnosis |
|---|---|---|:---:|:---:|---|
| 1 | **Explicit Positive** | `{names exact skill/capability directly}` | `YES` | `[Y/N]` | `{Diagnosis from metadata}` |
| 2 | **Explicit Positive** | `{names exact tool/task}` | `YES` | `[Y/N]` | `{...}` |
| 3 | **Implicit Positive** | `{user's need in natural phrasing, zero jargon}` | `YES` | `[Y/N]` | `{...}` |
| 4 | **Implicit Positive** | `{user's need in natural phrasing, zero jargon}` | `YES` | `[Y/N]` | `{...}` |
| 5 | **Adjacent Negative** | `{task belonging to sibling skill}` | `NO` | `[Y/N]` | `{...}` |
| 6 | **Adjacent Negative** | `{general reasoning or unrelated task}` | `NO` | `[Y/N]` | `{...}` |

* **Hit Rate Scoring**: $6/6 =$ Exemplary (`D1 = 5/5`); $4-5/6 =$ Needs Polish (`D1 = 3/5`); $\le 3/6 =$ Invisible Expert (`D1 = 1/5`).

### 1.6 Common Diagnostic Failure Profiles
When diagnosing a skill, identify if one of these 5 canonical failure profiles fits the target and name it prominently in the Executive Summary / Verdict:
* **Invisible Expert** (`High instruction quality, fails Triggering`): Excellent internal code/prose behind a vague description that never fires in chat (`fix description metadata before touching prose`).
* **Context Bomb** (`Fails Progressive Disclosure`): `SKILL.md` exceeds 500 lines or dumps all reference material inline (`loads too many tokens on every turn; move detail to references/ first`).
* **Beautiful Shell** (`High trigger rate, low value density`): Triggers eagerly, but body only contains universal zero-signal advice (`"Read docs first"`, `"Validate output"`) that a bare LLM already knows.
* **Fragile Robot** (`Low script reliability`): Helper utilities (`scripts/` or `clis/`) crash bare on predictable edge cases or swallow errors (`harden error handling cleanly`).
* **Unlocked Workshop** (`Low safety posture`): Over-privileged bash allowances (`Bash in allowed-tools`) or irreversible workflows (`deploys, mass edits`) missing explicit user confirmation gates.
```

--------------------------------------------------------------------------------

## 2. Prioritized Remediation Action Matrix Schema

When a skill review outputs `REQUEST_CHANGES` or identifies architectural flaws,
output a **Prioritized Remediation Action Matrix** sorting every finding by
Priority (`P0` to `P2`), linking to exact CL/Depot files and lines, citing
authoritative Central Skills documentation, grounding in LLM attention
mechanics, and prescribing concrete fixes.

### Priority Level Definitions

*   🚨 **P0 (`Blocker`)**: Critical violations that break structural validation
    (`missing BUILD file`), violate mandatory CL description hygiene (`missing
    MARKDOWN=true or EVALIN_REPORT`), or introduce broken/blackholed runtime
    configurations (`e.g., VPC egress without required Cloud DNS private zones,
    sidecar cert exchange crashes on port 443 block`).
*   ⚠️ **P1 (`High Impact`)**: Severe prompt engineering anti-patterns that
    induce trajectory non-determinism (`evalin` variance) or attention dilution:
    Caps-Lock checklist duplication across levels, `One Default, One Escape
    Hatch` violations (branching menus of options), exhaustive `Phase 1`
    questionnaires (10+ interrogation turns), or output token bloat requiring
    dual IaC + CLI + custom verification scripts simultaneously.
*   💡 **P2 (`Medium Polish`)**: Ergonomic polish and maintenance improvements:
    brittle prompt overfitting (caps-lock restrictions on internal Mermaid node
    IDs like `CR_TIER1_FE`), clarifying ambiguous environment variable drivers
    (`UNIX socket vs TCP endpoint strings`), or minor markdown formatting
    cleanup.

### Output Table Template

Priority             | Action Item & Summary    | Target CL Reference (`Depot File & Lines`)          | Authoritative Central Citation (`skill_creator`) | Underlying Mechanics & Logic                                                                | Concrete Recommended Fix
:------------------: | :----------------------- | :-------------------------------------------------- | :----------------------------------------------- | :------------------------------------------------------------------------------------------ | :-----------------------
🚨 **P0** (`Blocker`) | **{Short Action Title}** | `file://{path}#L{start}-L{end}` or `CL Description` | `file://.../SKILL.md#L...` or `reviewing.md`     | {Explain the exact machine learning / attention / runtime mechanics causing the failure.}   | {Prescribe exact, actionable engineering steps to resolve the issue.}
⚠️ **P1** (`High`)   | **{Short Action Title}** | `file://{path}#L{start}-L{end}`                     | `writing-guide.md` / `Principle N`               | {Explain the exact attention dilution, combinatorial explosion, or UX friction root cause.} | {Prescribe exact refactoring: e.g. prune questions, lock defaults, delete checklists.}
💡 **P2** (`Medium`)  | **{Short Action Title}** | `file://{path}#L{start}-L{end}`                     | `writing-guide.md` / `SKILL.md`                  | {Explain how prompt overfitting or driver ambiguity introduces developer friction.}         | {Prescribe precise cleanup or recommended comment guidance.}

--------------------------------------------------------------------------------

## 3. Good vs. Bad Skill Authoring Patterns

Use these concrete contrasting examples when explaining remediations across
review reports:

### 3.1 Caps-Lock Directives vs. Explaining the Why (`Principle 2`)

*   ❌ **Bad (`MUST/ALWAYS Smell / Over-Conditioning`)**:

    ```markdown
    MANDATORY SPECIFICATION #4: You MUST ALWAYS set ingress to INGRESS_TRAFFIC_INTERNAL_ONLY and you MUST check that public IPv4 is disabled! NEVER emit public IPs!
    ```

*   ✅ **Good (`Rationale & Context`)**:

    ```markdown
    Set internal application services to `INGRESS_TRAFFIC_INTERNAL_ONLY` and disable public IPv4 (`ipv4_enabled = false`) on databases — any public endpoint exposure bypasses our Cloud Armor Web Application Firewall screening and opens the data plane to public internet scanning.
    ```

### 3.2 Menu of Alternatives vs. One Default, One Escape Hatch (`writing-guide.md: lines 100-107`)

*   ❌ **Bad (`Branching Menu / $2^N$ Combinatorial Explosion`)**:

    ```markdown
    You can configure either a Global Application Load Balancer with Cloud CDN, or a Regional Application Load Balancer without Cloud CDN depending on user compliance preferences. Also choose between ALL_TRAFFIC egress or PRIVATE_RANGES_ONLY.
    ```

*   ✅ **Good (`Opinionated Golden Path with Escape Hatch`)**:

    ```markdown
    By default, deploy the standard 3-tier architecture with a Global Application Load Balancer (`enable_cdn = true`) and `ALL_TRAFFIC` Direct VPC Egress (`assets/main.tf`).
    *Exception*: Only use a Regional Application Load Balancer (`enable_cdn` omitted) if the user prompt explicitly mandates regional EU GDPR data residency.
    ```

### 3.3 Questionnaire Interrogation vs. Colonized Phase 1 (`UX Ergonomics`)

*   ❌ **Bad (`15-Topic Interrogation Loop`)**:

    ```markdown
    Before generating code, ask the user one at a time about: 1. Number of tiers, 2. Routing preference, 3. Load balancer topology, 4. Frontend integration, 5. Trailing traffic volume, 6. Container registry paths, 7. Database caching, 8. DB capacity/sizing, 9. High availability requirements, 10. GCP Region choices, 11. Compliance mandates, 12. Organization API perimeters, 13. Outbound internet egress rules, 14. Reliability SLAs, and 15. Observability/logging tiers.
    ```

*   ✅ **Good (`Colonized Phase 1 with Sensible Defaults`)**:

    ```markdown
    Assume the standard 80% baseline (`3-tier, US-Central1, Postgres Enterprise on Cloud SQL, Cloud Armor WAF, Direct VPC Egress`).
    Before generating code, only ask 2 mandatory disambiguation questions if unanswered in the prompt:
    1. Do you require global multi-region traffic (`CDN enabled`) or strictly localized European regional data residency?
    2. Do you need an in-memory Redis caching tier?
    ```

### 3.4 Duplicating Across Levels vs. Code as Single Source of Truth

*   ❌ **Bad (`Tripling Context Consumption`)**: `SKILL.md` lists 9 security
    rules, `references/non-negotiable-rules.md` copies the same 9 rules in
    caps-lock, `references/audit-checklist.md` copies them again, and
    `assets/main.tf` has them commented out.
*   ✅ **Good (`Code as the Single Source of Truth`)**: Hardcode the 9 exact
    security blocks (`ipv4_enabled = false`, `psc_enabled = true`,
    `ALL_TRAFFIC + DNS`) directly into `assets/main.tf` with inline HCL
    comments. Delete `non-negotiable-rules.md` and `audit-checklist.md`
    entirely. In `SKILL.md`, summarize the security architecture across 15 clean
    lines and instruct the agent to read `assets/main.tf`.
