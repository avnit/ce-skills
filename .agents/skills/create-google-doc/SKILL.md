---
name: create-google-doc
description: Creates a fully populated Google Doc natively from a local source file using a secure passwordless Remote Cloudtop Bridge.
---

# Skill: Create Google Doc via Remote Cloudtop Bridge

This skill provides a reusable, highly secure document generator that acts as a **Remote Cloudtop Bridge**. It securely copies markdown or text source files to your active gLinux Cloudtop virtual workstation via `scp` and executes internal Google API flows or standard CLI document builders remotely using passwordless `ssh` authenticated by your active corporate `gcert` session.

This completely decouples token storage from your local `gcloud` lab Application Default Credentials (ADC), preventing permissions conflicts while delivering shareable corporate document links instantly.

## Setup Guide

### Step 1: Verify Target Host in `gcp_config.txt`
Ensure your Cloudtop virtual workstation host is present in `gcp_config.txt` at your workspace root directory:
```text
cloudtop_host=your-username-dev-glinux.c.googlers.com
```

### Step 2: Execute Natively
Execute the script directly in your terminal:
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
