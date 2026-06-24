---
name: codelab-formatting
description: Strict Markdown standards for creating Google Cloud Codelabs.
---

# Skill: Codelab Markdown Formatting

This skill defines the strict Markdown standards for creating engaging Google Cloud Codelabs.

## Metadata

Each codelab created in Markdown must include the following metadata block at the top of the file:

```yaml
---
id: your-codelab-id
summary: A brief one-line summary of the lab (under 200 chars).
authors: Your Name
keywords: category:Cloud,product:BigQuery,docType:Codelab
layout: paginated
---
```

**CRITICAL RULES**:

- There must be NO blank lines inside the YAML block itself.
- There must be exactly one blank line between the closing `---` and the codelab title (`# Title`).
- **Keywords**: Do not add a space character after each comma. Example: `category:Cloud,product:BigQuery`.
- **Layout**: Always set to `paginated`.

## Steps and Headings

- **Title**: The title of your codelab should be the first line after the metadata and should use a Heading 1 tag (`#`).
- **Steps**: Each step of the codelab should be a Heading 2 (`##`). Prepend with step number (e.g., `## 1. Introduction`).
- **Headers**: Use `###`, `####`, `#####` for breaking down steps further.
- **Duration**: Each step MUST have a duration estimate in the format `Duration: MM:SS`.
  Example:

  ```markdown
  ## 1. Introduction

  Duration: 01:00
  ```

## Info Boxes (Callouts)

Use the following syntax for tips and warnings. Use sparingly (max 2-3 per step) and keep them concise (1-3 sentences).

- **Positive Note** (Tips, Best Practices):
  ```markdown
  > aside positive
  > This is a positive note. Use this style for best practices, shortcuts, or supplementary context.
  ```
- **Negative Note** (Cautionary, Important):
  ```markdown
  > aside negative
  > This is a negative note. Use this style for actions that could cause errors, incur unexpected costs, or lead to difficult-to-debug issues.
  ```

## Code Blocks

- Inline: Use backticks (`` `code` ``).
- Blocks: Use triple backticks with language specifier.
- Command-line snippets: Use triple backticks and the `console` directive or just `bash`/`shell`.

## Terminal-First File Creation

- When instructions require creating or editing a file, **prefer using `cat << 'EOF' > filename`** blocks. This allows the user to copy-paste the content directly into the terminal instead of opening an interactive editor like nano or vim. This reduces friction and cognitive load.

## Buttons

Wrap a link in `<button></button>` nodes: `markdown <button>[Download
Zip](https://www.google.com)</button>`

## Tone & Style

- **Conversational**: Use active voice and conversational tone ("we" and "you").
- **Verification Steps**: For ALL labs, verification steps MUST show the expected outcome. After an important action, show the reader what they should see. Use phrases like "You should see output similar to:".
