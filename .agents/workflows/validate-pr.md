---
description: Orchestrate local E2E Prompt Evaluation of System A (Base branch) and System B (Candidate branch) on a Golden Prompt Suite, grading quality and structural drift inside the JetSki developer sandbox
---

This workflow automates the process of local prompt regression testing within a pure Git and GitHub local repository environment in JetSki. To guarantee 100% sterile execution and prevent "cheating" (context contamination) or concurrent environment collisions, both System A (Baseline) and System B (Candidate) are executed strictly inside isolated Git worktrees checked out from fully pushed remote commits, utilizing decoupled local mailboxes and process-level `CLOUDSDK_CORE_PROJECT` project isolation.

## Dynamic Isolation and Thread-Safety Contract
1. **Commit-First Testing**: Validations are executed strictly against fully committed and pushed branch commits. No uncommitted active workspace files are allowed in the sandboxes.
2. **decoupled Local Mailboxes**: The validation framework (`.agents/`) is staged locally in each worktree so that step caches, status trackings, and mailboxes (`.agents/mailboxes/`) are completely private and decoupled per run.
3. **Active Project Isolation**: To prevent concurrent `gcloud config set project` collisions between parallel process trees sharing the same Unix user, the orchestrator dynamically binds the provisioned GCP project ID at the process environment level using the environment variable:
   `os.environ["CLOUDSDK_CORE_PROJECT"] = self.project_id`

---

Required parameters from the user:
1. **Golden Prompt Suite**: A local path to the test suite JSON (e.g., `.agents/scripts/tiny_golden_prompts.json`).
2. **Target Base Ref**: The git branch to compare against (default: `origin/main`).

Steering Workflow:

1. **Phase 1: Intake & Verification & Sterile State Pruning**
   - Initialize/update the unindented HTML `task.md` table inside your conversation's brain directory.
   - Run `python3 .agents/skills/gcloud-auth-verification/scripts/verify_auth.py` to verify sandbox active authentication context.
   - Prune shared local mailbox messages to clear any leftover failures from past interrupted runs:
     ```bash
     rm -f .agents/mailboxes/orchestrator/inbox/*.json
     rm -f .agents/mailboxes/chaos-tester/inbox/*.json
     ```

2. **Phase 2: Control Baseline Staging Setup (System A)**
   - Create a detached git worktree checkout under `/tmp/skynet-base` from your remote origin baseline branch:
     ```bash
     git worktree add --detach /tmp/skynet-base origin/main
     ```
   - Stage the active candidate's `.agents/` validation framework and `gcp_config.txt` locally inside `/tmp/skynet-base/` so that System A utilizes decoupled local mailboxes and the latest thread-safe orchestrator.

3. **Phase 3: Candidate Staging Setup (System B)**
   - Create a detached git worktree checkout under `/tmp/skynet-pr` from your pushed candidate remote branch commit:
     ```bash
     git worktree add --detach /tmp/skynet-pr origin/candidate-branch
     ```
   - Copy the generated candidate codelab files (which are gitignored) and the mandatory `gcp_config.txt` directly into `/tmp/skynet-pr/`.

4. **Phase 4: Twin GCP Projects Provisioning**
   - Provision two separate ephemeral GCP sandbox projects to prevent state contamination (such as pre-enabled APIs or IAM bindings overriding baseline states):
     - **Project A** (for System A Control run): `sysa-proj-[ID]`
     - **Project B** (for System B Candidate run): `sysb-proj-[ID]`
   - Ensure both validation runs dynamically override organizational policies in isolation.

5. **Phase 5: Execution Run - System A (Control Baseline)**
   - Spawn the System A validation pipeline strictly inside the `/tmp/skynet-base` directory context:
     ```bash
     python3 /tmp/skynet-base/.agents/scripts/orchestrator.py \
       /tmp/skynet-base/labs/dev/multi-region-glb-mig/multi-region-glb-mig.lab.md \
       --artifact-dir /tmp/sysa_artifacts
     ```
   - Working directory (`Cwd`) must be set to `/tmp/skynet-base`.

6. **Phase 6: Execution Run - System B (PR Candidate)**
   - Spawn the System B validation pipeline strictly inside the `/tmp/skynet-pr` directory context:
     ```bash
     python3 /tmp/skynet-pr/.agents/scripts/orchestrator.py \
       /tmp/skynet-pr/labs/dev/multi-region-glb-mig/multi-region-glb-mig.lab.md \
       --artifact-dir /tmp/sysb_artifacts
     ```
   - Working directory (`Cwd`) must be set to `/tmp/skynet-pr`.

7. **Phase 7: Evaluator Execution & Scoring (Pre-filtering)**
   - Execute the `evaluator.py` skill locally to recursively compare outputs and identify structural drift, running a pre-filtering pass that strips out non-functional metadata (such as generated timestamps, credentials, and ordering deltas):
     ```bash
     python3 .agents/skills/evaluator-engine/scripts/evaluator.py \
       --system-a-dir="/tmp/sysa_artifacts" \
       --system-b-dir="/tmp/sysb_artifacts" \
       --system-a-workspace="/tmp/skynet-base" \
       --system-b-workspace="/tmp/skynet-pr" \
       --metrics-output="doc/eval_reports/pr_report.json" \
       --fail-on-regression=true \
       --min-quality=0.95
     ```

8. **Phase 8: Local Report Compilation & Delivery (HITL Gate)**
   - Generate the detailed markdown report:
     👉 `doc/eval_reports/pr_report.md`
   - Render the results (verdict, quality score, reliability uptime, process efficiency, and trajectory score) along with a pretty-printed JSON representation of the structural differences.
   - **Human-in-the-Loop Override Gate**: If the quality gate fails due to a benign change (e.g., structural refactoring of comments or flat-mapping config tags), the developer reviews `pr_report.md` and performs an override bypass:
     ```text
     👉 /merge-pr --force --reason="Benign tag grouping refactoring"
     ```

9. **Phase 9: Ephemeral Sandbox Teardown & HITL**
   - Pause and invoke the `ask_question` tool to ask the developer if they want to retain sandbox projects for manual inspection.
   - Upon approval for teardown, run the cleanup utility and unregister both worktrees:
     ```bash
     python3 .agents/scripts/sandbox_cleanup.py --projects="sysa-proj-[ID],sysb-proj-[ID]"
     git worktree remove --force /tmp/skynet-base /tmp/skynet-pr
     ```
