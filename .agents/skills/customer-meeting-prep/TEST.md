# Skill Test & Evaluation Plan: customer-meeting-prep

This document outlines the evaluation suite for verifying the `customer-meeting-prep` skill.

---

## Test Scenarios

### Test Case 1: End-to-End Meeting Prep with Multi-Source Validation & Classification

- **Input Prompt**: `"Prep me for my upcoming meeting with Customer X. Search recent communications from the last 14 days, validate open capacity issues, and create a One-Pager with source badges."`
- **Expected Skill Actions**:
  1. Executes `csa_cli.par` with `--allowed_corpora="GMAIL,DRIVE,CALENDAR,CHAT"`.
  2. Queries `moma` MCP or Buganizer for internal issue status validation.
  3. Queries `google-developer-knowledge` MCP for public GCP product specs or quota documentation.
  4. Tags every single Q&A and blocker with `[Public]`, `[Internal Only]`, or `[Pre-GA / NDA]`.
  5. Generates artifact adhering to `assets/one_pager_template.md`.

---

## Evaluation Checklist

- [x] **Frontmatter Validity**: `SKILL.md` contains valid YAML frontmatter with `name: customer-meeting-prep` and concise `description`.
- [x] **Structure Compliance**: Folder contains `SKILL.md`, `references/`, `assets/`, `examples/`, and `TEST.md`.
- [x] **Source Classification Standards**: Clear rules for `[Public]`, `[Internal Only]`, and `[Pre-GA / NDA]`.
- [x] **Reference Implementation**: High-fidelity example provided under `examples/`.
