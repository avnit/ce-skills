---
name: skill-review
description: >-
  Performs authoritative Skill Reviewer and Central Skills (`skill_creator`) reviews on agent skills, skill CLs, and prompt designs. Evaluates structural validity, progressive disclosure architecture, LLM attention mechanics (`attention budget dilution`, `lost in the middle`), and UX ergonomics. Outputs standardized scorecards and prioritized remediation action matrices (`P0 Blockers`, `P1 High Impact`, `P2 Polish`). Use when reviewing a skill CL (via Critique link or CL number), auditing local skill directories, or diagnosing why a skill induces trajectory non-determinism (`evalin` variance), questionnaire fatigue, or output token bloat. Don't use for standard code reviews outside agent skills or for general feature implementation.
---

<!-- disableFinding(all) -->
<!-- mdlint off -->

# Skill Reviewer & Central Skills Agent (`skill-review`)

This skill orchestrates rigorous, high-signal reviews of AI agent skills and skill CLs. It evaluates targets across two non-negotiable dimensions:

1. **Agent Workflow & UX Ergonomics (`Signal over Noise`)**: Ensuring instructions provide an opinionated golden path without trapping developers in multi-turn questionnaires or inducing `lost in the middle` attention degradation.
2. **Central Skills Fleet Hygiene & Mechanics (`skill_creator` compliance)**: Enforcing strict structural hygiene (`BUILD` files, `OWNERS` boundaries, `EVAL.txtpb` task testing, and clean progressive disclosure).

## Workflow Overview

When invoked with a target skill (a Critique CL link, raw CL number, or local
skill directory path), execute this 6-phase review procedure:

1. **Phase 1: Structural & Fleet Hygiene Verification** (`blaze test` & file boundaries)
2.  **Phase 2: Cold Trigger Simulation & Metadata Evaluation** (`6 diagnostic
    prompts from frontmatter alone`)
3.  **Phase 3: Anatomy & Progressive Disclosure Audit** (`SKILL.md` vs
    `references/` vs `assets/`)
4.  **Phase 4: Skill Reviewer & LLM Attention Mechanics Audit** (`Signal vs
    Noise`, `Non-determinism`)
5.  **Phase 5: Evaluation & CL Description Quality Audit** (`EVAL.txtpb`,
    `EVALIN_REPORT`)
6.  **Phase 6: Scorecard & Remediation Matrix Generation** (`Scorecard +
    P0/P1/P2 Action Matrix + Failure Profiles`)

---

### Phase 1: Structural & Fleet Hygiene Verification

Before evaluating prompt wording, detect the workspace environment (`Google3 vs.
GitHub/OSS`) and verify physical structure:

*   **Environment Detection**:
    *   **Google3 Mode (`Piper/CitC/Fig/JJ`)**: If the path contains `google3/`
        or `/google/src/`, apply Google3 rules (`blaze test`, `BUILD` files,
        `OWNERS`, canonical `google3/...` links, and `EVALIN_REPORT` tags).
    *   **GitHub / OSS Mode (`Git / Open Source`)**: If running in an external
        repository or GitHub workspace, **do NOT require `BUILD` or `OWNERS`
        files**. Instead, verify valid **relative local file links
        (`./references/foo.md`)**, standard unit test runners (`pytest`, `bazel
        test`, or `npm test`), and clear PR/commit descriptions. Mark
        Google-specific scorecard rows (`blaze test`, `OWNERS`, `EVALIN_REPORT`)
        as **`NA (`GitHub / OSS Mode`)`**.

1.  **Fetch & Inspect Files**: If reviewing a Critique CL, use
    `fetch_changelist` to inspect `modified_paths`, `changelist_content`, and
    comments. If reviewing a local directory or GitHub PR, use `list_dir` and
    `view_file`.
2.  **Verify `BUILD` File Presence (`Google3 Mode Only`)**: Check that a `BUILD`
    (or `BUILD.bazel`) file exists along with `agent_skill(...)` and
    `validate_skill_test(...)` rules.
    *   *Rule*: Central permanent skills in Google3 (`learning/` or
        `third_party/skills/`) **MUST** include a `BUILD` file (`mark P0
        Blocker: FAIL if missing`). In GitHub/OSS mode, mark **`NA`**.
