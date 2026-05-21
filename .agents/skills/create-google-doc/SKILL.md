---
name: create-google-doc
description: Creates a fully populated Google Doc natively from a local source file on a Google Cloudtop workstation.
---

# Skill: Create Google Doc Natively on Cloudtop

This skill provides a reusable, highly secure document generator designed to execute natively on a Google Cloudtop (gLinux) workstation. It interfaces directly with the Google Drive API or Google Docs API using your active corporate credentials.

### 🔒 Pre-Flight Corporate Identity & Scopes Boundary
For compliance and corporate security, this skill enforces:
1.  **Active Corporate Account**: The active `gcloud` authenticated account MUST belong to the corporate **`@google.com`** domain.
2.  **Application Default Credentials (ADC) Scopes**: The local workstation token must be authenticated with active `drive` and `documents` scopes. If scopes are missing, the script automatically fails and prints the exact re-authentication command.

This approach delivers shareable corporate document links instantly without requiring remote SSH configuration.

## Execution Guide

Execute the script directly in your Cloudtop terminal:
```bash
python3 .agents/skills/create-google-doc/scripts/create_doc.py --src "artifacts/blueprint.md" --title "Artifact Blueprint: Customer Name"
```

***

## CLI Parameters

* `--src <file_path>`: (String, Required) Path to the local source file to populate the document.
* `--title <title>`: (String, Required) The final title of the generated Google Doc.

***

## Programmatic Integration

Other programmatic core tools or workflows can import the generator directly:

```python
import sys
from pathlib import Path
import sys
repo_root = Path(__file__).resolve().parents[3] # Dynamically resolve root
sys.path.append(str(repo_root / '.agents/skills/create-google-doc/scripts'))
from create_doc import create_google_doc_api

# Generate document programmatically
doc_link = create_google_doc_api(
    src_path="artifacts/blueprint.md",
    title="Technical Implementation Matrix"
)
print(f"Document successfully created: {doc_link}")
```

***

## Automated Pre-Formatted Document Generation

The script [`create_doc.py`](scripts/create_doc.py) natively integrates a powerful inline-styled HTML compilation engine that automatically styles Codelab markdown files into beautifully pre-formatted corporate documents upon generation.

### Styling Automation Features
- **Metadata Frontmatter**: Converts top-level YAML headers into custom grid tables.
- **Pagination**: Applies standard `page-break-before: always` layout boundaries before every major step heading (`##`).
- **Callout Callouts**: Wraps positive (`> aside positive`) and negative (`> aside negative`) aside blocks into distinct colored grid structures.
- **Code Blocks**: Embeds terminal commands and scripts natively into shaded light-gray containers.

By uploading the compiled inline HTML payload directly to the Google Drive API v3 storage endpoint specifying `mimeType='application/vnd.google-apps.document'`, Google Drive handles complete layout mappings natively, removing all client-side Apps Script extension maintenance.
