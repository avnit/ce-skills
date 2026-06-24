---
name: codelab-markdown-submit
description: >-
  Guides the creation, staging, and submission of DevSite codelabs authored in
  Markdown (.lab.md) within google3. Similar to the Google Docs to Codelab 
  workflow but native to the source repository. Use when creating new 
  codelabs from scratch, migrating Google Docs to Markdown, or updating 
  existing Markdown codelabs. Covers file placement, ownership, local 
  validation with claat, and staging with devsite2.
---

# Codelab Markdown Submit

This skill provides procedures for the "Documentation-as-Code" workflow for DevSite codelabs.

## About Markdown Codelabs

Markdown codelabs use the `.lab.md` extension and are compiled into the DevSite UI. Unlike standard documentation pages, they require specific metadata and directory structures to render the step-by-step navigation.

### What this skill provides

1.  **Placement**: Where to put your files in `google3`
2.  **Standards**: Metadata and directory requirements (OWNERS, img/)
3.  **Validation**: How to check your work before submitting
4.  **Submission**: The CL lifecycle (hg/fig) and staging (devsite2)

## Create/Update Workflow

1.  **Placement**: Files must be placed in a tenant-specific directory:
    `//depot/google3/third_party/devsite/{tenant}/{lang}/codelabs/{id}/`
    - e.g., `third_party/devsite/codelabs/en/codelabs/my-tutorial/`
2.  **Metadata**: The `index.lab.md` file must start with a YAML block. See [metadata.md](references/metadata.md).
3.  **Directory Requirements**: Must include an `OWNERS` file. See [structure.md](references/structure.md).
4.  **Local Preview**: Use `claat serve` to verify rendering. See [commands.md](references/commands.md).
5.  **CL Creation**:
    - `hg citc {workspace_name}`
    - `hg add index.lab.md img/`
    - `hg upload`
6.  **Staging**: `devsite2 stage --cl {cl_number}` to view on staging servers.
7.  **CL Description**: Add the staging link to the CL description to help reviewers.

## References

- [metadata.md](references/metadata.md) - Required YAML fields
- [structure.md](references/structure.md) - Mandatory files (OWNERS, img/)
- [commands.md](references/commands.md) - Command recipes for claat and devsite2
