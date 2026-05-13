---
name: send-email
description: Sends secure, styled emails natively from the user's corporate Gmail account using a passwordless Remote SSH/SCP Bridge to their Cloudtop workstation.
---

# Skill: Generic Gmail Remote Cloudtop Bridge

This skill is a **generic, reusable system emailer** that acts as a **Remote Cloudtop Bridge**. It securely copies email payloads to your active gLinux Cloudtop virtual workstation via `scp` and executes the official pre-built corporate `gmail` CLI (`/google/bin/releases/gemini-agents-gmail/gmail`) remotely using passwordless `ssh` authenticated by your active `gcert` session.

This approach completely avoids local macOS codesign / security Gatekeeper blocks, standard OAuth consent screens, `credentials.json` client IDs, or local virtualenvs, providing a 100% secure, corporate-compliant, and zero-dependency mail delivery pipeline.

## Setup Guide

Follow these simple steps to configure your generic emailer in less than 30 seconds.

### Step 1: Add Cloudtop Host to `gcp_config.txt`
Open `/Users/shacharb/Downloads/ce-scale/gcp_config.txt` and append your Cloudtop virtual workstation host:

```text
cloudtop_host=your-username-dev-glinux.c.googlers.com
```

### Step 2: Execute natively
Run the script natively in your terminal using your standard Mac Python 3 interpreter (no packages needed!):

```bash
python3 _agents/skills/send-email/scripts/send_email.py --to "user@example.com" --subject "YOUR_SUBJECT" --body "YOUR_BODY" [options]
```

***

## CLI Parameters

*   `--to <emails>`: (String, Required) Comma-separated list of recipient email addresses.
*   `--subject <subject>`: (String, Required) The email subject line.
*   `--body <body>`: (String, Required) Raw text message, or a **local file path** (e.g. `artifacts/mtd_billing_audit.md` to parse and email the file contents).
*   `--html`: (Flag) Converts Markdown files and tables inside the body into a beautiful Google Cloud styled HTML card.
*   `--attachment <file_path>`: (String) Path to attach any local file (e.g., `artifacts/mtd_billing_audit.md` as a file attachment). The script automatically copies it to `/tmp` on Cloudtop to be natively attached by the remote binary.

***

## 🔗 Programmatic Inter-Skill Integrations

Since this skill is generic, other skills in the workspace can easily import it or call it to trigger alerts.

### Method A: Programmatic Python `import` (Recommended)
Add the script's directory to the Python path, and import `send_email_api` natively:

```python
import sys
import os

# Add the email skill scripts folder to python path
sys.path.append('/Users/shacharb/Downloads/ce-scale/_agents/skills/send-email/scripts')
from send_email import send_email_api

# Send email programmatically
send_email_api(
    to="user@example.com",
    subject="GKE Cluster High Cost Alert!",
    body_or_path="GKE Cluster sandbox-gke-1 has exceeded its billing thresholds.",
    is_html=False
)
```

### Method B: Subprocess CLI Call
Any shell, script, or non-python utility can execute the emailer via subprocess:

```python
import subprocess

subprocess.run([
    "python3",
    "_agents/skills/send-email/scripts/send_email.py",
    "--to", "user@example.com",
    "--subject", "MTD Sandbox Cost Audit",
    "--body", "artifacts/mtd_billing_audit.md",
    "--html"
], check=True)
```
