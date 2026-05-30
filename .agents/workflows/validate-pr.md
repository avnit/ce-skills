---
description: Orchestrate local E2E Prompt Evaluation of System A (Base branch) and System B (Workspace branch) on a Golden Prompt Suite, grading quality and structural drift inside the JetSki developer sandbox
---

This workflow automates the process of local prompt regression testing within a pure Git and GitHub local repository environment in JetSki. It checks out the base ref in a standard Git worktree, provisions twin isolated GCP sandbox projects, executes a set of golden prompts sequentially via the parent agent session, performs a recursive dictionary difference comparison, and outputs a detailed quality and trajectory report.

To prevent context contamination (i.e. the agent "cheating" by reading the active workspace or previous runs), it actively prunes cache files, invokes subagents under isolated workspace branch clones, and dynamically randomizes prompt execution parameters (VPC CIDRs, hex names, and regions) using predefined contract pools.

Required parameters from the user:
1. **Golden Prompt Suite**: A local path to the test suite JSON (e.g., `.agents/scripts/tiny_golden_prompts.json`).
2. **Target Base Ref**: The git branch to compare against (default: `origin/main`).

Steering Workflow:

1. **Phase 1: Intake & Verification & Sterile State Pruning**
   - Initialize/update the unindented HTML `task.md` table inside your conversation's brain directory.
   - Run `python3 .agents/skills/gcloud-auth-verification/scripts/verify_auth.py` to verify sandbox active authentication context.
   - Prune local caches to prevent the test agent from reading historic execution memories:
     ```bash
     rm -rf .tester_state/
     find . -name "*.pyc" -delete
     ```
   - Stream UI updates: *"Sterile State Pruning complete. Local caches cleared."*

2. **Phase 2: Local Staging Setup (Git Worktree)**
   - Create a detached git worktree checkout under `/tmp/skynet-base` from your remote origin baseline branch:
     ```bash
     git worktree add --detach /tmp/skynet-base origin/main
     ```
   - Stream an active progress notification in the JetSki UI: *"Created detached Git Worktree baseline staging under /tmp/skynet-base."*

3. **Phase 3: Twin GCP Projects Provisioning**
   - Provision two separate ephemeral GCP sandbox projects to prevent state contamination (such as pre-enabled APIs or IAM bindings overriding baseline states):
     - **Project A** (for System A Control run): `sysa-proj-[ID]`
     - **Project B** (for System B Candidate run): `sysb-proj-[ID]`
   - Stream UI updates: *"Provisioned twin isolated GCP staging projects."*

4. **Phase 4: Execution Run - System A (Control Baseline)**
   - **Fidelity Subagent Branching**: Instead of launching raw Python scripts that bypass MCP sockets and local workflows, the Parent Agent spawns a dedicated JetSki Subagent targeting the baseline `/tmp/skynet-base` worktree.
   - Call `invoke_subagent` with the following configuration:
     * **Workspace**: `branch` pointing to `/tmp/skynet-base` (guarantees that `main` branch versions of `.agents/workflows/` and skills are evaluated).
     * **Role**: `"System A Control Runner"`
     * **MCP Tools**: `enable_mcp_tools: true` (seamlessly bridges sockets/pipes for `f1`, `plx`, `moma`, etc.)
     * **GCP Project Context**: Bind sandbox project `sysa-proj-[ID]`.
   - Stream UI updates: *"Control System A Golden Prompts execution completed successfully."*

5. **Phase 5: Execution Run - System B (PR Workspace Candidate)**
   - **Candidate Subagent Staging**: The Parent Agent spawns a second, twin JetSki Subagent targeting the active workspace branch `/usr/local/google/home/shacharb/skynet`.
   - Call `invoke_subagent` with the following configuration:
     * **Workspace**: `inherit` or `branch` pointing to the developer's active branch directory (ensures that the modified workflows/skills under evaluation are actively executed).
     * **Role**: `"System B Candidate Runner"`
     * **MCP Tools**: `enable_mcp_tools: true`
     * **GCP Project Context**: Bind sandbox project `sysb-proj-[ID]`.
   - Stream UI updates: *"Candidate System B Golden Prompts execution completed successfully."*


6. **Phase 6: Evaluator Execution & Scoring (Pre-filtering)**
   - Execute the `evaluator.py` skill locally to recursively compare outputs and identify structural drift, running a pre-filtering pass that strips out non-functional metadata (such as generated timestamps, credentials, and ordering deltas):
     ```bash
     python3 .agents/skills/evaluator-engine/scripts/evaluator.py \
       --system-a-dir="/tmp/system_a_outputs" \
       --system-b-dir="/tmp/system_b_outputs" \
       --system-a-workspace="/tmp/skynet-base" \
       --system-b-workspace="/usr/local/google/home/shacharb/skynet" \
       --metrics-output="doc/eval_reports/pr_report.json" \
       --fail-on-regression=true \
       --min-quality=0.95
     ```

7. **Phase 7: Local Report Compilation & Delivery (HITL Gate)**
   - Generate the detailed markdown report:
     👉 `doc/eval_reports/pr_report.md`
   - Render the results (verdict, quality score, reliability uptime, process efficiency, and trajectory score) along with a pretty-printed JSON representation of the structural differences.
   - Stream a formatted summary table directly in the JetSki terminal console.
   - **Human-in-the-Loop Override Gate**: If the quality gate fails due to a benign change (e.g., structural refactoring of comments or flat-mapping config tags), the developer reviews `pr_report.md`, validates structural intent, and performs an explicit override bypass:
     ```text
     👉 /merge-pr --force --reason="Benign tag grouping refactoring"
     ```

8. **Phase 8: Ephemeral Sandbox Artifact Review Gate (Mandatory HITL)**
   - Before executing the cleanup scripts or destroying worktrees, the orchestrator **MUST explicitly pause and invoke the `ask_question` tool** to present an interactive modal:
     - **Question**: *"Would you like to keep the temporary Git worktrees and GCP sandbox projects active to manually review the generated codelab artifacts and logs, or should I clean them up now?"*
     - **Options**:
       - `"Automatically delete both GCP projects and unregister Git worktrees now (Recommended)"`
       - `"Retain all temporary staging environments and GCP resources for manual inspection"`
   - If the user chooses to clean up: proceed immediately to Phase 9.
   - If the user chooses to retain: skip the teardown commands, print the project IDs and worktree directories (`/tmp/skynet-base` and `/tmp/skynet-pr`) to the console, and conclude the workflow.

9. **Phase 9: Ephemeral Sandbox Teardown**
   - Run the cleanup utility to delete both provisioned sandbox cloud projects:
     ```bash
     python3 .agents/scripts/sandbox_cleanup.py --projects="sysa-proj-[ID],sysb-proj-[ID]"
     ```
   - Force remove and unregister the git worktrees to restore a pristine local workspace state:
     ```bash
     git worktree remove --force /tmp/skynet-base /tmp/skynet-pr
     ```
   - Stream final UI update: *"Staging sandbox teardown complete. PR validation finished."*
