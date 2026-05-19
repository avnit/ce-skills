# Metadata Reference

Each codelab authored in Markdown must include a YAML metadata block at the top of the file:

```markdown
---
id: devsite/codelabs/my-tutorial
summary: Learn how to perform X using Y in this tutorial.
status: [published]
authors: [your-ldap]
categories: cloud, devsite
tags: web
duration: 10:00
description: A deeper description of the tutorial.
feedback_link: http://go/devsite-bug

---
```

> [!IMPORTANT]
> Always ensure there is an empty line before the closing `---` of the metadata block. Without it, some parsers (like `claat` via Goldmark) might fail to recognize the metadata block and error out with `invalid metadata format`.

## Required Fields

- **`id`**: Unique identifier for the codelab. Usually matches the directory path.
- **`summary`**: A one-sentence description.
- **`authors`**: Comma-separated list of LDAPs.
- **`status`**: Current status, e.g., `[published]`, `[draft]`.
- **`categories`**: Relevant categories for discovery.

## Optional Fields

- **`duration`**: Estimated time to complete in minutes. **Note**: Always use `MM:SS` format (e.g., `10:00` for 10 minutes) to ensure correct parsing by `claat`.
- **`tags`**: Discovery tags.
- **`feedback_link`**: URL for feedback (Buganizer).
- **`project`**: Path to the `_project.yaml` file (e.g., `/devsite/_project.yaml`).
- **`book`**: Path to the `_book.yaml` file (e.g., `/devsite/_book.yaml`).
- **`layout`**: `paginated` (default) or `scrolling`.
- **`robots`**: `noindex` to hide from search.
