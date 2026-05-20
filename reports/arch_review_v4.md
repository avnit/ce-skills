# CE Agentic Automation: Architectural Review V4 - Operational Gaps & Lifecycle Management

**Author**: Google L6 System Architect
**Date**: 2026-05-19
**Status**: For Team Review

## 1. Executive Summary

While the system has achieved 100% architectural alignment (Phase 0.5 planning and unified testing), we have identified a critical **Operational Race Condition** during the cleanup phase. This report details the "Gated Cleanup" failure—where resources are deleted before the user can choose to retain them—and explains the evolution of the Visual Status Board.

## 2. Critical Failure: The Cleanup Race Condition (P0)

### 2.1 The Issue
The agent currently deletes the sandboxed GCP environment before asking the user if they want to keep it. This bypasses the "Clean-up Choice Gate" intended for cost management and user experimentation.

### 2.2 Root Cause Analysis
*   **The "Faithful Simulator" Problem**: The unified `tester.py` script is designed to complete 100% of the steps in the Codelab. 
*   **Logical Race Condition**: Our `reviewer.md` and `writer.md` protocols mandate that every Codelab must have a `## Clean up` section at the end. Because the tester sees this section in the markdown, it executes the cleanup commands as part of the "successful validation."
*   **Orchestration Gap**: The "Keep or Delete" choice gate in the orchestrator occurs *after* the `tester.py` has finished, but by then, the "faithful simulator" has already destroyed the resources.

### 2.3 Proposed Remediation
*   **Modify `tester.py`**: Add a detection flag to skip any section titled "Clean up" or "Cleanup" by default during validation runs.
*   **Post-Validation Trigger**: The final cleanup commands should only be executed as a "Phase 6" action *after* the user explicitly selects "Delete" in the choice gate.

## 3. Visual Board Evolution (UX Analysis)

### 3.1 Structural Shift
The transition from `deterministic_runner.py` to `tester.py` changed the `task.md` layout:
*   **Old Board**: Focused on raw **Command Blocks**.
*   **New Board**: Focused on **Execution Steps** (Tutorial Chapters).

### 3.2 Rationale
*   **Tutorial Mirroring**: The new board reflects the H2 headers of the Codelab, ensuring the user can map the "DONE" status directly to the page they are reading.
*   **Details & Outputs**: The new column pulls narrative text from the Codelab body, providing business context (e.g., "In high-scale architectures...") rather than just raw CLI flags.

## 4. Specific Action Items for Team

1.  **Tester Script Update**: Update `.agents/skills/codelab-validation/scripts/tester.py` to implement `is_cleanup_step` detection logic.
2.  **Persona Sync**: Update `prompts/tester.md` to explicitly state: *"Verify all steps except the final Cleanup; wait for Orchestrator signal before running destructive commands."*
3.  **Workflow Finalization**: Update `create-codelab.md` to ensure the "Choice Gate" is the final blocker before the lab is marked `COMPLETED`.

## 5. Risk Assessment

*   **Risk**: Resources might leak if a run is abandoned before the cleanup gate.
*   **Mitigation**: The `codelab-cleanup` skill remains the fallback for "Day 2" cost containment.
