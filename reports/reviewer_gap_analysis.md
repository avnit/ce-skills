# Gap Analysis: Proposed Security Critic vs. Active Codelab Reviewer

> [!IMPORTANT]
> **Abstract**: This gap analysis evaluates the functional discrepancies between our initial proposed `security-critic` subagent and the actual system requirements defined in `/prompts/reviewer.md` (Codelab Reviewer). We identify critical pedagogical, structural, and stylistic omissions and detail a concrete remediation roadmap to restore the reviewer's full operational scope.

---

## 1. Direct Comparison Matrix

| Feature Domain | Original Proposed `security-critic` | Active `/prompts/reviewer.md` | Gap Status | Severity |
| :--- | :--- | :--- | :---: | :---: |
| **1. Cloud Security & Least Privilege** | Strict audit of IAM, firewalls, PSC endpoints, KMS encryption, and secure-web-skills. | Strict audit of VPC isolation, IAM least privilege, and private endpoint connections. | **Aligned** | Minimal |
| **2. Enterprise Production Standards** | Unspecified (implied via general security best practices). | In-depth review of high availability (HA), Managed Instance Group (MIG) scaling, session persistence, and negative testing. | **MISSING** | **High** |
| **3. DevSite Formatting Compliance** | Unspecified. | Strict validation of metadata frontmatter (YAML parameters like `id`, `summary`, `keywords`), callout block formats (`> aside positive`), and correct line styling. | **MISSING** | **Critical** |
| **4. Tutorial Structure Validation** | Unspecified. | Verifies specific step sequences: First step is Introduction; Penultimate step is Clean Up (Step N-1); Final step is Congratulations. | **MISSING** | **Critical** |
| **5. Instructional Pedagogy** | Unspecified. | Validates learning objectives, "Why" vs "What" conceptual explanations, active tone, and conversational second-person voice. | **MISSING** | **High** |
| **6. Output Visualization Check** | Unspecified. | Enforces that all critical actions show the expected terminal output or console screenshot descriptions (Proof of Life). | **MISSING** | **High** |

---

## 2. Detailed Gaps Identified

### Gap A: Codelab Structural Standards & Metadata
*   **The Discrepancy**: Our proposed `security-critic` focused entirely on analyzing Terraform HCL. However, the actual Codelab Reviewer is responsible for checking the final `.lab.md` markdown file against strict DevSite compilation rules:
    - YAML Frontmatter: Validating that `id`, `summary`, and `keywords` are correct.
    - Durations: Ensuring *every step* has a valid `Duration:` in `MM:SS` format.
    - Gated Steps: Verifying that the penultimate step contains the `Clean up` scripting block and the final step is `Congratulations`.

### Gap B: Instructional Design & Pedagogy
*   **The Discrepancy**: The proposed critic would approve a technically perfect HCL design even if the tutorial did not explain *why* a command was being executed. The actual reviewer prompt enforces **pedagogical quality**:
    - Conceptual Clarity: Ensuring the writer explains the underlying mechanics of the feature, not just a blind list of commands.
    - Voice and Tone: Confirming that the writing style remains friendly, conversational, and second-person ("you will create...").

### Gap C: Expected Output Checks ("Proof of Life")
*   **The Discrepancy**: Codelabs must show visual verification cues. The actual reviewer prompt mandates checking that the tutorial includes expected terminal outputs or screenshot descriptions after significant steps to guide the student.

---

## 3. Remediation Roadmap: Refactoring to `codelab-reviewer`

To address these gaps, we will perform the following updates:

### Action 1: Refactor Subagent Definition
We will rename the subagent from `security-critic` to **`codelab-reviewer`** to reflect its full, double-expert scope (GCP Architecture + Technical Training & Pedagogy).

### Action 2: System Prompt Restoration
We will update the prompt payload for this subagent to **restore 100% of the original `/prompts/reviewer.md` evaluation criteria** (Technical, Style, and Pedagogy), while keeping the zero-trust security controls (`mandatory-secure-web-skills`) as a core pillar of Section 1.

### Action 3: Tool Access Adjustment
The refactored `codelab-reviewer` subagent requires the **Developer Documentation MCP tool** (`search_documents`) to verify active `gcloud` syntax flags against official Google documentation. We will ensure this MCP access is enabled.
