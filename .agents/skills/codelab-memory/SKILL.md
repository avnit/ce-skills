---
name: codelab-memory
description: Interface to the centralized RAG system for retrieving and storing lessons learned.
---

# Skill: Codelab Memory

This skill provides an interface to the centralized RAG system used to store and retrieve lessons learned, gotchas, and best practices.

## Retrieving Learnings

Use the provided script to search for relevant learnings via MCP `query_team_knowledge` before starting a design or when debugging a failure:

```bash
python3 .agents/skills/codelab-memory/scripts/query_rag.py --query "your search topic"
```

**When to use:**

- **Phase 1 (Research)**: Search for gotchas related to the topic.
- **Phase 4 (Validation)**: If a test fails, search for the error message to see if there is a known solution.

## Storing Learnings

Direct uploads to the corpus are retired. To store new lessons learned, gotchas, or remediation rules, use the **closed-loop-learning** skill to submit structured records via `submit_lesson` for review and curation:

- Refer to the **closed-loop-learning** skill for bug file extraction and lesson submission workflows.

**When to use:**

- After successfully fixing a non-obvious error during validation.
- After receiving critical feedback from the user that represents a general rule.
