# Workflow: Open Buganizer Issue for ce-skills (/open-bug)

This workflow guides you through filing a tracked issue or feature request in Buganizer under **ce-skills Component ID `2150801`**.

## Operational Workflow

### Phase 1: Interactive Scoping & Intake

1. Use the `ask_question` tool to gather the required parameters for the ticket:
   - **Issue Type**: Ask the user to choose between:
     - `BUG` (Software defect or failure)
     - `FEATURE_REQUEST` (New enhancement or capability)
     - `PROCESS` (Onboarding, access request, or team process)
     - `CLEANUP` (Refactoring, tech debt, or asset cleanup)
   - **Priority**: Ask for the ticket priority level:
     - `P1` (Critical / Blocking)
     - `P2` (Default / Standard feature or fix)
     - `P3` (Minor / Low urgency)
   - **Title**: Request a concise title summarizing the request.
   - **Assignee**: Ask if they want to assign it to themselves (`$USER`), leave it unassigned, or specify a peer LDAP.

### Phase 2: Execute Scripted Filing

1. Once details are confirmed, execute the deterministic helper script via `run_command`:
   ```bash
   python3 .agents/skills/open-bug/scripts/open_bug.py --title "<title>" --description "<detailed_description>" --priority "<P1|P2|P3>" --type "<type>" [--assignee "<ldap>"]
   ```

### Phase 3: Present Filing Confirmation

1. Display the execution results prominently to the user.
2. If created via CLI, highlight the direct Buganizer link (`http://b/<issue_id>`).
3. Always display the **One-Click Pre-filled Web UI Filing Link** so the user can review or manually submit in their browser if desired!
