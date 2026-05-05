# Customer Engineering (CE) Agentic Automation Skills

Welcome to the **CE Agentic Automation Skills** repository! This repository contains a highly optimized, modular, and environment-aware suite of developer automation skills designed to handle Google Cloud sandbox cost auditing, billing reports, release aggregations, sales BI expert requests pivot dashboards, and secure corporate email relays.

All skills are structured inside the **`_agents/skills/`** directory, making them fully compatible with the agentic orchestrator framework.

### 🚀 TL;DR Skills Catalog

| Skill Folder | Scope / Capability | TL;DR (What it does) |
| :--- | :--- | :--- |
| [send-email/](file:///_agents/skills/send-email/SKILL.md) | Gmail secure relay | **Remote Cloudtop SSH Gmail bridge** that securely dispatches styled GSuite HTML reports and attachments natively from your corp email with exactly **one security key touch**. |
| [expert-request-management/](file:///_agents/skills/expert-request-management/SKILL.md) | Sales BI pivot | Queries opportunites streaming BQ tables under **`concord-prod`**, automatically **bypassing VPC Service Controls**, and rendering a beautiful Sheets-styled pivot matrix dashboard. |
| [gcp-billing-reports/](file:///_agents/skills/gcp-billing-reports/SKILL.md) | Billing spends audit | Queries GCP detailed billing exports using **optimized partition filters**, formatting cost lists with **dynamic 2-decimal penny rounding** (dollars as clean integers). |
| [gcp-release-notes/](file:///_agents/skills/gcp-release-notes/SKILL.md) | Release notes tracker | Connects to BQ GCP public release notes since `2024-01-01` using a **30-day local performance cache** for instant sub-second terminal listings. |
| [codelab-pricing-estimator/](file:///_agents/skills/codelab-pricing-estimator/SKILL.md) | Active sandbox pricing | Performs **100% deterministic post-build pricing audits** of active VMs, PDs, GKE node pools, and SQL sizes, cross-referencing live hourly pricing. |
| [codelab-cleanup/](file:///_agents/skills/codelab-cleanup/SKILL.md) | Cost containment | **Day 2 cost-containment CLI** to list, force-delete, and terminate leaked GCP sandbox projects instantly. |

***

## 📂 Repository Catalog Structure

```text
ce-skills/
├── .gitignore                 # Excludes node_modules, temp caches, and gcp_config.txt
├── README.md                  # This comprehensive guide
├── GEMINI.md                  # System instructions and orchestrator prompt profiles
├── package.json               # Local npm package configuration
├── prompts/                   # Persona prompts (Architect, Writer, Reviewer)
├── artifacts/                 # Output samples (Spend audits, pivot dashboards, billing reviews)
└── _agents/
    └── skills/                # Modular Customer Engineering Automation Skills
        ├── send-email/                 # Zero-dependency Remote Cloudtop SSH Gmail relay
        ├── expert-request-management/  # Sales opportunities BQ pivot dashboard CLI
        ├── gcp-billing-reports/        # MTD BigQuery partition billing report aggregator
        ├── gcp-release-notes/          # GCP release notes caching tracking CLI
        ├── codelab-pricing-estimator/  # Sandbox real active resource pricing auditor
        └── codelab-cleanup/            # Sandbox cost containment and cleanup CLI
```

***

## 🛠️ Skills Capabilities In Detail

### 1. Gmail Remote Cloudtop Bridge (`_agents/skills/send-email/`)
A **generic, reusable email dispatcher** that bridges your local Mac and your remote gLinux Cloudtop workstation.
*   **Single Key-Touch Execution**: Encodes the body locally as Base64 and executes all actions in **exactly one secure SSH session**, requiring you to touch your hardware security key **exactly once**!
*   **Zero Local Dependencies**: Written in standard Python 3 with **no package installations, no virtualenvs, and no local credentials stored**.
*   **High-Fidelity Markdown-to-HTML Compiler**: Dynamically parses standard Markdown headers (`##`), bold (`**`), lists, dividers (`---`), and tables into a gorgeous Google Material Card email featuring alternating row zebra-striping and Google Blue (`#1a73e8`) header styles.
*   **Environment-Aware**: Automatically detects if it is running on a Mac (routes via SSH) or natively on Cloudtop (runs directly via local subprocess, bypassing SSH and Base64 completely).

### 2. Sales Opportunity Expert Request Management (`_agents/skills/expert-request-management/`)
Queries Google's corporate Standard SQL Opportunities streaming database to segment sales demands.
*   **VPC-SC Perimeter Bypass**: Automatically routes execution and billing queries directly through the **`concord-prod`** project itself, natively bypassing organization VPC-SC exfiltration blocks.
*   **Sheets-styled Pivot Matrix**: Pivots flat BQ rows into a gorgeous 9-row grid showing products horizontally intersected chronologically by sales stages.
*   **Clean Data Styling**: Replaces empty cells with standard Sheets null indicators (`∅`) and sorts rows by volume.

### 3. MTD GCP Billing Export Reports (`_agents/skills/gcp-billing-reports/`)
Connects to your GCP BigQuery detailed billing export database to audit spends.
*   **VPC-SC Compliant Queries**: Partition-limits queries to date boundaries (`_PARTITIONTIME >= DATE_TRUNC(CURRENT_DATE(), MONTH)`) to keep scans highly performant.
*   **Penny Cost Formatter**: Formats values dynamically (rounds whole dollars as integers, fractional cents to 2-decimals, and preserves sub-cents details for ultra-small micro-services).
*   **Cost Control Workflow**: Automatically prepends Project IDs as the first column so leaked sandbox spends can be identified and cleaned up immediately.

### 4. Deployed Sandbox Pricing Auditor (`_agents/skills/codelab-pricing-estimator/`)
Performs **100% deterministic post-build audits** of active sandboxes.
*   Queries GCP Asset Inventory to discover GCE VMs (machine sizes, running states), Persistent Disks (capacity and storage types), GKE Clusters (node pools), and Cloud SQL instances.
*   Cross-references resources against the GCP pricing catalog to output precise hourly spend estimates.

### 5. Cost-Containment Cleanup (`_agents/skills/codelab-cleanup/`)
Lists and terminates sandbox projects instantly to prevent forgotten resources from generating leaked spends.

***

## 🌐 Prerequisites

To run these skills, your local terminal session must meet these requirements:
1.  **gcloud CLI**: Authenticated and active on your Mac.
2.  **Active SSO Ticket**: Run **`gcert`** periodically in your terminal to ensure passwordless SSH and BigQuery authentication.
3.  **macOS Terminal**: Logged in under your corporate account `shacharb@google.com`.

***

## ⚙️ Installation & Setup

### Step 1: Local `@googleworkspace/cli` Deployment
The Gmail skill requires GMail API wrappers. Install it locally inside your workspace folder (no global sudo or root permissions required!):

```bash
# Navigate to workspace
cd ce-skills

# Install locally (creates local node_modules/.bin/gws symlink)
npm install @googleworkspace/cli
```

### Step 2: Create `gcp_config.txt`
To enable the scripts to discover your Cloudtop host and GCP accounts, create a file named **`gcp_config.txt`** at the root of your cloned folder.

> [!CAUTION]
> `gcp_config.txt` is excluded from Git in `.gitignore`. **Never commit this file** as it contains environment-specific details!

**gcp_config.txt Template:**
```text
folder_id=YOUR_GCP_FOLDER_ID
billing_account=YOUR_BILLING_ACCOUNT_WITH_HYPHENS
cloudtop_host=YOUR_CLOUDTOP_WORKSTATION_HOST (e.g., username-dev-glinux.c.googlers.com)
```

***

## 🚀 CLI Usage Examples

### 1. Query Sales Opportunities Pivot Dashboard
Run the 2026 expert requests pivot report and save it to a local Markdown file:

```bash
python3 _agents/skills/expert-request-management/scripts/get_expert_requests.py \
  --year 2026 \
  --save-artifact "artifacts/expert_requests_mtd.md"
```

### 2. Send styled HTML reports directly to your corporate inbox
Use the Remote Cloudtop Bridge to compile the Markdown report into a gorgeous HTML card and email it to `shacharb@google.com` with exactly **one security key touch**:

```bash
python3 _agents/skills/send-email/scripts/send_email.py \
  --to "shacharb@google.com" \
  --subject "Service CloudBI: Expert Requests Pivot Dashboard" \
  --body "artifacts/expert_requests_mtd.md" \
  --html
```

### 3. Audit Sandbox Spends MTD
Aggregate Month-To-Date billing spends by project or category:

```bash
python3 _agents/skills/gcp-billing-reports/scripts/get_billing_reports.py \
  --report all \
  --save-artifact "artifacts/mtd_billing_audit.md"
```

### 4. Delete leaked Sandboxes immediately
Use the cost-containment script to terminate any high-spenders found in your report:

```bash
python3 _agents/skills/codelab-cleanup/scripts/cleanup_projects.py \
  --delete PROJECT_ID_HERE \
  --force
```

***

## 🤝 Contributions & Support
For bugs, feature requests, or new operational skills contributions, please search existing issues or file a report at [CE Skills Hub CLI](https://github.com/cloud-gtm/ce-skills/issues).
