# CE Agentic Automation: Architectural Review & Improvement Plan

**Author**: Google L6 System Architect
**Date**: 2026-05-19
**Status**: Finalized

## 1. Executive Summary

The current system architecture for CE Agentic Automation is highly modular and utilizes advanced persona-based steering. However, it exhibits a critical "Research-First" anti-pattern where agents consume expensive context and MCP resources before establishing a concrete plan. Furthermore, there is a significant redundancy between the `deterministic_runner` and the `codelab-validation` simulator, leading to agent ambiguity during the testing phase.

## 2. Architectural Analysis

### 2.1 Strengths
*   **Persona Separation**: Clear distinction between Architect, Writer, Reviewer, and Tester.
*   **Visual Feedback Loop**: The `task.md` mechanism provides excellent real-time visibility into agent state.
*   **Rule Enforcement**: Global rules in `.agents/rules/` are successfully injected into agent context.

### 2.2 Weaknesses & Key Failures
*   **Research-First Anti-Pattern**: Agents currently invoke MCP documentation and code search *immediately* upon request, often before clarifying the user's intent or proposing a high-level strategy. This leads to inefficient tool usage and potential hallucination propagation.
*   **Dual Testing Engines**: 
    *   `codelab-testing` (deterministic_runner.py) focuses on hash-based bash execution.
    *   `codelab-validation` (simulate_visual_updates.py) focuses on natural language step interpretation.
    *   **Result**: The agent is often confused about which tool to use, leading to incomplete validation or failure to maintain state.
*   **Dead Rules**: `system_rules.md` mandates an `implementation_plan.md` artifact, but this is not currently integrated into any active workflow or persona prompt.

## 3. Agent Ambiguity Audit

| Ambiguity Source | Description | Impact |
| :--- | :--- | :--- |
| **Testing Conflict** | `Main System Prompt` mandates `deterministic_runner`, while `Tester` persona mandates `codelab-validation`. | Agents flip-flop between engines, losing state. |
| **Planning Sequence** | No explicit instruction to "Plan before Tooling". | High token usage due to premature and wide-scoped MCP searches. |
| **Gated Human Gap** | Rules require approval for `implementation_plan.md`, but workflows skip directly to `blueprint.md`. | Reduced safety; user sees the *result* of research rather than the *strategy* for research. |

## 4. Proposed "Plan-First" Architecture

We propose a restructured orchestration lifecycle that enforces a "Gated Human" planning phase *before* any significant tool usage.

### 4.1 New Phase 0.5: Meta-Planning
1.  **Intent Capture**: Analyze user request.
2.  **Meta-Plan Generation**: Create `implementation_plan.md` (ephemeral).
3.  **Human Gate**: Invoke `ask_question` to approve the *strategy* (e.g., "I will first research X, then search for code pattern Y, then design the blueprint").
4.  **Execution**: Only proceed to MCP/Research after meta-plan approval.

### 4.2 Unified Testing Framework
Merge the strengths of both engines into a single `validation-engine` skill:
*   **Logic**: Use `codelab-validation`'s state machine for high-level step tracking and prerequisite handling.
*   **Execution**: Use `deterministic_runner`'s hash-based subshell manager for actual command evaluation.

## 5. Priority List & Risk Assessment

| Priority | Improvement | Risk | Benefit |
| :--- | :--- | :--- | :--- |
| **P0** | **Enforce Plan-First Strategy**: Update `Architect` and `Main System Prompt` to require an approved meta-plan before MCP usage. | Slight increase in initial latency (waiting for user). | Significant reduction in token waste and tool-use errors. |
| **P1** | **Unify Testing Engines**: Deprecate redundant scripts and create a unified `tester.py` that handles both state and execution. | Potential breakage of existing `.state` files. | Consistent validation behavior and simplified `Tester` persona. |
| **P2** | **Implement `implementation_plan.md` Gate**: Formally integrate the rule-mandated planning artifact into workflows. | User friction (extra approval step). | Guaranteed alignment between user expectations and agent research direction. |

## 6. Next Steps

1.  **Refactor `Architect` persona** to include Meta-Planning phase.
2.  **Update `Main System Prompt`** to align with the Unified Testing Strategy.
3.  **Consolidate `codelab-testing` and `codelab-validation`** into a single skill.
