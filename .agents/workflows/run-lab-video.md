---
description: Automate the execution of a codelab inside Chrome for video recording
---

Consult the **lab-video-automation** skill to drive the step-by-step interactive execution of a target codelab.

Required parameters from the user:
1. Project ID (e.g., `multi-vpc-dns-1778621330`)
2. Lab Markdown Path (e.g., `labs/dev/multi-vpc-dns-forwarding/multi-vpc-dns-forwarding.lab.md`)

Steering Workflow:
1. Instruct the agent to read the operational runbook and execution flags documented in the **lab-video-automation** skill manifest.
2. Execute the automation engine passing the required project ID and lab path parameters exactly as specified by the skill's runbook guidelines.
3. Guide the user to monitor live recording progress via the dynamic status dashboard managed inside the run folder.
