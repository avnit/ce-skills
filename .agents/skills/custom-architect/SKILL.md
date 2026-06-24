---
name: custom-architect
description: >
  Grounded Architect-Critic cooperative design loop. Spawns the
  cloud-architect and arch-critic subagents to collaborate on GCP
  blueprints and ground HCL configs using official Developer Docs MCP.
---

# Grounded Architect-Critic Cooperative Design Loop

This skill provides instructions and system prompt templates to run an autonomous cooperative design pipeline for Google Cloud architectures, ensuring 100% Well-Architected framework compliance and documentation grounding.

## Directory Layout Standard
All configurations are fully self-contained and portable:
```
.agents/skills/custom-architect/
├── SKILL.md                             # This cheatsheet
└── references/
    ├── architect_subagent_prompt.md     # The Cloud Architect prompt template
    └── critic_subagent_prompt.md        # The Grounded Critic prompt template
```

## The Cooperating Pipeline Loop
Before presenting any design blueprint (`blueprint.md`) to the user:
1. Spawns `cloud-architect` to draft the initial configuration.
2. Spawns `arch-critic` to audit the draft against GCP security, reliability, and performance pillars.
3. The critic **must** use `google-developer-documentation-mcp` (`search_documents` or `answer_query` tools) to ground all findings.
4. All objections and citation links are exchanged asynchronously via the POSIX mailbox broker.
5. The loop terminates only when the critic issues an `APPROVED` envelope.

## Quick Bootstrapping Guide
To define and run these subagents, the parent agent parses the reference files and executes:
- `define_subagent` for both `cloud-architect` and `arch-critic`.
- `invoke_subagent` with the role and the target JSON pointer.