3.  **Run Structural Validation Target (`Google3 Mode Only`)**: If accessible in
    a Google3 workspace, run:

    ```bash
    blaze test {package_path}:validate_{skill_name_as_snake_case}_skill_test
    ```

4.  **Enforce Strict `OWNERS` File Boundaries (`Google3 Mode Only`)**:

    *   **Permanent Google3 Skills (`learning/...`, `third_party/skills/...`)**:
        **MUST** include an `OWNERS` file (`mark FAIL if missing`).
    *   **Experimental Google3 Skills (`experimental/users/...`)**: **MUST NOT**
        include an `OWNERS` file (`skill_creator/SKILL.md:L337-339`).
    *   **GitHub / OSS Mode**: Mark **`NA`** (`unless using repo-specific
        CODEOWNERS`).

5.  **Check for Extraneous Files**: Verify no `README.md`, `CHANGELOG.md`, or
    `INSTALLATION_GUIDE.md` files exist inside a Google3 skill directory (`in
    GitHub/OSS mode, a clean README.md is acceptable and encouraged`).

6.  **Run Automated Link & Path Verification (`check_skill_links`)**: To verify
    deterministically across both Google3 and GitHub/OSS modes that all Markdown
    links and pointers actually exist—and never use ephemeral user cloud paths
    (`/google/src/cloud/<user>/...`)—execute our dual-environment verification
    tool:

    ```bash
    blaze run //experimental/users/shacharb/skills/skill_review/scripts:check_skill_links -- --skill_path={path/to/SKILL.md}
    ```

    *(or `python3 scripts/check_skill_links.py --skill_path={path}` in
    standalone/GitHub environments via our `argparse` fallback). If broken links
    or ephemeral cloud paths are found, mark **`P0 Blocker: FAIL`**.

--------------------------------------------------------------------------------

### Phase 2: Cold Trigger Simulation & Metadata Evaluation

Evaluate skill triggering reliability **strictly from frontmatter metadata
(`name` + `description` + `Use when / Don't use for`) before reading the
SKILL.md body prose**:

1.  **Draft 6 Diagnostic Prompts**: While unbiased by body contents, draft 6
    natural user requests:
    *   **2 Explicit positive prompts**: The user names the exact task or tool
        (`e.g., "Review my agent skill at /path/to/skill"`).
    *   **2 Implicit positive prompts**: The underlying workflow need in natural
        phrasing without jargon or skill keywords (`e.g., "Why does the agent
        ignore the checklist I wrote when deploying?"`).
    *   **2 Adjacent negative prompts**: Tasks belonging to sibling skills or
        general LLM reasoning.
2.  **Evaluate Hit Rate**: Test whether a standard semantic router selects the
    skill across all 6 prompts:
    *   **6/6 Hit Rate (`Exemplary 5/5`)**: Triggers reliably across implicit
        phrasing right out of the box.
    *   **4-5/6 Hit Rate (`Warning 3/5`)**: Misses implicit paraphrases
        (`description lacks natural synonyms/verbs`).
    *   **$\le 3/6$ Hit Rate (`Invisible Expert Profile 1/5`)**: Fails to fire
        in real developer workflows regardless of how good the code body is.
3.  **Prescribe Exact Description Rewrites**: If hit rate is $< 6/6$,
    immediately diagnose the missing synonyms / boundary clauses and prescribe
    an exact replacement `description block` inside the `P1 Remediation Table`.

---

### Phase 3: Anatomy & Progressive Disclosure Audit

Evaluate how information is distributed across the skill hierarchy (`google3/learning/gemini/agents/skills/skill_creator/SKILL.md` anatomy):

1. **`SKILL.md` Body Density (`Level 2 Context`)**: Verify that `SKILL.md` stays lean and imperative (<200 lines). Information must live in either `SKILL.md` or `references/`, never both (`Duplicating Across Levels`).
2. **Reference Directory (`references/`) Usage**: 
   * Check that all reference files are one level deep and linked directly from `SKILL.md`.
   * **Audit for Checklist Duplication**: Verify reference files store static lookup schemas, API parameter tables, or multi-page documentation—NOT active behavioral instructions or caps-lock checklists (`CRITICAL CHECKLIST`, `MANDATORY SPECIFICATIONS`) that repeat what is already in `SKILL.md` or `assets/main.tf`.
