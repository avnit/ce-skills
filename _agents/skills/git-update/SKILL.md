---
name: git-update
description: Interactive tool to commit, push, and merge changes with confirmation and diff viewing.
---

# Skill: Git Update

This skill provides an interactive, step-by-step process to commit local changes, push them to the remote branch, and merge changes from the `main` branch into the current branch. It asks for permission at each step and shows the files that have changed in each branch.

## Usage

```bash
python3 _agents/skills/git-update/scripts/git_update.py -m "Your commit message"
```

To stage and commit only a specific file or directory:

```bash
python3 _agents/skills/git-update/scripts/git_update.py -m "Your commit message" --path path/to/file_or_directory
```

**Steps:**

1.  **Local Changes:** Shows modified files in your current branch and asks if you want to add and commit changes in the specified path.
2.  **Push:** Asks if you want to push the committed changes to the remote repository.
3.  **Fetch and Compare:** Fetches updates from the remote and shows files that have changed in your branch vs. the `main` branch since they diverged.
4.  **Merge:** Asks if you want to merge the `main` branch into your current branch.

## Arguments

*   `-m`, `--message`: The commit message (required).
*   `--main-branch`: The name of the main branch to merge from (default: `main`).
*   `--path`: The path to stage and commit (default: `.`).
