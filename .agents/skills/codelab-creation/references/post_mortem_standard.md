# Post-Mortem Retrospective & Continuous Improvement Standard

This standard defines the mandatory feedback loop that the **Central Commander** must execute at the end of every workflow run. The goal is to evaluate process adherence, audit the root causes of validation defects, and systematically upgrade upstream research and blueprint skills to prevent bugs from ever reaching the sandboxed deployment phase.

We do NOT document trivial Google Cloud CLI commands or generic service features. Instead, we focus on **improving the codelab creation process** itself.

---

## 1. The Retrospective Lifecycle

At the conclusion of the Quality Review phase (Phase 5/6) and before final delivery to the user, the Commander must:

1.  Reflect on the entire run's execution timeline.
2.  Draft a structured **`post_mortem.md`** file in the active session brain folder.
3.  Formulate and propose direct, actionable upgrades to upstream repository skills, common gotchas (`gotchas.md`), or specialist prompts.
4.  **Mandatory Human Approval Gate**: Present the proposed skill/prompt upgrades to the user. **Under no circumstances** should any repository skill, prompt, or gotcha file be modified or updated without the user's explicit manual review and sign-off (e.g., via interactive chat or modal).

---

## 2. Structured Post-Mortem Schema (`post_mortem.md`)

The post-mortem report must contain the following four distinct analysis pillars:

```markdown
# Post-Mortem Retrospective: [Codelab/Workflow Name]

## 1. Process Adherence Evaluation

- **Mandatory Strategy Plan Gate**: Did the Commander draft and obtain manual sign-off on the `implementation_plan.md` before research or coding? (Yes/No + Comments)
- **Intake Scoping Gate**: Were interactive questions used to dynamically configure complexity, format, and cleanup? (Yes/No)
- **Preview-First Blueprinting**: Was `blueprint.md` created in the brain folder and audited by the `arch-critic` _before_ writing to the codebase? (Yes/No)
- **Validation Reproducibility**: Was `tester.py` run statefully inside a persistent terminal session? (Yes/No)

## 2. Defect Deflector Audit (What failed in Validation?)

List all failures, syntax errors, or execution hangs encountered during Phase 4 (Validation).

- **Defect 1**: [e.g., VM boot timeout during SSH]
  - _Root Cause_: VM startup script attempted apt-get downloads in a private VPC subnet with no internet egress path.
- **Defect 2**: [e.g., MIG Template URI resolution failure]
  - _Root Cause_: Regional template was referenced using global URI format, causing GCE API to reject the creation call.

## 3. Upfront Prevention Mechanics (The "Why")

For each defect audited above, analyze why the pipeline let this error slip through to Phase 4. How could this have been prevented _earlier_ (in Phase 1 Research or Phase 2 Blueprint Design)?

- _Prevention 1_: During Phase 1 Research, the Commander should have checked if the backend subnet had PGA or NAT. In Phase 2, the Blueprint should have been gated by a strict check: _"All startup scripts in private subnets must be completely self-contained."_
- _Prevention 2_: During the Phase 2 `arch-critic` audit, the specialist should have parsed the template URI and cross-referenced the regional GCE specifications in the developer documentation MCP.

## 4. System Skill Upgrades (Actions Taken)

List the exact, permanent updates made to the repository's core skills or prompts during this retrospective to automate the prevention of these issues in future runs.

- _Action 1_: Added a strict rule to the "Common Gotchas" checklist in `.agents/skills/codelab-creation/references/gotchas.md`.
- _Action 2_: Upgraded the `arch-critic` specialist prompt to inspect MIG template URLs for regional context matching.
```

---

## 3. Upstream Prevention Mechanics (Focus on Process, not Commands)

To keep the knowledge base clean, lightweight, and focused:

- **Banned**: Do not log command-specific syntax fixes (e.g., "Forgot --quiet on line 12" or "Added --zone flag"). These are trivial bugs easily captured by standard lints or official docs.
- **Required**: Focus on **systemic prevention guidelines** that steer the Commander's planning phase.
  - _Example_: Instead of documenting a fix for a specific GKE storage size command, upgrade the research phase to force querying the Developer Docs MCP whenever a GKE persistent volume storage class is designed, ensuring dynamic allocations align with minimum GKE version requirements upfront.
