---
name: codelab-cleanup
description: Day 2 operations to list and delete GCP projects used during codelab testing.
---

# Skill: Codelab Cleanup

This skill provides tools to list and delete Google Cloud projects created during codelab testing. This is essential for cost management and preventing resource leakage.

## Prerequisites

This skill relies on the same configuration as `gcp-provisioning`. Ensure you have a `gcp_config.txt` file in your working directory or in the skill directory of `gcp-provisioning`.

The file must contain:

```text
folder_id=YOUR_FOLDER_ID
```

## Listing Projects

To list all open projects in the configured folder:

```bash
python3 .agents/skills/codelab-cleanup/scripts/cleanup_projects.py --list
```

**What it does:**

- Reads `folder_id` from `gcp_config.txt`.
- Queries GCP for all projects in that folder.
- Displays the name, project ID, project number, creation time, and state.

## Deleting a Project

To delete a specific project:

```bash
python3 .agents/skills/codelab-cleanup/scripts/cleanup_projects.py --delete PROJECT_ID
```

**What it does:**

- Prompts for confirmation before proceeding.
- Triggers the deletion of the specified project.

To force deletion without confirmation (use with caution):

```bash
python3 .agents/skills/codelab-cleanup/scripts/cleanup_projects.py --delete PROJECT_ID --force
```

## Deleting All Projects in Folder

To clean up all projects in the configured folder (use with extreme caution):

```bash
python3 .agents/skills/codelab-cleanup/scripts/cleanup_projects.py --delete-all
```

- This will list all projects and ask for a final confirmation before deleting all of them.

---

## Automated Leak Sweeper & Cost Control

To prevent silent cloud billing leaks in continuous validation environments, we provide a dedicated automated sweeper utility:

```bash
python3 .agents/skills/codelab-cleanup/scripts/sweeper.py --age 4 --force
```

**What it does:**

- Queries all active projects under the configured `folder_id`.
- Calculates each project's active age in UTC against its `createTime` property.
- Automatically deletes projects older than the `--age` limit (default: 4 hours) when `--force` is active.
- By default, running without `--force` performs a safe **Dry-Run** print audit without making deletion API calls.

### Sidecar Background Daemon Scheduling

The sweeper is packaged with a standard `sidecar.json` configuration which can be registered inside background agent schedulers to trigger automated cleanup runs on an hourly loop dynamically.
