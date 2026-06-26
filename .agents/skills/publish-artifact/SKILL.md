---
name: publish-artifact
description: Publishes generated artifacts (codelabs, one-pagers, blueprints, diagrams, etc.) to internal g3doc CompanyDoc (//depot/company/...) supporting team-wide and personal publishing options with instant live preview links.
---

# Publish Artifact Skill (g3doc CompanyDoc)

This skill automates publishing local workspace artifacts to internal **g3doc CompanyDoc** (`//depot/company/...`) in Piper / Google3.

The CompanyDoc repository is structured into two distinct publishing scopes to keep engineering artifacts discoverable and well-governed:

1. **Team-wide Publishing**: `//depot/company/teams/<team_name>/<category>/<subject>/`
2. **Personal Publishing**: `//depot/company/users/<username>/<category>/<subject>/`

## When to use this skill

Use this skill when the user explicitly asks to publish, upload, or sync an artifact they've created (e.g., a design document, blueprint, one-pager, or codelab) to CompanyDocs / g3doc.

## Usage Instructions

To publish an artifact, execute the publishing script using the `run_command` tool:

```bash
bash .agents/skills/publish-artifact/scripts/publish.sh -f "<path_to_local_artifact>" -c "<category>" -s "<subject>" -p "<personal|team>" [-t "<team_name>"]
```

### Script Arguments:

- `-f|--file <file_path>`: (Required) The absolute or relative path to the local artifact file or directory.
- `-c|--category <category>`: (Required) The category classification. Examples: `blueprints`, `codelabs`, `diagrams`, `whitepapers`, `customers`.
- `-s|--subject <subject>`: (Required) The specific topic identifier (e.g., `closed_loop_learning` or `customer_x`).
- `-p|--scope <personal|team>`: (Optional, defaults to `personal`) Whether to publish under `company/users/$USER` or `company/teams/$TEAM`.
- `-t|--team <team_name>`: (Required if scope is `team`) The target team directory name under `company/teams/` (e.g., `practice-ce`, `cloud-gtm`, or `ce-skills`).

### Examples

**Example 1: Personal Publishing**
Publishing `doc/system_design.md` to user's personal CompanyDoc space:

```bash
bash .agents/skills/publish-artifact/scripts/publish.sh -f "doc/system_design.md" -c "blueprints" -s "closed_loop_learning" -p "personal"
```

_Staged Path_: `//depot/company/users/<ldap>/blueprints/closed_loop_learning/system_design.md`

**Example 2: Team-wide Publishing**
Publishing `demo/one-pager.md` to the `practice-ce` team space:

```bash
bash .agents/skills/publish-artifact/scripts/publish.sh -f "demo/one-pager.md" -c "whitepapers" -s "customer_x" -p "team" -t "practice-ce"
```

_Staged Path_: `//depot/company/teams/practice-ce/whitepapers/customer_x/one-pager.md`

## How it works internally

The script will:

1. Locate an available CitC workspace containing a `/company` mount (e.g., `/google/src/cloud/$USER/ce-skills/company`).
2. Resolve target destination directory based on `--scope` (`users/$USER` vs `teams/$TEAM`).
3. Copy the artifact files into the target CitC directory.
4. **G3doc Formatting**: For markdown files (`*.md`), inspect headers and automatically inject standard g3doc metadata blocks (`<!--* freshness: ... *-->` and `[TOC]`) if missing.
5. Execute `g4 open` / `g4 add` to register files in Piper version control.
6. Create a pending changelist (CL) and generate the direct shareable **g3doc Live Preview URL**:
   `https://g3doc.corp.google.com/company/.../filename.md?cl=<cl_number>`