3. **Code as the Single Source of Truth (`assets/`)**: Where static asset templates or IaC (`assets/main.tf`, `assets/config.yaml`) exist, verify that non-negotiable architectural rules (`ipv4_enabled = false`, `ALL_TRAFFIC + DNS overrides`) are pre-configured inside those templates as valid code blocks rather than duplicated in external markdown rules files.
4. **Helper CLIs (`clis/`)**: If the skill requires complex conditional utility logic, verify it is compiled as a unified binary under `clis/` rather than loose scripts in `scripts/`.

---

### Phase 4: Skill Reviewer & LLM Attention Mechanics Audit

Conduct an exhaustive diagnostic against the 5 critical LLM failure modes detailed in `references/llm-attention-mechanics.md`:

1. **The MUST/ALWAYS Caps-Lock Smell (`Over-Conditioning`)**:
   * Audit `SKILL.md` and `references/` for caps-lock shouting (`MUST`, `ALWAYS`, `NEVER`, `MANDATORY`).
   * **Justified Exceptions Rule**: Do NOT mark caps-lock as a violation if it represents a justified safety requirement (`e.g., NEVER delete production data without --confirm`), hard platform limit (`e.g., description MUST be under 1024 characters`), or irreversible consequence. ONLY flag caps-lock when it substitutes for causal engineering rationale (`"MUST/ALWAYS Smell"`).
   * Verify every non-obvious constraint pairs its directive with clear causal engineering rationale (`Explain the Why`) rather than louder caps-lock commands (`references/llm-attention-mechanics.md#1-attention-budget-degradation--lost-in-the-middle`).
2. **Menu of Alternatives (`Combinatorial Explosion & Non-Determinism`)**:
   * Check whether the skill presents branching options (e.g., `Global vs Regional`, `ALL_TRAFFIC vs PRIVATE`, `Enterprise vs Plus`) without locked-down defaults.
   * Enforce **One Default, One Escape Hatch** (`references/llm-attention-mechanics.md#2-combinatorial-explosion--menu-of-alternatives-non-determinism`). Require an **opinionated 80% golden path** by default, with alternatives relegated to conditional exceptions.
3. **The Questionnaire Interrogation Trap (`Phase 1 UX Fatigue`)**:
   * Check whether the workflow instructs the agent to ask the user more than 3 questions before generating code (`references/llm-attention-mechanics.md#3-the-questionnaire-interrogation-trap-phase-1-fatigue`).
   * Require **Colonizing Phase 1**: prune open-ended questionnaires down to 2–3 essential architectural forks (`e.g., # of tiers, EU residency, Redis cache`). Everything else must auto-deploy with sensible defaults.
4. **Output Token Bloat (`max_tokens` Truncation)**:
   * Check whether a single workflow turn demands multiple overlapping deliverables (`e.g., full Markdown report + Mermaid diagram + 700-line Terraform + bottom-up gcloud CLI script + custom Python script`).
   * Enforce **One Job Well** (`references/llm-attention-mechanics.md#4-output-token-bloat--truncation-max_tokens-exhaustion`): prune redundant code generation (`e.g., drop gcloud scripts and custom Python validation scripts when writing Terraform IaC`).
   * **Cohesive vs Bloat Rule**: Do NOT penalize skills that cleanly orchestrate cohesive sequential phases (`e.g., 1. Audit -> 2. Plan -> 3. Execute`) or use dedicated helpers in `clis/`. ONLY flag `One Job Well` violations when a skill forces multiple overlapping, redundant deliverables in a **single turn** or combines completely unrelated capabilities.
5. **Prompt Overfitting (`Brittle Micromanagement`)**:
   * Audit for brittle constraints (`e.g., forcing exact Mermaid node ID prefixes like CR_TIER1_FE`). Require general rules that survive paraphrasing.
6. **Domain Mechanics Verification**: Verify that commands, CLI flags, network routing rules, and API dependencies mentioned in `SKILL.md` or `assets/` actually work right out of the box without hidden gotchas (`e.g., Cloud Run ALL_TRAFFIC DNS requirements or sidecar cert exchanges`).
   * **Verification Grounding**: When auditing domain mechanics, CLI flags, and API dependencies, ONLY assert technical gotchas if verified directly using codebase search (`code_search`), tool declarations, or authoritative documentation. Never guess or invent failure modes on unfamiliar internal systems.
