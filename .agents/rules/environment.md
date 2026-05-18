---
trigger: always_on
---

# Running Environment & Multi-ADC Configuration Standard

All development, validation, and deployment tasks are performed in a highly specific Google Cloud multi-identity environment. Developers and agent processes must strictly adhere to these rules when executing commands, initializing credentials, or configuring API clients.

## 1. Environmental Context (Argolis)
- **Target Platform**: The target sandbox and testing environment is hosted within **Argolis** (Google's primary internal demonstration, testing, and prototyping environment).
- **Organization Policies**: Restrictive organization policies may be active. Standard sandbox provisioning and resource creation workflows must dynamically bypass or remediate organization policy blocks where possible.

## 2. Multi-Identity & Two Application Default Credentials (ADC)
The workstation is configured with two distinct authenticated Google Cloud identities. Each has different scopes of access and purposes:

### A. Sandbox / Admin Identity
- **Account Email Template**: `admin@<user-domain>.altostrat.com`
- **Primary Purpose**: Used for provisioned resource management, sandbox testing, codelab deployments, and standard Google Cloud resource administration.
- **Access Scopes**: Broad administration rights over sandbox projects.
- **Default Usage**: Most CLI operations, background runners, and scripts that communicate with test GCP resources should run under this identity.

### B. Corporate / Google Employee Identity
- **Account Email Template**: `<ldap>@google.com`
- **Primary Purpose**: Used for accessing internal corporate Google services (such as Google Docs, Gmail, internal APIs, and corporate developer platforms).
- **Access Scopes**: Corporate networks and employee-scoped GCP tools.

## 3. Authentication & Execution Guidelines
- **Strict Context Separation**: Before launching a workflow or deploying resources, verify which credential is active using the `gcloud-auth-verification` skill.
- **GCP API & CLI Execution**: Default to using the Sandbox/Admin account (`admin@<user-domain>.altostrat.com`) for resource provisioning, building, or automated QA testing.
- **Corporate Bridging**: Use `<ldap>@google.com` exclusively for operations that securely interact with corp systems (e.g., emailing via the `send-email` skill, or bridging files to Google Drive/Docs).
- **ADC Quota Alignment**: When running libraries (Python, Terraform) that rely on Application Default Credentials, ensure the ADC quota project is aligned with the active sandbox project.
