---
name: qwiklabs-to-codelab
description: >-
  Converts hosted Qwiklabs tutorials into self-run Google Cloud Codelabs. Accepts inputs via Google Doc links, raw text files, or live browser page capture. Replaces hosted environment text with standard self-paced boilerplate while preserving 100% technical flow, command sequences, and architectural consistency.
---

# Skill: Qwiklabs to Codelab Conversion Automation

This skill automates transforming hosted laboratory tutorials (such as Qwiklabs environments) into high-quality, standalone, self-run Google Cloud Codelabs. It ensures zero loss of technical execution logic while elevating document formatting to meet core repository enterprise standards.

## 📥 Supported Input Mechanisms

The conversion orchestrator natively handles tutorial source intake across three distinct channels:
1. **Google Doc Links**: Extracts text and markdown blocks from multi-tab or single-tab design documents.
2. **Plain Text Inputs**: Directly parses raw unformatted `.txt` files or inline user block submissions.
3. **Live Browser Subagent Capture**: When a specific hosted lab web link is provided, the orchestrator triggers the **`browser_subagent`** tool to navigate to the URL, pause for manual authentication if a login gateway is displayed, capture fully rendered page contents, and extract underlying HTML/markdown structures cleanly.

---

## 🚨 CRITICAL RULE 1: ZERO Technical Deviation

To guarantee reliability and execution reproducibility, you **MUST maintain 100% absolute consistency** across all underlying technical implementation logic:
- **Command Preservation**: Every terminal command line, script block, flag definition, parameter string, and configuration block must be preserved exactly as provided in the source lab.
- **No Hallucination or Reinvention**: Do not attempt to optimize, rewrite, or change the architectural order of technical steps. If a command relies on specific file basenames or localized execution patterns, carry them forward without modification.
- **File & Asset Mapping**: If source steps reference local files or specific resource basenames, keep those names completely uniform throughout the generated tutorial.

---

## 🧹 CRITICAL RULE 2: Hosted to Self-Run Boilerplate Filtering

Hosted lab tutorials contain platform-specific mechanical instructions that do not apply to self-paced developer execution. You must apply strict content replacement logic:

### ❌ Sections to Strip (Hosted Mechanics)
Carefully evaluate the source content and eliminate all sections targeting:
- Instructions instructing users to "Click the **Start Lab** button".
- Warnings enforcing mandatory Incognito or private browsing session requirements (`> aside negative` callouts targeting student profile separation).
- Temporary credential allocation steps (e.g., noting student user accounts like `google1623327_student@qwiklabs.net` or auto-generated temporary passwords).
- Directives to select pre-provisioned Qwiklabs projects from dropdown menus.

### Inject Standard Self-Paced Setup Boilerplate
Replace the stripped hosted environment sections by prepending standard Codelab introductory blocks and mandatory self-paced setup boilerplate conforming to the `writer.md` persona standards:

#### Section 1: Introduction
Must outline a clear business problem, bulleted learning objectives starting with action verbs, and standard workspace prerequisites.

#### Section 2: Setup and Requirements
Must load and inject the exact, standard "Setup and Requirements" markdown boilerplate defined in the template resource: `.agents/skills/codelab-formatting/resources/setup_boilerplate.md`.

### Variable Mapping Hygiene
Map fixed Qwiklabs environment variables cleanly to self-paced extraction blocks. If the hosted lab relies on static project strings, replace them with dynamic query assignments:
```bash
export PROJECT_ID=$(gcloud config get-value project)
```

---

## 🎨 CRITICAL RULE 3: Codelab Formatting Integration

To make the converted tutorial an **amazing codelab**, ensure all output blocks strictly implement the formatting checklists defined in the **`codelab-formatting`** skill:
- **Frontmatter Metadata Block**: Enforce zero blank lines inside the top-level YAML configuration. Include standard keys: `id`, `summary`, `authors`, `keywords`, `layout: paginated`. Ensure exactly one blank line separates the closing `---` delimiter and the main tutorial header (`#`).
- **Duration Annotation**: Every step heading (`##`) MUST contain an explicit time duration estimation formatted exactly as `Duration: MM:SS` directly underneath the heading string.
- **Callout Blocks**: Use standard callout wrappers (`> aside positive` or `> aside negative`) sparingly to highlight important context or manual UI actions.
- **Proof of Life / Outcome Visualization**: For every critical deployment or testing command, ensure expected output visualization blocks are present, using formatting headers like `"You should see output similar to:"` followed by terminal blocks.

---

## 🧠 Conversion System Prompt / Guidelines

When executing a conversion pass, apply the following structured guidelines:

1. **Intake & Segment**: Read through the raw extracted tutorial content. Group steps logically to maintain step hygiene (aiming for one logical task per top-level step heading).
2. **Filter out Noise**: Strip all mentions of Qwiklabs support panels, temporary student passwords, or hosted timers.
3. **Reconstruct Frontmatter**: Derive an intuitive, lowercase hyphenated identifier string for the `id` parameter and compose a concise single-line summary.
4. **Author Output**: Generate the full markdown file (`.lab.md`) ensuring perfect code block indentation, clean markdown structures, and zero deviation in terminal command syntaxes.
5. **Deliver Clean Artifacts**: Output the path to the finalized markdown file directly to the user for local validation.
