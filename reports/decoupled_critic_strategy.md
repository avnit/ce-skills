# Architectural Design: Decoupled Specialized Critics in Jetski

> [!NOTE]
> **Objective**: Evaluate the architectural benefits, orchestration rules, and prompt splitting schemas of separating the review role into two distinct subagents: a technical **`security-critic`** (hard infrastructure auditing) and a structural/pedagogical **`codelab-reviewer`** (tutorial formatting and instructional quality).

---

## 1. Why Split? The Core Architectural Benefits

Combining technical cloud security auditing with soft instructional formatting into a single monolithic reviewer reduces execution accuracy. Decoupling them yields three distinct advantages:

1.  **Token Economy & Execution Agility**: In workflows where you are only developing infrastructure (VCS mode 3 / Terraform templates / pre-sales demo environments) and *not* authoring codelab tutorials, you *do not need* to check DevSite headers, congratulations steps, or conversational tone. Decoupling allows the Orchestrator to trigger **only the `security-critic`**, reducing token consumption by over 50%.
2.  **Sharp Persona Focus**: The `security-critic` is instructed as a zero-trust, highly adversarial system auditor. It evaluates strictly code, syntax, firewall ports, and IAM bindings. The `codelab-reviewer` is an educator—focused on formatting, readability, metadata structures, and clear pedagogy. Separating them prevents LLM context drift.
3.  **Dynamic Workflow Pipeline Binding**: 

```
                  [ USER PROMPT / INPUT ]
                             │
                             ▼
                    [ ORCHESTRATOR AGENT ]
                             │
            ┌────────────────┴────────────────┐
            ▼ (If Pure Infrastructure Run)    ▼ (If E2E Codelab Run)
┌────────────────────────┐        ┌────────────────────────┐
│  Run security-critic   │        │  Run security-critic   │
│  (Only Audits HCL)     │        │           AND          │
└────────────────────────┘        │  Run codelab-reviewer  │
                                  └────────────────────────┘
```

---

## 2. Decoupled Subagent Specifications

To support JIT bootstrapping in `.agents/state/compiled_subagents.json`, we define the split prompts and configurations.

### 2.1 Subagent A: `security-critic` (Hard Architecture Audit)
*   **Role Focus**: Highly pessimistic, adversarial security auditor. Zero-trust mindset.
*   **Blackboard Targets**: `workspace_state/blueprint.json`, `workspace_state/infrastructure_hcl/main.tf`.
*   **Ingested Reference Docs**: `.agents/rules/gcloud_auth.md`, `mandatory-secure-web-skills`.
*   **Auditor Checklist**:
    1.  Firewall Tags & Limits: Check for wildcards `0.0.0.0/0` or open ports.
    2.  IAM Least Privilege: Verify no wildcard `*` owner privileges or service account leaks.
    3.  PSC & Endpoints: Validate that private endpoints don't expose open backdoors.
    4.  Data Protection: Enforce CMEK / KMS key ring mappings on Cloud Storage / DBs.
*   **System Prompt**: See compiled payload map.

---

### 2.2 Subagent B: `codelab-reviewer` (Style & Pedagogy Audit)
*   **Role Focus**: Instructional designer, standard compliance reviewer. Empathetic but strict.
*   **Blackboard Targets**: `labs/dev/[lab_name]/[lab_id].lab.md`.
*   **Ingested Reference Docs**: `.agents/skills/codelab-formatting/SKILL.md`.
*   **Auditor Checklist**:
    1.  YAML Frontmatter: Ensure `id`, `summary`, `keywords`, and layout parameters are present and correctly formatted.
    2.  Durations: Confirm all step headers contain correct `Duration: MM:SS` formats.
    3.  Structure Check: Verify that Step 1 is "Introduction", Step N-1 is "Clean up" (with gcloud tear-down scripts), and the final step is "Congratulations".
    4.  Pedagogy & Tone: Verify the active, second-person friendly voice. Ensure "Why vs What" explanations are clear.
    5.  Proof of Life: Confirm all major commands have corresponding `Expected output:` code blocks or screenshot descriptions.

---

## 3. Orchestration Rules: Does This Add Complexity?

**No, the Orchestrator handles the segmentation autonomously behind the scenes.** The user experiences zero added complexity.

```python
# Orchestrator Dispatch Decision Matrix
def determine_review_pipeline(execution_scope, blackboard_state):
  pipeline = []
  
  # The security-critic is a P0 core gate for ALL code generation
  if blackboard_state.has_infrastructure_code:
    pipeline.append("security-critic")
    
  # The codelab-reviewer is triggered ONLY if we are compiling a tutorial
  if execution_scope == "E2E" or blackboard_state.has_tutorial_markdown:
    pipeline.append("codelab-reviewer")
    
  return pipeline
```

### State Coordination
1.  Both subagents write their findings to the shared blackboard directory under distinct filenames (`security_audit_findings.json` and `style_audit_findings.json`).
2.  The Orchestrator reads these files and presents a consolidated progress report to the user.
3.  The `security-critic` runs *first*. If HCL fails the security gate, execution halts immediately, preventing compilation of a broken tutorial. Only after the architecture passes the security gate is the `codelab-reviewer` triggered.

---

## 4. Feasibility & Evaluation

| Capability Metric | Monolithic Reviewer | Decoupled Critics (Split) |
| :--- | :--- | :--- |
| **Token Overhead** | Poor (always processes HCL, pedagogy, and YAML). | **Excellent** (Triggered selectively). |
| **Validation Precision** | Medium (critic persona is diluted). | **High** (Each subagent has a sharp, narrow directive). |
| **Orchestration Cost** | Very low. | Low (Managed autonomously by the parent agent). |
| **State Isolation** | Medium (combined findings in one file). | **High** (Isolate security logs from formatting logs). |

### Conclusion
Splitting the reviewers is the **best option**. It elevates the system to a production-realistic operational model, reduces token wastage in pure infrastructure plays, and sharpens the audit quality.
