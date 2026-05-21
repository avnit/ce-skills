---
name: send-email
description: Sends secure, styled emails natively from the user's corporate Gmail account on a Google Cloudtop workstation.
---

# Skill: Generic Gmail Cloudtop Native Emailer

This skill is a **generic, reusable system emailer** designed to execute natively on a Google Cloudtop (gLinux) workstation. It interfaces directly with the official pre-built corporate `gmail` CLI (`/google/bin/releases/gemini-agents-gmail/gmail`) using your active `gcert` session.

This provides a 100% secure, corporate-compliant, and zero-dependency mail delivery pipeline.

## Execution Guide

Run the script directly inside your Cloudtop terminal session:

```bash
python3 .agents/skills/send-email/scripts/send_email.py --to "user@example.com" --subject "YOUR_SUBJECT" --body "YOUR_BODY" [options]
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
from pathlib import Path
import sys
repo_root = Path(__file__).resolve().parents[3] # Dynamically resolve root
sys.path.append(str(repo_root / '.agents/skills/send-email/scripts'))
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
    ".agents/skills/send-email/scripts/send_email.py",
    "--to", "user@example.com",
    "--subject", "MTD Sandbox Cost Audit",
    "--body", "artifacts/mtd_billing_audit.md",
    "--html"
], check=True)
```
