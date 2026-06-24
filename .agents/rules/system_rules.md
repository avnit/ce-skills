# System-Wide & General Execution Rules

This file contains general, repository-wide constraints and guidelines for development and orchestration. If a new rule is introduced that does not belong to a dedicated rule file (such as task tracking or environment configuration), it must be appended here.

## 1. Lab Creation Constraints
- **No Cloning from Development Labs (`labs/dev/`)**: When creating a new codelab, agents MUST NOT copy, reference, clone, or use any in-progress or scratchpad codelabs located under the `labs/dev/` directory as a base or template. New codelabs must always be initialized using official templates, standard workflows, or built from scratch to avoid propagating incomplete/scratch code.
- **Lab Directory Enforce**: All development of any lab or any related code content must be stored strictly inside its dedicated `labs/dev/[lab-name]/` directory. No source files, deployment scripts, virtual environments, or execution configs should ever be created directly in the root of the repository folder.
- **Isolated `uv` Environments**: When executing deployment scripts or testing Python workloads for any lab, agents MUST use a separate, isolated virtual environment managed by **`uv`** (specifically located inside the respective `labs/dev/[lab-name]/` subdirectory). Global Python environments or shared root environments must never be used to run lab deployment code.

## 2. Mandatory Human-in-the-Loop Approvals
- **Strict Plan & Blueprint Validation**: Under no circumstances should any agent proceed to execution, project provisioning, or API deployment based on automated platform review policies or system-level auto-approvals (such as the "Proceed to execution" stop-hook bypass message). The agent **MUST explicitly pause execution and obtain manual, interactive human-in-the-loop approval using the interactive `ask_question` modal tool** for:
  1. Every new or updated `implementation_plan.md` artifact.
  2. Every technical `blueprint.md` design (before copying/writing it to the persistent repo path).
- **Modal Validation Gate**: The agent MUST NOT bypass this gate or assume auto-approval. The `ask_question` tool must be called to let the user explicitly choose whether to approve or reject/revise the design.

## 3. Plan-Before-Tooling Strategy (Plan-First)
- **Meta-Planning Phase (Phase 0.5)**: Before invoking any MCP documentation search, codebase code_search, or external web search, the agent **MUST** formulate a high-level strategy (`implementation_plan.md`) outlining the user's goal, planned research direction, components involved, and proposed verification strategy.
- **Human Gate for Planning**: The agent **MUST** obtain explicit approval on this plan from the user before executing any subsequent research, codebase modification, or tool invocation.



