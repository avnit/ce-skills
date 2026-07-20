---
name: send-email
description: Sends secure, styled emails natively from your Cloudtop session using the Google Message Router (sendgmr).
---

# Skill: Google Message Router (GMR) Native Emailer

This skill is a **generic, reusable system emailer** designed to execute natively on a Google Cloudtop (gLinux) workstation. It interfaces directly with the official corporate **Google Message Router (GMR)** CLI (`${SENDGMR:-/google/bin/releases/gws-sre/files/sendgmr/sendgmr}`) using your active local **LOAS** (`gcert`) session.

### 🔒 Identity Independence & Zero-Conflict Auth

Because this skill leverages your active local LOAS credentials (`gcert`) to authenticate and route mail, it is **completely decoupled from your `gcloud` active credentials context**.

You can keep `gcloud` set to your sandbox admin identity (e.g., `admin@*.altostrat.com`) to perform provisioning and sandboxing tasks, and this emailer will still natively route corporate emails from your `@google.com` context without requiring any account switching!

---

## Execution Guide

Run the script directly inside your Cloudtop terminal session:

```bash
python3 .agents/skills/send-email/scripts/send_email.py --to "user@google.com" --subject "YOUR_SUBJECT" --body "YOUR_BODY" [options]
```

---

## CLI Parameters

- `--to <emails>`: (String, Required) Comma-separated list of recipient email addresses.
- `--subject <subject>`: (String, Required) The email subject line.
- `--body <body>`: (String, Required) Raw text message, or a **local file path** (e.g. `artifacts/mtd_billing_audit.md` to parse and email the file contents).
- `--html`: (Flag) Converts Markdown files and tables inside the body into a beautiful Google Cloud styled HTML card.
- `--attachment <file_path>`: (String) Path to attach any local file.

---

## 🔗 Programmatic Inter-Skill Integrations

Other skills or scripts can import `send_email_api` natively:

```python
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[3] # Dynamically resolve root
sys.path.append(str(repo_root / '.agents/skills/send-email/scripts'))
from send_email import send_email_api

# Send email programmatically
send_email_api(
    to="user@google.com",
    subject="Spend Review Alert",
    body_or_path="Sandbox project has exceeded spend thresholds.",
    is_html=False
)
```
