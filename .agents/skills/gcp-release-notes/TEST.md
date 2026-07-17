# Skill Evaluation & Test Plan: gcp-release-notes

This document defines the evaluation test suite for verifying the `gcp-release-notes` skill, ensuring deterministic output formatting, table structure integrity, metadata completeness, and AI impact explanation quality.

---

## Test Scenarios & Evaluation Suite

### Test Case 1: Standard Topic Search with Formatted Table Output

- **Objective**: Verify keyword search against GCP release notes in BigQuery and clean Markdown table rendering.
- **Input Command**:
  ```bash
  python3 .agents/skills/gcp-release-notes/scripts/get_release_notes.py --topic "GKE" --limit 5
  ```
- **Expected Results**:
  1. Header section contains metadata: Topic (`"GKE"`), Release Type (`ALL`), Since date, Limit (`5`), and timestamp.
  2. Output renders as a standard 4-column Markdown table: `| Published At | Product Name | Type | Description |`.
  3. Cell descriptions convert HTML tags (`<p>`, `<li>`, `<a>`) into valid Markdown formatting (`<br>`, `* `, `[text](url)`).
  4. Internal pipe characters (`|`) are safely escaped as `\|`.

### Test Case 2: Release Type Filtering & Custom Date Scoping

- **Objective**: Verify exact filtering by release note type (`FEATURE`, `FIX`, `DEPRECATION`) and start date.
- **Input Command**:
  ```bash
  python3 .agents/skills/gcp-release-notes/scripts/get_release_notes.py --topic "Cloud Run" --type FEATURE --start-date 2025-01-01 --limit 3
  ```
- **Expected Results**:
  1. All returned rows have `Type` matching `FEATURE`.
  2. All `Published At` dates are `>= 2025-01-01`.
  3. Formatted table columns align properly without breaking table boundaries.

### Test Case 3: AI Architect Impact Explanation Column Evaluation

- **Objective**: Verify dynamic Gemini solutions-architect impact analysis integration.
- **Input Command**:
  ```bash
  python3 .agents/skills/gcp-release-notes/scripts/get_release_notes.py --topic "Cloud NGFW" --limit 1 --ai-explain
  ```
- **Expected Results**:
  1. Output renders a 5-column Markdown table: `| Published At | Product Name | Type | Description | AI Architect Impact |`.
  2. The `AI Architect Impact` cell contains a concise, single-sentence technical architectural impact statement.
  3. Text inside the AI impact cell does not contain raw newline characters that break Markdown table structure.

### Test Case 4: Output Mode & Local Artifact File Persistence

- **Objective**: Verify JSON output formatting and automatic file directory creation when saving artifacts.
- **Input Command**:
  ```bash
  python3 .agents/skills/gcp-release-notes/scripts/get_release_notes.py --topic "Vertex AI" --limit 2 --output json --save-artifact "tmp/eval_output/vertex_notes.json"
  ```
- **Expected Results**:
  1. Console and file output contain valid JSON formatted output array.
  2. Parent directory `tmp/eval_output/` is created automatically if non-existent.
  3. File content matches valid JSON structure with keys `published_at`, `product_name`, `release_note_type`, and `description`.

### Test Case 5: Product Catalog & Type Discovery

- **Objective**: Verify listing available GCP products and release note types.
- **Input Command**:
  ```bash
  python3 .agents/skills/gcp-release-notes/scripts/get_release_notes.py --list-products
  python3 .agents/skills/gcp-release-notes/scripts/get_release_notes.py --list-types
  ```
- **Expected Results**:
  1. Outputs alphabetical list of available products in a clean Markdown table.
  2. Caches product list to `products.md` for fast retrieval on subsequent runs.
  3. Outputs list of unique release note types (`FEATURE`, `FIX`, `DEPRECATION`, `ANNOUNCEMENT`, etc.).

---

## Evaluation Checklist

- [ ] **Frontmatter Validity**: `SKILL.md` contains valid YAML frontmatter with `name: gcp-release-notes` and concise `description`.
- [ ] **Formatted Table Layout Compliance**: Table outputs strictly maintain column alignment and use `<br>` tags to prevent breaking table row rendering.
- [ ] **HTML-to-Markdown Cleanliness**: HTML elements (`<p>`, `<b>`, `<code>`, `<a>`) are converted to clean Markdown syntax without artifacts or unescaped pipe characters.
- [ ] **AI Explanation Column Quality**: `--ai-explain` outputs relevant, concise technical architectural impact summaries under 30 words.
- [ ] **CLI Execution & Error Resilience**: Script runs without syntax errors, validates date arguments, and provides friendly authentication guidance on BigQuery errors.
