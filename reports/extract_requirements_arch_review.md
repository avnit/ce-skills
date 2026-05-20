# Architectural Review: `extract-requirements` Workflow Compliance

**Author**: Google L6 System Architect
**Date**: 2026-05-19
**Status**: Finalized (Compliance Audit)

## 1. Executive Summary

The `extract-requirements.md` workflow, while functionally comprehensive for solutions engineering, fails to comply with the mandated **Plan-First** architecture and the **Live Task Tracking** system rules. It skips the Phase 0.5 Meta-Planning gate and utilizes an outdated, non-standard method for progress reporting that bypasses the centralized `tasks.md` template.

## 2. Identified Failures & Ambiguities

### 2.1 Missing "Plan-First" Gate (P0)
*   **Rule Conflict**: The global system architecture (Report V1-V3) mandates a `Phase 0.5: Meta-Planning` step before any tool usage or research.
*   **Failure**: The workflow skips directly to "Scope Intake & Setup," meaning the agent begins ingestion and analyst execution without an approved `implementation_plan.md`.

### 2.2 Task Board Non-Compliance (P0)
*   **Rule Conflict**: `.agents/rules/tasks.md` requires a specific unindented HTML table template with standardized colors and zero-indentation for IDE preview compatibility.
*   **Failure**: 
    - The workflow does not reference the `tasks.md` template.
    - It instructs the agent to "Initialize the unindented HTML task.md tracker," but provides no schema or script to ensure compliance, leading to "Agent Ambiguity" where the agent may generate a different format each time.
    - It only mentions updating Step 1 and the final steps, violating the **Continuous Updates** mandate.

### 2.3 Redundant "Manual" Logic
*   **Ambiguity**: The workflow describes the task board initialization as a manual text-generation task for the agent. In contrast, the `codelab-validation` skill uses a script (`tester.py`) to automate this.
*   **Risk**: Inconsistent "Live Board" experiences across different workflows (Codelab vs. Discovery).

## 3. Priority Improvement List

| Priority | Improvement | Risk | Benefit |
| :--- | :--- | :--- | :--- |
| **P0** | **Insert Meta-Planning Gate**: Add Phase 0.5 to the workflow, requiring `implementation_plan.md` approval. | Slight intake latency. | Ensures agent strategy is aligned with user expectations before processing sensitive customer data. |
| **P0** | **Enforce `tasks.md` Template**: Explicitly reference `.agents/rules/tasks.md` and mandate the use of the standardized HTML table. | Formatting overhead for the agent. | Guaranteed visual preview compatibility in the IDE. |
| **P1** | **Standardize Task Updates**: Add explicit "Mark Step X RUNNING/DONE" instructions to every phase in the workflow. | Increased prompt length. | Real-time transparency into long-running discovery analyst tasks. |

## 4. Proposed Workflow Structure (V2)

1.  **Phase 0: Auth Verification** (Standard)
2.  **Phase 0.5: Meta-Planning** (NEW: Approval of `implementation_plan.md`)
3.  **Phase 1: Scope Intake & Task Initialization** (Use `tasks.md` template)
4.  **Phase 2-8**: (Existing logic, but with mandatory `task.md` updates after each phase).

## 5. Conclusion
The `extract-requirements` workflow is currently an "architectural island" that ignores global system rules. By synchronizing it with the Plan-First and Task-Tracking standards, we ensure a consistent and reliable experience for Solutions Engineering tasks.