7. **Writing & Syntax Formatting Audit (`writing-guide.md`)**:
   * Verify **Imperative Form** (`Run the validator`, not `You should run`).
   * Verify **Placeholders use `{snake_case}`** (`--path={output_dir}`).
   * Verify **Code blocks include explicit language specifiers** (`starlark`, `python`, `bash`).
   * Verify **Options/Flags are formatted cleanly in Markdown tables** rather than dense prose.
8. **Path & Environment Variable Hygiene (`skill_creator` Standards)**:
   * Verify **`$VAR` Alias Preservation**: Enforce preserving environment variable aliases (`$CRITIQUE`, `$SPONGE`, `$BLAZE`) rather than hardcoding precompiled binary paths (`/google/bin/releases/...`) (`skill_creator/SKILL.md:L224-229 & L311-315`).
   * Verify **Canonical Link Paths**: Enforce stable `google3/...` or `/google/src/files/...` paths over ephemeral, user-specific cloud paths (`/google/src/cloud/<user>/...`) (`writing-guide.md:L137-155`).
9. **General Anti-Patterns Check (`writing-guide.md: lines 110-136`)**:
   * Check for and prune: **Explaining known concepts** (`e.g., explaining what gRPC is`), **Redundant restatements**, and **Universal generic advice** (`"Read the docs before proceeding"`, `"Handle errors appropriately"`, `"Test your changes before submitting"`).
10. **Post-Submit Reporting Issues Footer (`reviewing.md: lines 153-176`)**:
    *   For permanent skills (`learning/`, `third_party/skills/`), verify the
        `SKILL.md` ends with a `## Reporting Issues` footer linking to a
        Buganizer hotlist (`http://b/hotlists/...`). Omit for experimental user
        directories.

---

### Phase 5: Evaluation & CL Description Quality Audit (`eval_creator` & `reviewing.md`)

If reviewing an automated evaluation suite (`EVAL.txtpb`) or active Critique CL, audit against `eval_creator` (`google3/learning/gemini/agents/skills/eval_creator/SKILL.md`) and `reviewing.md`:

1. **`EVAL.txtpb` Suite Name & Structure (`eval_creator:L321`)**:
   * Verify `suite_name: "{skill_name}"` strictly matches the `snake_case` directory name.
   * Verify no unsupported `skills:`, `user_simulator:`, or `tags:` blocks exist on cases (`eval_creator:L347`). Verify every case has $\ge 1$ `expectations` (`eval_creator:L298`).
2. **Task Tests vs. Knowledge Quizzes (`eval_creator:L20-36`)**:
   * Verify test cases are **task tests** (`agent must execute actions, use tools, or generate concrete code/reports`) rather than knowledge quizzes (`"How do I use X?"` or `"Explain how X works"`).
3. **No Tool Name/Flag Leaks in Prompts (`eval_creator:L95 & L374`)**:
   * Verify natural user phrasing (`"Show me P0 bugs assigned to me"`). **Prompts MUST NEVER mention tool names, CLI commands, subcommands, or flags.** The `SKILL.md` teaches which tools to use; the prompt tests if the agent learned.
4. **Data Selection & Live Verification (`eval_creator:L99-152`)**:
   * Verify prompts use strong verifiable data (`real, stable data for read-only` or `$USER` / `my`). Audit for and reject hardcoded user-specific LDAPs (`e.g., basilm`) or ephemeral IDs.
5. **Outcome vs. Implementation Expectations (`eval_creator:L216-295`)**:
   * Assert **outcomes, not implementation details or attempt** (`"Agent returns bugs assigned to etaropa"` vs `"Agent uses issues search --assignee etaropa"`).
   * Verify graceful-failure expectations (`"If allocs exist... If no allocs are available..."`) when reading variable external state.
6. **Hermetic Fixture Setup/Teardown (`eval_creator:L186-215`)**:
   * Verify isolated setup (`setup.commands`) and teardown (`cleanup.commands`) per case when write paths or temporary resources (`Strategy A`) are exercised.
