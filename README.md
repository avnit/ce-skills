# Customer Engineering (CE) Agentic Automation Skills

Welcome to the **CE Agentic Automation Skills** repository! This repository contains a highly optimized, modular, and environment-aware suite of developer automation skills, interactive UI workflows, and permanent agent rules designed to scale Google Cloud systems engineering operations.

---

## 🧭 Declarative Framework Workflows (`.agents/workflows/`)

Workflows are interactive, conversational execution guides activated natively via chat slash commands. They dictate step-by-step orchestration logic and user intake sequences:

| Slash Command               | Configuration File                                                           | Workflow Purpose & Execution Scope                                                                                                                                                                           |
| :-------------------------- | :--------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`/check-billing`**        | [check-billing.md](file:///.agents/workflows/check-billing.md)               | Orchestrates the automated generation of Month-To-Date (MTD) Google Cloud billing reports and cost reviews using BigQuery.                                                                                   |
| **`/create-codelab`**       | [create-codelab.md](file:///.agents/workflows/create-codelab.md)             | Orchestrates end-to-end generation, test project provisioning, hermetic validation, and delivery of premium Google Cloud Codelabs from initial user prompts.                                                 |
| **`/create-project`**       | [create-project.md](file:///.agents/workflows/create-project.md)             | Sub-orchestration workflow used to provision clean sandboxed GCP test projects and remove restrictive organization policies dynamically.                                                                     |
| **`/extract-requirements`** | [extract-requirements.md](file:///.agents/workflows/extract-requirements.md) | Orchestrates the automated evaluation of discovery call notes and transcripts to generate comprehensive customer artifacts (Blueprints, Gap Analyses, One-Pagers).                                           |
| **`/generate-adr`**         | [generate-adr.md](file:///.agents/workflows/generate-adr.md)                 | Orchestrates the end-to-end interactive scoping, remote WAF MCP catalog querying, CISO peer review, and professional authoring of a Google Cloud Architecture Decision Record (ADR).                         |
| **`/generate-diagram`**     | [generate-diagram.md](file:///.agents/workflows/generate-diagram.md)         | Orchestrates the automated generation of high-fidelity Google Cloud architecture diagrams natively from Codelabs, Terraform files, or Design blueprints.                                                     |
| **`/onboarding`**           | [onboarding.md](file:///.agents/workflows/onboarding.md)                     | **Master Onboarding sequence** to prepare local environments. Prompts developers via interactive write-in boxes to configure provisioning credentials (`gcp_config.txt`) and binds their primary CE Persona. |
| **`/open-bug`**             | [open-bug.md](file:///.agents/workflows/open-bug.md)                         | Automates opening Buganizer tracking tickets and issues for ce-skills under Component ID 2150801 using scripted CLI execution.                                                                               |
| **`/organize-workspace`**   | [organize-workspace.md](file:///.agents/workflows/organize-workspace.md)     | Performs structural layout sweeps to eliminate root-level clutter, compile decoupled markdown review tables, and relocate assets safely across defined namespaces.                                           |
| **`/publish-artifact`**     | [publish-artifact.md](file:///.agents/workflows/publish-artifact.md)         | Orchestrates the end-to-end publishing of local files or directories to internal g3doc CompanyDoc supporting instant live preview links.                                                                     |
| **`/qwiklabs-to-codelab`**  | [qwiklabs-to-codelab.md](file:///.agents/workflows/qwiklabs-to-codelab.md)   | Orchestrates the end-to-end automated conversion of hosted Qwiklabs tutorials into standalone, self-run Google Cloud Codelabs.                                                                               |
| **`/run-waf-audit`**        | [run-waf-audit.md](file:///.agents/workflows/run-waf-audit.md)               | Orchestrates automated ingestion of design blueprints, multi-pillar Well-Architected Framework (WAF) auditing, and ADR reporting.                                                                            |
| **`/system-validation`**    | [system-validation.md](file:///.agents/workflows/system-validation.md)       | Validate environmental readiness, `gcp_config.txt` configuration, background daemons, and MCP server accessibility.                                                                                          |
| **`/validate-codelab`**     | [validate-codelab.md](file:///.agents/workflows/validate-codelab.md)         | Orchestrates the end-to-end automated testing and validation of a codelab from a markdown file or HTTP link using persistent subshell execution.                                                             |
| **`/workspace-search`**     | [workspace-search.md](file:///.agents/workflows/workspace-search.md)         | Cross-corpus semantic search across Google Workspace (Gmail, Calendar, Drive, and Chat) using Context Service CLI.                                                                                           |

---

## 🛡️ Permanent Framework Rules (`.agents/rules/`)

Rules represent continuous boundary constraints injected into all active models using `trigger: always_on` frontmatter headers to enforce reliable developer experiences globally:

- **`tasks.md`**: Enforces the generation and continuous dynamic updates of a beautifully styled HTML table tracking board ([task.md](file:///task.md)) to guarantee native IDE visual preview tabs.
- **`persona.md`**: Configures the active model's primary focus target based on onboarding selections:
  1. **Practice CE**: Deep technical architecture, exact CLI flag validation, and precise topology diagrams.
  2. **Platform CE**: Broad landing zones, cross-cloud alignment, and strategic governance guardrails.
  3. **Outcome CE**: Speed-runs, low-latency validations, and immediate customer unblocking paths.

---

## 🚀 Comprehensive Programmatic Skills Catalog (`.agents/skills/`)

Skills are code-backed capability layers pairing instruction manifests (`SKILL.md`) with specialized execution tools (Python/Bash):

| Skill Directory                                                                                                 | Scope / Capability          | TL;DR Description                                                                                                  |
| :-------------------------------------------------------------------------------------------------------------- | :-------------------------- | :----------------------------------------------------------------------------------------------------------------- |
| [agent_waf_system/](file:///.agents/skills/agent_waf_system/SKILL.md)                                           | WAF ADR Engine              | Orchestrates interactive multi-agent discovery, constraint checks, and automated CISO gating for WAF designs.      |
| [closed-loop-learning/](file:///.agents/skills/closed-loop-learning/SKILL.md)                                   | Closed-loop RAG learning    | System for processing agent/test bugs into generalized lessons learned and uploading them to centralized RAG.      |
| [codelab-authenticity-validator/](file:///.agents/skills/codelab-authenticity-validator/SKILL.md)               | Conversion authenticity     | Deterministic validation checks verifying converted codelabs against live hosted source files.                     |
| [codelab-cleanup/](file:///.agents/skills/codelab-cleanup/SKILL.md)                                             | Cost containment            | Day 2 operations to list, check safety liens, and force-delete leaked GCP sandbox test projects instantly.         |
| [codelab-creation/](file:///.agents/skills/codelab-creation/SKILL.md)                                           | Master Codelab builder      | Guides multi-phase blueprints, formatting checklists, and testing factories to author production-ready tutorials.  |
| [codelab-formatting/](file:///.agents/skills/codelab-formatting/SKILL.md)                                       | Style syntax standards      | Strict metadata parsing standards and markdown layout templates for `.lab.md` files.                               |
| [codelab-markdown-submit/](file:///.agents/skills/codelab-markdown-submit/SKILL.md)                             | DevSite source submit       | Local `claat` preview validation, directory placement structure, and source repo change-list workflows.            |
| [codelab-memory/](file:///.agents/skills/codelab-memory/SKILL.md)                                               | Centralized RAG memory      | Interacts with global Vertex AI corpora to retrieve prior art and append newly solved technical traps.             |
| [codelab-pricing-estimator/](file:///.agents/skills/codelab-pricing-estimator/SKILL.md)                         | Active cost estimation      | Audits running cloud resources post-build against live pricing catalogs to render concrete hourly spend forecasts. |
| [codelab-validation/](file:///.agents/skills/codelab-validation/SKILL.md)                                       | Unified stateful QA routing | Interprets natural language steps statefully and executes commands via persistent hash-cached subshells.           |
| [codelab_audit_logging/](file:///.agents/skills/codelab_audit_logging/SKILL.md)                                 | Evidence extraction         | Extracts Cloud Audit logs compiling concrete resource lifecycle trace boards into lab outputs.                     |
| [creating_gcp_diagrams/](file:///.agents/skills/creating_gcp_diagrams/SKILL.md)                                 | Visual generation           | Translates raw Mermaid blocks into stunning, high-contrast Google Cloud styled image assets.                       |
| [custom-architect/](file:///.agents/skills/custom-architect/SKILL.md)                                           | Custom Architecture loop    | Cooperative Architect-Critic loop grounded using developer documentation tools.                                    |
| [customer-design-blueprint/](file:///.agents/skills/customer-design-blueprint/SKILL.md)                         | Design Blueprints           | Master framework for standard engineering design blueprints.                                                       |
| [customer-one-pager/](file:///.agents/skills/customer-one-pager/SKILL.md)                                       | Customer Context            | Outlines context, pain points, and suggested plans from discovery notes.                                           |
| [customer-test-plan/](file:///.agents/skills/customer-test-plan/SKILL.md)                                       | Validation Test Plans       | Unified test plans executing stateful validations using tester engine structures.                                  |
| [customer_gap_analysis/](file:///.agents/skills/customer_gap_analysis/SKILL.md)                                 | Capability Gap Matrix       | Builds detailed capability severity matrix mapping and technical recommendations.                                  |
| [demo-magic-simulation/](file:///.agents/skills/demo-magic-simulation/SKILL.md)                                 | Terminal Pace Simulators    | Compiles executable simulations capturing pacing details for terminal actions.                                     |
| [expert-request-management/](file:///.agents/skills/expert-request-management/SKILL.md)                         | Sales BI dashboarding       | Queries specific opportunities BQ tables rendering customized spreadsheet reporting tabs.                          |
| [extracting_requirements_from_meetings/](file:///.agents/skills/extracting_requirements_from_meetings/SKILL.md) | Transcript blueprinting     | Structures raw meeting notes into concrete technical requirements and solution architectures.                      |
| [g3doc-formatter/](file:///.agents/skills/g3doc-formatter/SKILL.md)                                             | Formatting compliance       | Formats markdown files and codelabs to strictly adhere to official g3doc and G3Mark standards.                     |
| [gcloud-auth-verification/](file:///.agents/skills/gcloud-auth-verification/SKILL.md)                           | Active Credentials Check    | Interactively verifies credentialed accounts and aligns active default environments.                               |
| [gcp-billing-reports/](file:///.agents/skills/gcp-billing-reports/SKILL.md)                                     | Partitioned spend list      | Connects to BigQuery billing exports to present dynamic Month-To-Date cost breakdowns per Project and SKU.         |
| [gcp-provisioning/](file:///.agents/skills/gcp-provisioning/SKILL.md)                                           | Project automation          | Provisions test projects, validates standard billing attachments, and strips organization policies.                |
| [gcp-release-notes/](file:///.agents/skills/gcp-release-notes/SKILL.md)                                         | Updates caching             | Queries GCP release note repositories utilizing sub-second caching routines for real-time lookups.                 |
| [git-update/](file:///.agents/skills/git-update/SKILL.md)                                                       | Stage, Commit, Push         | Guides local changes updates, remote fetches, and merge checks seamlessly.                                         |
| [lab-video-automation/](file:///.agents/skills/lab-video-automation/SKILL.md)                                   | Automated UI execution      | Controls visible Chrome profile execution windows over CDP pipes to support screen recording setups.               |
| [onboarding/](file:///.agents/skills/onboarding/SKILL.md)                                                       | Developer setup             | Automates developer setup including multi-user billing configs (`gcp_config.txt`), persona bindings, and sidecars. |
| [open-bug/](file:///.agents/skills/open-bug/SKILL.md)                                                           | Issue Tracking              | Automates opening Buganizer tracking tickets and issues under Component ID 2150801 using scripted CLI execution.   |
| [publish-artifact/](file:///.agents/skills/publish-artifact/SKILL.md)                                           | Live publishing             | Publishes generated artifacts to internal g3doc CompanyDoc supporting instant live preview links.                  |
| [qwiklabs-to-codelab/](file:///.agents/skills/qwiklabs-to-codelab/SKILL.md)                                     | Tutorial Conversion         | Enforces deterministic self-paced conversion from Qwiklabs pages or Docs files.                                    |
| [send-email/](file:///.agents/skills/send-email/SKILL.md)                                                       | Secure corp relay           | Remote Cloudtop SSH bridge dispatching styled corporate HTML messages and file attachments securely.               |
| [skill-creator/](file:///.agents/skills/skill-creator/SKILL.md)                                                 | Skill creator tool          | Guides creating, editing, testing, reviewing, and validating AI agent skills.                                      |
| [system-validation/](file:///.agents/skills/system-validation/SKILL.md)                                         | Environment readiness       | Validates onboarding parameters, gcp_config.txt, CitC workspaces, sidecars, and MCP server connectivity.           |
| [workspace-organizer/](file:///.agents/skills/workspace-organizer/SKILL.md)                                     | Clutter sweeps              | Enforces repository directory standards, audits root clutter, and organizes workspace files.                       |
| [workspace_agency_csa/](file:///.agents/skills/workspace_agency_csa/SKILL.md)                                   | Semantic CSA Search         | Cross-corpus Workspace searches across Gmail, Calendar, Drive, and Chat using the CSA CLI.                         |

---

## 📂 Master Repository Topology

```text
ce-skills/
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

---

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

---

## 🤝 Contributions & Support

To submit new programmatic skills, propose workflow sequences, or flag operational bugs, please file an issue report on the [CE Skills Upstream Repository](https://github.com/cloud-gtm/ce-skills/issues).
