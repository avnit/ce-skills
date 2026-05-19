---
description: Validate environmental readiness, gcp_config.txt configuration, and MCP server accessibility.
---

Consult the **system-validation** skill to orchestrate the end-to-end validation of your environment setup.

Steering Workflow:
1. Instruct the agent to read the full operational instructions documented in the **system-validation** skill.
2. Execute the Python system verification script, passing the dynamic active JetSki conversation artifact directory to avoid polluting the user's workspace:
   ```bash
   python3 .agents/skills/system-validation/scripts/verify_system.py <appDataDir>/brain/<conversation-id>/system_validation_report.md
   ```
3. Analyze the exit code and standard output:
   - **If Exit Code is `0`**: Report a successful validation run cleanly to the user.
   - **If Exit Code is `1`**: Report the validation failures, list the precise remediation actions needed (e.g., setting credentials or enabling APIs), and provide the user with the link to the setup guide:
     * [CE-Scale JetSki Configuration](https://docs.google.com/document/d/1RLhTRPgfZnXssXog-pKbBnMExulxZyaKMWWTbtw0mF0/edit?usp=sharing&resourcekey=0-ETB7RzJbpqeYH2syDTMF4g)
4. Prompt the user to complete any failed setup requirements and re-run the validation once completed.
