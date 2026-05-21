---
name: create-google-doc
description: Creates and synchronizes a Google Doc natively from a local Markdown source file on Cloudtop using OneDoc (go/onedoc).
---

# Skill: Create and Sync Google Doc Natively via OneDoc

This skill provides a seamless, robust document generator designed to execute natively on a Google Cloudtop workstation. By integrating **OneDoc (go/onedoc)** under the hood, it connects local Markdown files with Google Docs securely without causing Application Default Credentials (ADC) or scope conflicts with sandbox `gcloud` accounts.

### 🔒 Secure Local Execution
1.  **Credential Independence**: OneDoc leverages your active corporate Single Sign-On credentials natively. Unlike standard Drive API scripts, it does **NOT** require re-authenticating or changing active `gcloud` client configurations, resolving gcloud authorization scope conflicts.
2.  **Bidirectional Linking**: Creating a document automatically links the local Markdown file with the remote Google Doc by injecting tracking metadata (Doc URL and file ID) cleanly into the file's YAML frontmatter.

---

## Execution Guide

Execute the script directly in your Cloudtop terminal:
```bash
python3 .agents/skills/create-google-doc/scripts/create_doc.py --src "artifacts/blueprint.md" --title "Artifact Blueprint: Customer Name"
```

***

## CLI Parameters

* `--src <file_path>`: (String, Required) Path to the local Markdown source file to create and sync.
* `--title <title>`: (String, Required) The final title of the generated Google Doc.

***

## Programmatic Integration

Other workflows or scripts can import and run the generator directly:

```python
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[3] # Dynamically resolve root
sys.path.append(str(repo_root / '.agents/skills/create-google-doc/scripts'))
from create_doc import create_google_doc_api

# Generate document programmatically via OneDoc
doc_link = create_google_doc_api(
    src_path="artifacts/blueprint.md",
    title="Technical Implementation Matrix"
)
print(f"Document successfully created and linked: {doc_link}")
```

***

## Feature Support Natively Handled by OneDoc
OneDoc supports standard markdown formatting natively, making the generated Google Docs look clean, premium, and ready for review:
- **Metadata Frontmatter**: Respects YAML configuration headers.
- **Dynamic Synchronization**: Run subsequent syncs or updates directly via OneDoc commands (e.g. `onedoc push`).