7. **CL Description Hygiene (`reviewing.md:L71-97`)**:
   * `### Skill creation prompt`: Must link to or paste the prompt/conversation used to build the skill.
   * `### Trajectories using skill:`: Must list verified `go/traj/?trajectory_id=...` execution links.
   * `EVALIN_REPORT`: Must contain `EVALIN_REPORT=https://evalin.corp.google.com/report/...` linking to a completed ablation report comparing with-skill vs without-skill.
   * `MARKDOWN=true`: Exactly `MARKDOWN=true` **MUST** be present in the CL description footer.

---

### Phase 6: Scorecard & Remediation Matrix Generation

Synthesize your findings and output the final review artifact or direct response using the standardized structure defined in `references/devrel-review-framework.md` and `references/report-template.md`:

* **Execution Modes**: By default (`Summary-First Mode`), output only the Executive Summary and the **Prioritized Remediation Action Matrix**. ONLY output the full 23-row formal scorecard table (`devrel-review-framework.md Sections 1.1-1.3`) when the user explicitly requests `"formal scorecard"`, `"complete audit"`, or when submitting a formal Critique review.
*   **Dynamic Output Adaptation (`Google3 vs. GitHub/OSS`)**:
    *   **In Google3 Mode (`Piper/CitC`)**: Render the full Google3 scorecard
        tables across Sections 1.1–1.3 exactly as defined (`with blaze test,
        OWNERS, canonical google3/ links, and Critique CL Table`).
    *   **In GitHub / OSS Mode (`Open Source / Git PRs`)**: Automatically
        **OMIT** the Google-only rows (`blaze test`, `OWNERS file`,
        `$CRITIQUE/$SPONGE aliases`, `canonical google3/ paths`, and `Buganizer
        footer`) from the rendered Content/Structural tables so the report
        remains clean and native to open source (`zero internal noise`). Replace
        Section 1.3/2.3 (`Critique CL Table`) with a **GitHub Pull Request &
        Test Verification Checklist** (`e.g., verifying PR description links to
        issue/origin prompt, verifying CI runner test output / pytest HTML
        report is linked, and verifying zero Google-internal URLs or
        confidential data leak into GitHub`).
*   **Progressive Loading Discipline**: Do NOT load all reference documents
    simultaneously inside active context. Load `llm-attention-mechanics.md` ONLY
    during Phase 4 when diagnosing attention failures. Load `report-template.md`
    ONLY when explicitly generating a comprehensive multi-section report file
    artifact.

1.  **Output the Formal Scorecard**: Include the `blaze test` status, Content
    Review Table, CL Review Table, and Red Flags
    (`references/devrel-review-framework.md`) when in Full Scorecard Mode
    (adapted dynamically to the environment).
2. **Output the Prioritized Remediation Action Matrix**: Sort all findings into `P0 Blockers`, `P1 High Impact`, and `P2 Polish` (`references/devrel-review-framework.md#2-prioritized-remediation-action-matrix-schema`).
3. **Cite Exact Guidance**: For every table row, provide exact Citations (`[file://path#L...](file:///path#L...)`) to target file lines AND official `skill_creator` frameworks. Explain the underlying LLM attention mechanics (`why it breaks`) and prescribe exact engineering fixes (`how to refactor`).
4.  **Comprehensive Review Reports**: When explicitly instructed to output a
    complete, standalone, or comprehensive review report artifact, strictly
    follow the multi-section layout and schema defined in
    `references/report-template.md` (adapted dynamically to Google3 vs.
    GitHub/OSS).

## References

* **Standardized Skill Review Report Template**: [report-template.md](references/report-template.md)
* **Skill Review Framework & Scorecard Schema**: [devrel-review-framework.md](references/devrel-review-framework.md)
* **LLM Attention Mechanics & Failure Modes**: [llm-attention-mechanics.md](references/llm-attention-mechanics.md)
*   **Official Central Skills Review Guide**:
    [reviewing.md](google3/learning/gemini/agents/skills/skill_creator/references/reviewing.md)
*   **Official Central Skills Writing Guide**:
    [writing-guide.md](google3/learning/gemini/agents/skills/skill_creator/references/writing-guide.md)
