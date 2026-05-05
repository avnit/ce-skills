# Customer Engineering (CE) Agentic Automation Skills

Welcome to the **CE Agentic Automation Skills** repository! This repository contains a highly optimized, modular, and environment-aware suite of developer automation skills designed to handle Google Cloud sandbox cost auditing, billing reports, release aggregations, sales BI expert requests pivot dashboards, and secure corporate email relays.

All skills are structured inside the **`_agents/skills/`** directory, making them fully compatible with the agentic orchestrator framework.

### 🚀 TL;DR Skills Catalog

| Skill Folder | Scope / Capability | TL;DR (What it does) |
| :--- | :--- | :--- |
| [codelab-cleanup/](file:///_agents/skills/codelab-cleanup/SKILL.md) | Cost containment | **Day 2 cost-containment CLI** to list, force-delete, and terminate leaked GCP sandbox projects instantly to prevent leaked spends. |
| [codelab-creation/](file:///_agents/skills/codelab-creation/SKILL.md) | Codelab orchestration | **Master orchestrator workflow** for blueprinting, content writing, and statefully validating DevSite codelabs natively inside google3/CitC. |
| [codelab-formatting/](file:///_agents/skills/codelab-formatting/SKILL.md) | Codelab standards | Strict linting and styling rules for Google Cloud Codelab Markdown (.lab.md) specifications. |
| [codelab-markdown-submit/](file:///_agents/skills/codelab-markdown-submit/SKILL.md) | Codelab submission | Staging, local validation (claat/devsite2), ownership configuration, and submitting Markdown codelabs natively in google3. |
| [codelab-memory/](file:///_agents/skills/codelab-memory/SKILL.md) | RAG learning cache | Connects to the centralized RAG system to store and query lessons learned from previous runs. |
| [codelab-pricing-estimator/](file:///_agents/skills/codelab-pricing-estimator/SKILL.md) | Active sandbox pricing | Performs **100% deterministic post-build pricing audits** of active VMs, PDs, GKE node pools, and SQL sizes, cross-referencing live hourly catalog. |
| [codelab-testing/](file:///_agents/skills/codelab-testing/SKILL.md) | Deterministic QA | QA test-runner evaluating CLI and code block outputs via deterministic shell scripts. |
| [codelab-validation/](file:///_agents/skills/codelab-validation/SKILL.md) | Stateful QA | Validates natural language tutorial steps statefully with prerequisite gating for long-running setups. |
| [codelab_audit_logging/](file:///_agents/skills/codelab_audit_logging/SKILL.md) | VPC audit logs | Gathers VPC/GCP audit logs to generate a clear table of evidence in the lab directories. |
| [creating-gcp-diagrams/](file:///_agents/skills/creating-gcp-diagrams/SKILL.md) | Architecture diagrams | Converts Mermaid code into styled Google Cloud architecture diagrams and premium images. |
| [expert-request-management/](file:///_agents/skills/expert-request-management/SKILL.md) | Sales BI pivot | Queries opportunites streaming BQ tables under **`concord-prod`**, automatically **bypassing VPC Service Controls**, and rendering a beautiful Sheets-styled pivot matrix dashboard. |
| [extracting_requirements_from_meetings/](file:///_agents/skills/extracting_requirements_from_meetings/SKILL.md) | Requirement extraction | Parses raw meeting transcripts/notes into formal blueprints, deal drivers, and technical requirements. |
| [gcp-billing-reports/](file:///_agents/skills/gcp-billing-reports/SKILL.md) | Billing spends audit | Queries GCP detailed billing exports using **optimized partition filters**, formatting cost lists with **dynamic 2-decimal penny rounding** (dollars as clean integers). |
| [gcp-provisioning/](file:///_agents/skills/gcp-provisioning/SKILL.md) | Argolis provisioning | Provisions GCP sandbox test projects, binds billing accounts, and disables organizational policies. |
| [gcp-release-notes/](file:///_agents/skills/gcp-release-notes/SKILL.md) | Release tracker | Connects to BQ GCP public release notes since `2024-01-01` using a **30-day local performance cache** for instant sub-second terminal listings. |
| [send-email/](file:///_agents/skills/send-email/SKILL.md) | Gmail secure relay | **Remote Cloudtop SSH Gmail bridge** that securely dispatches styled GSuite HTML reports and attachments natively from your corp email with exactly **one security key touch**. |

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

## 🤝 Contributions & Support
For bugs, feature requests, or new operational skills contributions, please search existing issues or file a report at [CE Skills Hub CLI](https://github.com/cloud-gtm/ce-skills/issues).
