# End-to-End Guide: Publishing to g3doc CompanyDoc

This guide outlines the complete architectural workflow, prerequisites, and approval requirements for publishing local engineering artifacts (Codelabs, Blueprints, One-Pagers, Diagrams) from external GitHub repositories to Google internal **g3doc CompanyDoc** (`//depot/company/...`).

---

## 1. The Hybrid Bridging Architecture

Engineering teams often write code and documentation in external GitHub repositories (like `cloud-gtm/ce-skills`) while publishing internal documentation to Piper (`//depot/company/...`) so that non-engineering Googlers (FTEs and TVCs) can view them without Piper access.

Rather than manually copying files between directories, the `publish-artifact` skill acts as an automated filesystem bridge:

```
[GitHub Local Repo] --(publish.sh bridge)--> [Piper CitC Workspace] --(Critique CL)--> [Live g3doc Site]
```

---

## 2. Prerequisites: What You Need Before Publishing

Before running the publishing command, ensure your Cloudtop environment meets the following requirements:

1. **Active Piper Workspace**: You must have at least one active CitC (`g4`) or Fig (`hg`) client located under `${CITC_WORKSPACE_ROOT:-/google/src/cloud/$USER/<your-client>/google3}` that includes the `company` view.
   > **Why is a Piper Workspace Required?**  
   > While _viewing_ CompanyDocs (`g3doc.corp.google.com/company/...`) requires no special permissions or Piper access, _authoring and publishing_ new documentation requires an active Piper client because all CompanyDoc source markdown files live inside Google's central Piper repository under `//depot/company/...`.
   - _Check_: The `publish.sh` script automatically reads `piper_workspace` from `gcp_config.txt` (or accepts `-w <workspace_name>`).
   - _Create if missing_: If the specified workspace does not exist, `publish.sh` automatically executes `g4 client -c <workspace_name>` to force create it for you!
2. **Target Artifact**: A valid markdown file (`*.md`) or directory located inside your local GitHub working directory.

---

## 3. The Step-by-Step Publishing Workflow

### Step 1: Trigger the Script

From within your GitHub repository folder, invoke `publish.sh` specifying the file, category, subject, and scope:

```bash
# Example: Publishing a Codelab to the ce-skills team portal
bash .agents/skills/publish-artifact/scripts/publish.sh \
  -f "codelabs/spanner_rag.md" \
  -c "codelabs" \
  -s "spanner_rag" \
  -p "team" \
  -t "ce-skills"
```

### Step 2: Automated Processing

The script automatically executes the following backend operations:

- Locates your active Piper workspace.
- Copies the artifact into `//depot/company/teams/ce-skills/codelabs/spanner_rag/spanner_rag.md`.
- Inspects the file header and prepends mandatory g3doc metadata if missing:

  ```markdown
  # Spanner RAG Codelab

  <!--* freshness: { owner: 'ce-skills' reviewed: '2026-06-26' } *-->

  [TOC]
  ```

- Registers the file in Piper version control (`g4 add` or `hg add`).
- Generates an instant shareable **Critique Live Preview URL**.

---

## 4. Going Live: Approval & Submission Requirements

What you need to do before your document is publicly viewable depends on the scope you selected:

### Option A: Personal Scope (`--scope personal`)

- **Target Path**: `//depot/company/users/<username>/...`
- **Approval Requirement**: **None (Exempt)**. Personal markdown files do not require peer review.
- **Go-Live Process**: Open the Critique CL link provided by the script, verify the live preview rendering, and click **Submit directly**.

### Option B: Team Scope (`--scope team --team <team_name>`)

- **Target Path**: `//depot/company/teams/<team_name>/...`
- **Approval Requirement**: **Critique LGTM Approval**. Team spaces enforce two-party code review governance.
- **Go-Live Process**:
  1. Open your Piper directory (`cd ${CITC_WORKSPACE_ROOT:-/google/src/cloud/$USER/<your-client>/google3}/company/teams/<team_name>/`).
  2. Mail the changelist for review: `g4 mail` (or `hg mail`).
  3. Add a peer teammate or team owner (listed in `OWNERS`) as a reviewer.
  4. Once your reviewer grants an **LGTM**, click **Submit** in Critique.

### ⚡ Live Deployment

As soon as the Critique CL is fully submitted, Google's internal content delivery network synchronizes automatically. Your documentation is live across Google within minutes at:
👉 `https://g3doc.corp.google.com/company/teams/<team_name>/<category>/<subject>/<filename>.md`
