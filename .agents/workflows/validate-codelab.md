---
description: Orchestrate the end-to-end automated testing and validation of a codelab from a markdown file or HTTP link using persistent subshell execution
---

This workflow automates the process of extracting commands and validating a codelab end-to-end. It handles source downloading/parsing, sandboxed project provisioning, stateful step-by-step command execution via the `tester.py` engine, report compilation, and interactive cleanup.

Required parameters from the user:
1. **Codelab Source**: A local path to a markdown file (e.g., `labs/dev/swp-basics/swp-basics.lab.md`) OR a public HTTP/HTTPS URL to a hosted codelab or markdown content.
2. **Project Strategy**: Choice of provisioning a brand-new temporary GCP sandbox project (recommended for isolation) OR specifying an existing active GCP project ID.

Steering Workflow:

1. **Phase 1: Intake & Verification**
   - Confirm that the source parameter is provided.
   - If the source is a URL, the workflow will download and extract the relevant commands automatically.
   - Initialize/update the `task.md` table inside your conversation's brain directory.

2. **Phase 2: Project Setup Choice**
   - Present an active gcloud identity and credential verification modal using the **`gcloud-auth-verification`** skill.
   - Present an option to the user via `ask_question` or a prompt:
     - Option A: Provision a brand-new isolated GCP project automatically (using the folder and billing ID set in `gcp_config.txt`).
     - Option B: Provide an existing active GCP project ID.
   - If Option B is selected, ask the user for the project ID.

3. **Phase 3: E2E Validation Execution**
   - Execute the `validator.py` skill to coordinate the test:
     ```bash
     python3 .agents/skills/codelab-validation/scripts/validator.py --src "<SOURCE>" [--project-id "<PROJECT_ID>"] --artifact-dir "<appDataDir>/brain/<conversation-id>"
     ```
   - The validator will automatically:
     - Stage the lab guide in `labs/validate/active_lab.lab.md`.
     - Provision the new project (if not provided) and disable common Org Policies using `disable_org_policies.sh`.
     - Scan the guide for dynamic variable placeholders, generating a `variables.json` template inside the validation folder to map dynamic configurations seamlessly.
     - Identify steps containing manual/GUI actions and flag them with the `🖥️ GUI / MANUAL ACTION` orange badge on the E2E validation board.
     - Launch the stateful tester subshell (`tester.py`) to execute all bash command blocks sequentially with resolved variables.
     - Maintain the visual task preview board in real-time.

4. **Phase 4: Result Compilation & Report Delivery**
   - Once the validation run completes, read the generated validation report located at `/usr/local/google/home/shacharb/skynet/labs/validate/report/validation-report.md`.
   - Copy or output the report details cleanly to the user's workspace and chat interface.
   - Highlight any failed steps or architectural recommendations from the report.

5. **Phase 5: Interactive Project Cleanup**
   - If a new project was provisioned for this test run, **prompt the user** explicitly:
     > "Would you like to keep the temporary sandbox project `<PROJECT_ID>` for further manual inspection, or should I clean it up?"
   - If the user chooses to delete/clean up:
     - Run the cleanup script:
       ```bash
       python3 .agents/skills/codelab-cleanup/scripts/cleanup_projects.py --delete <PROJECT_ID> --force
       ```
     - Report the successful removal of all provisioned cloud resources.
   - If they choose to keep it, remind them of manual deletion commands.
