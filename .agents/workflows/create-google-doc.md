---
description: Orchestrate the automated generation of a Google Doc from a local Markdown file or pasted raw chat text using OneDoc.
---

# Workflow: Generate Google Doc from Markdown via OneDoc

This workflow steers the automated creation of a beautifully formatted Google Doc from either an existing workspace Markdown file or raw Markdown content copied into the chat, leveraging **OneDoc (go/onedoc)** natively on the workstation.

## Operational Workflow

### Phase 1: Intake Source Configuration

1. Ask the user if they would like to use an existing Markdown file in the workspace (e.g., `meeting/customer_a/one_pager.md`) or if they want to paste the Markdown content directly in the chat:
   - **Option A: Workspace File**:
     - Ask the user to supply the file path.
     - Resolve its absolute path.
   - **Option B: Copied Chat Text**:
     - Save the copied Markdown content to a temporary scratch file inside the conversation's active brain directory:
       `<appDataDir>/brain/<conversation-id>/scratch/doc_source.md`

### Phase 2: Google Doc Creation and Sync

1. Prompt the user to supply the final Title for the Google Doc.
2. Trigger the native OneDoc integration script to compile, upload, and synchronize the source Markdown file:
   ```bash
   python3 .agents/skills/create-google-doc/scripts/create_doc.py --src <SOURCE_FILE_PATH> --title "<DOCUMENT_TITLE>"
   ```
3. Capture the standard output from the execution. Extract the generated document link and present it to the user in the chat.
