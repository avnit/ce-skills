# Customer Engineering (CE) Agentic Automation Skills

Welcome to the **CE Agentic Automation Skills** repository! This repository contains a highly optimized, modular, and environment-aware suite of developer automation skills, interactive UI workflows, and permanent agent rules designed to scale Google Cloud systems engineering operations.

***

## 🧭 Declarative Framework Workflows (`.agents/workflows/`)

Workflows are interactive, conversational execution guides activated natively via chat slash commands. They dictate step-by-step orchestration logic and user intake sequences:

| Slash Command | Configuration File | Workflow Purpose & Execution Scope |
| :--- | :--- | :--- |
| **`/create-codelab`** | [create-codelab.md](file:///.agents/workflows/create-codelab.md) | Orchestrates end-to-end generation, test project provisioning, hermetic validation, and delivery of premium Google Cloud Codelabs from initial user prompts. |
| **`/onboarding`** | [onboarding.md](file:///.agents/workflows/onboarding.md) | **Master Onboarding sequence** to prepare local environments. Prompts developers via interactive write-in boxes to configure provisioning credentials (`gcp_config.txt`) and binds their primary CE Persona. |
| **`/organize-workspace`** | [organize-workspace.md](file:///.agents/workflows/organize-workspace.md) | Performs structural layout sweeps to eliminate root-level clutter, compile decoupled markdown review tables, and relocate assets safely across defined namespaces. |
| **`/create-project`** | [create-project.md](file:///.agents/workflows/create-project.md) | Sub-orchestration workflow used to provision clean sandboxed GCP test projects and remove restrictive organization policies dynamically. |
| **`/run-lab-video`** | [run-lab-video.md](file:///.agents/workflows/run-lab-video.md) | Sub-orchestration workflow automating terminal interactive executions inside Chrome profiles to support screen recording setups. |

***

## 🛡️ Permanent Framework Rules (`.agents/rules/`)

Rules represent continuous boundary constraints injected into all active models using `trigger: always_on` frontmatter headers to enforce reliable developer experiences globally:

* **`tasks.md`**: Enforces the generation and continuous dynamic updates of a beautifully styled HTML table tracking board ([task.md](file:///task.md)) to guarantee native IDE visual preview tabs.
* **`persona.md`**: Configures the active model's primary focus target based on onboarding selections:
  1. **Practice CE**: Deep technical architecture, exact CLI flag validation, and precise topology diagrams.
  2. **Platform CE**: Broad landing zones, cross-cloud alignment, and strategic governance guardrails.
  3. **Outcome CE**: Speed-runs, low-latency validations, and immediate customer unblocking paths.

***

## 🚀 Comprehensive Programmatic Skills Catalog (`.agents/skills/`)

Skills are code-backed capability layers pairing instruction manifests (`SKILL.md`) with specialized execution tools (Python/Bash):

| Skill Directory | Scope / Capability | TL;DR Description |
| :--- | :--- | :--- |
| [codelab-cleanup/](file:///.agents/skills/codelab-cleanup/SKILL.md) | Cost containment | Day 2 operations to list, force-delete, and terminate leaked GCP sandbox test projects instantly. |
| [codelab-creation/](file:///.agents/skills/codelab-creation/SKILL.md) | Master Codelab builder | Guides multi-phase blueprints, formatting checklists, and testing factories to author production-ready tutorials. |
| [codelab-formatting/](file:///.agents/skills/codelab-formatting/SKILL.md) | Style syntax standards | Strict metadata parsing standards and markdown layout templates for `.lab.md` files. |
| [codelab-markdown-submit/](file:///.agents/skills/codelab-markdown-submit/SKILL.md) | DevSite source submit | Local `claat` preview validation, directory placement structure, and source repo change-list workflows. |
| [codelab-memory/](file:///.agents/skills/codelab-memory/SKILL.md) | Centralized RAG memory | Interacts with global Vertex AI corpora to retrieve prior art and append newly solved technical traps. |
| [codelab-pricing-estimator/](file:///.agents/skills/codelab-pricing-estimator/SKILL.md) | Active cost estimation | Audits running cloud resources post-build against live pricing catalogs to render concrete hourly spend forecasts. |
| [codelab-validation/](file:///.agents/skills/codelab-validation/SKILL.md) | Unified stateful QA routing | Interprets natural language steps statefully and executes commands via persistent hash-cached subshells. |
| [codelab_audit_logging/](file:///.agents/skills/codelab_audit_logging/SKILL.md) | Evidence extraction | Extracts Cloud Audit logs compiling concrete resource lifecycle trace boards into lab outputs. |
| [creating-gcp-diagrams/](file:///.agents/skills/creating-gcp-diagrams/SKILL.md) | Visual generation | Translates raw Mermaid blocks into stunning, high-contrast Google Cloud styled image assets. |
| [expert-request-management/](file:///.agents/skills/expert-request-management/SKILL.md) | Sales BI dashboarding | Queries specific opportunities BQ tables rendering customized spreadsheet reporting tabs. |
| [extracting_requirements_from_meetings/](file:///.agents/skills/extracting_requirements_from_meetings/SKILL.md) | Transcript blueprinting | Structures raw meeting notes into concrete technical requirements and solution architectures. |
| [gcp-billing-reports/](file:///.agents/skills/gcp-billing-reports/SKILL.md) | Partitioned spend list | Aggregates detailed billing exports using penny-rounding logic for optimized executive lists. |
| [gcp-provisioning/](file:///.agents/skills/gcp-provisioning/SKILL.md) | Project automation | Provisions test projects, validates standard billing attachments, and strips organization policies. |
| [gcp-release-notes/](file:///.agents/skills/gcp-release-notes/SKILL.md) | Updates caching | Queries GCP release note repositories utilizing sub-second caching routines for real-time lookups. |
| [lab-video-automation/](file:///.agents/skills/lab-video-automation/SKILL.md) | Automated UI execution | Controls visible Chrome profile execution windows using Playwright to support external screen recording setups, paired with optional Gemini self-healing recovery routines. |
| [send-email/](file:///.agents/skills/send-email/SKILL.md) | Secure corp relay | Remote Cloudtop SSH bridge dispatching styled corporate HTML messages and file attachments securely. |

***

## 📂 Master Repository Topology

```text
skynet/
├── .gitignore                 # Excludes local temporary caches, lock files, and generated config files
├── README.md                  # This comprehensive alignment documentation
├── package.json               # Standard Node.js package dependencies
├── prompts/                   # Isolated sub-agent persona definitions (Architect, Writer, Reviewer)
├── artifacts/                 # Output samples and framework diagnostic audit reports
├── .agents/                   # Declarative Framework Namespace
│   ├── workflows/             # Interactive conversational slash-command execution files
│   └── rules/                 # Permanent always-on behavioral boundary conditions
└── .agents/                   # Programmatic Core Namespace
    └── skills/                # Modular python/shell tools featuring isolated dependency lockfiles
```

***

## ⚙️ Environment Setup & Onboarding

### 1. Agentic Initialization (Recommended Path)
Rather than creating credential files manually, **launch the interactive onboarding workflow directly in your chat**:
```text
/onboarding
```
The agent will dynamically solicit required workspace parameters (`folder_id`, `billing_account`) via secure UI input dialogues, automatically output a perfectly valid `gcp_config.txt` to disk, and mount your customized Systems Engineering Persona target instantly!

### 2. Local Installation
Certain utility scripts use standard module layers. Synchronize dependencies using modern resolvers:
```bash
# Authenticate with corporate credentials first:
gcert

# Python skills featuring dedicated lockfiles isolate execution automatically via:
uv run --project .agents/skills/<skill_folder>/ scripts/<script_name>.py
```

***

## 🤝 Contributions & Support
To submit new programmatic skills, propose workflow sequences, or flag operational bugs, please file an issue report on the [CE Skills Upstream Repository](https://github.com/cloud-gtm/ce-skills/issues).
