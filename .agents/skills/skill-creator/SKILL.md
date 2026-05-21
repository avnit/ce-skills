---
name: skill-creator
description: >-
  Guides creating, editing, testing, reviewing, and validating AI agent skills.
  Use when building new skills, updating existing skills (any change in or under
  a directory containing a SKILL.md), writing TEST.md test plans,
  or running skill tests.
---

# Skill: Creator of Agent Skills

This skill provides guidance for the full lifecycle of agent skills in a native, non-google3 workspace environment: creation, testing, review, and validation.

## About Skills

Skills are **cheatsheets, not documentation.** They're the gotchas, quick recipes, and procedural knowledge that an experienced engineer would pass on to a teammate — the things no model can reliably know from training data alone. They are not manuals, tutorials, or comprehensive references.

A good skill reads like a senior engineer's notes: terse, opinionated, full of "do this, not that" and "watch out for X." If you find yourself writing paragraphs of explanation, you're writing docs, not a skill.

### What Skills Provide

1.  **Quick recipes** - Exact commands and patterns for common tasks
2.  **Gotchas and pitfalls** - What the agent will get wrong without help
3.  **Domain-specific knowledge** - Schemas, business logic, internal conventions
4.  **Bundled scripts** - Short, deterministic scripts for fragile/repetitive operations

Skills shouldn't contain heavy abstractions like libraries. If code is needed, an agent should always bias towards reusing existing interfaces, but if it needs to build its own tooling, it should do that under the skill's `scripts/` directory.

### When to Create a Skill (and When Not To)

**Create a skill when:**

*   The agent cannot reliably do the job without it, even with good prompts.
*   The workflow is real, recurring, and stable (not hypothetical or volatile).
*   The procedure has branching logic, scripts, or domain-specific knowledge.
*   Consistency matters — getting it wrong has real consequences.

**Don't create a skill when:**

*   It's a one-off task (inline instructions in the conversation are fine).
*   The agent already handles it reliably without help.
*   The procedure changes frequently (skills work best when workflows stabilize).

---

## Skill Structure

Every skill resides under the **`.agents/skills/`** directory and follows this structure:

```
.agents/skills/skill_name/
├── SKILL.md              # Required: metadata + cheatsheet instructions
├── scripts/              # Executable Python or Bash scripts
├── references/           # Supplementary schemas, gotchas, or detailed cheatsheets
└── assets/               # Static files used in output (templates, examples)
```

### SKILL.md Structure

*   **Frontmatter** (YAML): Contains `name` (kebab-case, e.g., `gcp-billing-reports`) and `description` (third-person capability statement, under 1024 chars). These are the **only** things the agent reads to trigger a skill.
*   **Body** (Markdown): Procedural cheatsheet instructions loaded AFTER the skill triggers. Keep under **500 lines** to save context window tokens.

---

## Execution Guide: Initializing a New Skill

To automatically initialize a clean, pre-populated skill directory, execute the initialization script:

```bash
python3 .agents/skills/skill-creator/scripts/init_skill.py --name <your-skill-name>
```

*   `<your-skill-name>`: The name of your new skill in **kebab-case** (e.g. `gke-ingress-pvc`). The script will automatically create the structural folders and pre-populate `SKILL.md`.

---

## Design & Writing Principles

### 1. Concise is Key
The context window is shared with system prompts and conversation history. Prefer concise examples over verbose explanations. Challenge each piece: "Does the agent really need this?"

### 2. Verify, Don't Trust
Include runnable validation commands, expected outputs, or concrete success criteria. If the agent cannot test whether it followed the instructions correctly, the instruction is too vague.

### 3. Avoid Menus of Alternatives
Provide **one default** with a clear escape hatch, not a list of choices:
*   ✅ "Use `pdfplumber` for text extraction. For scanned PDFs requiring OCR, use `pytesseract` instead."
*   ❌ "You can use `pypdf`, or `pdfplumber`, or `PyMuPDF`..."

### 4. Design Scripts like Tiny CLIs
*   Run from the command line with deterministic stdout.
*   Fail loudly with clear error codes (never return empty results silently).
*   Handle errors explicitly inside the script; do not punt them back to the agent.

---

## Test and Commit Workflow

1.  **Write a `TEST.md` (Optional)**: Create a test plan to verify your skill works against real prompts.
2.  **Commit Changes**: Stage and commit the new skill directory onto your active Git branch:
    ```bash
    git add .agents/skills/<your_skill_name>/
    git commit -m "feat: Initialize <your-skill-name> skill"
    git push origin <your_branch>
    ```

***

## Automated Skill Reviewer Subagent

For automated compliance and quality audits of your skill directory, you can define and invoke the specialized **`skill-reviewer`** subagent:
*   **System Prompt Reference**: See [skill_reviewer_prompt.md](references/skill_reviewer_prompt.md) for details.
*   **How to Invoke**: Call `invoke_subagent` with the subagent name set to `skill-reviewer` and provide the target skill path in the prompt.

