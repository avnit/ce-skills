---
name: g3doc-formatter
description: Formats markdown files and codelabs to strictly adhere to official g3doc and G3Mark standards before publishing to CompanyDoc.
---

# g3doc Formatter Skill

This skill provides deterministic Python script formatting to prepare local Markdown files (`*.md` and `.lab.md`) for publication to Google internal **g3doc CompanyDoc** (`//depot/company/...`). It enforces compliance with official G3Mark rendering guidelines (`/google/src/files/head/depot/google3/corp/g3doc/docs/reference/markdown.md`).

## Usage Instructions

Run the Python formatting script directly via terminal before copying files into CitC / Piper:

```bash
python3 .agents/skills/g3doc-formatter/scripts/format_g3doc.py \
  --file "<path_to_markdown_file>" \
  --owner "<owner_ldap_or_team>" \
  [--in-place]
```

### Script Arguments:

- `--file`: (Required) Path to the markdown file to format.
- `--owner`: (Required) Owner username or team name (e.g., `ce-skills` or `shacharb`) for the freshness tag.
- `--in-place`: (Optional) Overwrites the file in place. If omitted, prints the formatted content to stdout.

## Transformations Applied

1. **Freshness Tag Injection**: Automatically inserts mandatory g3doc metadata (`<!--* freshness: { owner: '<owner>' reviewed: '<YYYY-MM-DD>' } *-->`) immediately below the H1 title.
2. **Table of Contents Macro**: Inserts `[TOC]` below the freshness tag if not already present.
3. **GitHub Alerts to G3Mark Callout Conversion**: Converts standard GitHub alert blocks into bolded g3doc callout keywords to mitigate G3Mark blockquote rendering bug `b/426022910`:
   - `> [!NOTE]` $\rightarrow$ `> **Note:**`
   - `> [!TIP]` $\rightarrow$ `> **Tip:**`
   - `> [!WARNING]` $\rightarrow$ `> **Warning:**`
   - `> [!IMPORTANT]` $\rightarrow$ `> **Important:**`
   - `> [!CAUTION]` $\rightarrow$ `> **Caution:**`
