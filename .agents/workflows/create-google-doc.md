---
description: Orchestrate the automated generation of a Google Doc from a local markdown file or pasted raw chat text using the secure corporate Remote Cloudtop Bridge.
---

# Workflow: Generate Google Doc from Markdown

This workflow steers the automated creation of a beautifully pre-formatted Google Doc from either an existing workspace Markdown file or raw Markdown content copied into the chat.

## Operational Workflow

### Phase 1: Corporate Identity & Auth Verification
1. Connect to the workspace authentication validation utility to verify which active credential is in use:
   ```bash
   python3 .agents/skills/gcloud-auth-verification/scripts/verify_auth.py
   ```
2. **CRITICAL IDENTITY RULE**: Deploying files to Google Docs requires access to corporate workspace endpoints. The active account **MUST** be a corporate `@google.com` account.
3. If the active account is a sandbox admin or test account (e.g., `admin@*.altostrat.com`):
   - Invoke the `ask_question` tool to prompt the user to switch to their corporate `@google.com` account.
   - Proactively configure the active account:
     ```bash
     gcloud config set account <ldap>@google.com
     ```

### Phase 2: Intake Source Configuration
1. Ask the user if they would like to use an existing Markdown file in the workspace (e.g., `meeting/customer_a/one_pager.md`) or if they want to paste the Markdown content directly in the chat:
   - **Option A: Workspace File**:
     - Ask the user to supply the file path.
     - Resolve its absolute path.
   - **Option B: Copied Chat Text**:
     - Save the copied Markdown content to a temporary scratch file inside the conversation's active brain directory:
       `<appDataDir>/brain/<conversation-id>/scratch/doc_source.md`

### Phase 3: Cloudtop Host Verification
1. Scan the `gcp_config.txt` file at the workspace root to verify that the `cloudtop_host` variable is present:
   ```text
   cloudtop_host=your-username-dev-glinux.c.googlers.com
   ```
2. If the host is missing, trigger an intake request using the `ask_question` tool to capture their Cloudtop workstation host, and write it dynamically to `gcp_config.txt`.

### Phase 4: Google Doc Creation
1. Prompt the user to supply the final Title for the Google Doc.
2. Trigger the Remote Cloudtop Bridge script to compile the source Markdown file into styled HTML, securely copy it to the Cloudtop workstation, and provision the Google Doc:
   ```bash
   python3 .agents/skills/create-google-doc/scripts/create_doc.py --src <SOURCE_FILE_PATH> --title "<DOCUMENT_TITLE>"
   ```
3. Capture the standard output from the execution. Extract the generated document link and present it beautifully to the user in the chat.
