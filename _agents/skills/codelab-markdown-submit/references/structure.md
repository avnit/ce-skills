# Directory Structure

Codelabs in `google3` require a specific directory structure. All files within the directory are treated as parts of the codelab.

## Mandatory Files

- **`index.lab.md`**: The main Markdown content.
- **`OWNERS`**: Piper ownership file.
- **`METADATA`**: G3doc metadata file.

## Recommended Structure

```text
//google3/third_party/devsite/{tenant}/{lang}/codelabs/{id}/
├── index.lab.md        # Main content
├── OWNERS              # Ownership and approval
├── METADATA            # Buganizer and and freshness 
└── img/                # Images
    └── screenshot.png
```

### `OWNERS` File

You must include an `OWNERS` file with at least two reviewers. This is necessary for both code review and automated metadata extraction.

### `img/` Directory

Store all assets in a subdirectory to keep the root clean. Reference them relatively in your Markdown:
`![Alt Text](img/screenshot.png)`

### `METADATA` File

Create a `METADATA` file to route bugs to your team:

```text
doc_bug_component: {YOUR_COMPONENT_ID}
freshness: {
  review_date: { year: 2024 month: 10 day: 01 }
}
```
