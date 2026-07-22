---
name: open-bug
description: Automates opening Buganizer tracking tickets and issues for ce-skills under Component ID 2150801 using scripted CLI execution with an instant pre-filled Web UI fallback.
---

# Open Bug Skill (ce-skills)

This skill automates filing Buganizer issues and task trackers targeting official **ce-skills Component ID `2150801`**.

## When to use this skill

Use this skill whenever the user asks to open a bug, file an issue, track a feature request, or record a task for `ce-skills`.

## Usage Instructions

Execute the deterministic helper script via the `run_command` tool:

```bash
python3 .agents/skills/open-bug/scripts/open_bug.py --title "<issue_title>" --description "<detailed_description>" --priority "<P0|P1|P2|P3|P4>" --type "<BUG|FEATURE_REQUEST|PROCESS|CLEANUP>" [--assignee "<ldap>"]
```

### Script Arguments:

- `--title`: (Required) A concise summary title for the issue.
- `--description`: (Required) Detailed markdown explanation of the bug or task request.
- `--priority`: (Optional, defaults to `P2`) Priority level (`P0` to `P4`).
- `--type`: (Optional, defaults to `BUG`) Issue category (`BUG`, `FEATURE_REQUEST`, `PROCESS`, `CLEANUP`).
- `--assignee`: (Optional) LDAP username of the person to assign the ticket to (without `@google.com`).
- `--component-id`: (Optional, defaults to `2150801`) Target Buganizer component ID.

### How it works internally:

1. **URL Fallback Generation**: Constructs a URL-encoded one-click filing link (`https://b.corp.google.com/issues/new?component=2150801&...`).
2. **CLI Execution**: Invokes `${ISSUES:-/google/bin/releases/issues-cli/issues} create` to create the ticket directly in Buganizer.
3. **Resiliency**: If CLI mutation is restricted by LOAS or credentials policy, the script catches the failure cleanly and instructs the user to click the pre-filled web UI link.
