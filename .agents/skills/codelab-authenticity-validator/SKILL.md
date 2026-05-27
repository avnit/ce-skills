---
name: codelab-authenticity-validator
description: >-
   deterministic verifies the authenticity and execution integrity of converted self-paced Codelabs against their hosted Qwiklabs sources. Analyzes command blocks, ensures image asset downloading, checks formatting consistency, and automatically produces a detailed Gap & Alignment Report.
---

# Skill: Codelab Authenticity Validator

This skill automates the high-fidelity verification and structural auditing of converted self-paced tutorials against their raw hosted laboratory sources. It ensures a strict **1:1 Command and Intent Alignment** (Zero Technical Deviation), validates that all external assets have been cleanly localized, and guarantees all platform references are properly hyperlinked.

---

## 🔍 Multi-Phase Auditing Framework

To verify a converted Codelab tutorial, follow these structured steps:

### Phase 1: Command Preservations & Normalization
1.  **Extract all code blocks** (enclosed inside backticks) from both the raw captured source (`raw_source.md`) and the finalized compiled self-paced file (`[lab-name].lab.md`).
2.  **Normalize whitespace, formatting, and continuation slashes (`\`)** to prevent false flags.
3.  Verify that **every terminal command, script argument, parameter string, and utility flag** from the source is fully accounted for in the generated codebase.
4.  Ensure specific target naming configurations or variable replacements maintain perfect functional equivalent alignment (e.g., replacing console manual strings like `<PROJECT_ID>` with programmatic setups like `$(gcloud config get-value project)`).

### Phase 2: Local Asset Sourcing Verification
1.  Scan the finalized compiled file to check for any remaining remote image URLs starting with `http://` or `https://` (including standard Markdown image tags and HTML `<img src="...">` parameters).
2.  Verify that all images have been downloaded and relocated into a local `img/` directory directly adjacent to the tutorial markdown file.
3.  Confirm all image references inside the Codelab point exclusively to clean, relative local file paths (`img/[filename]`).

### Phase 3: Hyperlink & Reference Enrichment Audit
1.  Scan for key external reference terms (e.g., repository libraries like `Tunix`, tools like `Kaggle` or `Hugging Face`, authorization consoles like `Wandb`).
2.  Verify that if these reference terms exist in the text, they are formatted as standard Markdown hyperlinks pointing to their respective canonical homepages rather than plain text.

---

## 🛠️ Automated Alignment Validation Run

To automate this multi-phase audit, execute the verification runner script:

```bash
python3 .agents/skills/codelab-authenticity-validator/scripts/verify_alignment.py \
  <raw_source_path> \
  <generated_path> \
  <report_output_path>
```

### Runner Script Parameters:
*   `<raw_source_path>`: Path to the raw extracted laboratory markdown file.
*   `<generated_path>`: Path to the newly generated `.lab.md` file in the repository codebase.
*   `<report_output_path>`: Destination path where the generated Gap & Alignment Report (`gap_report.md`) will be saved (typically adjacent to the lab file).

---

## 📝 Gap & Alignment Report Content Standards

Every validated conversion must include a **Gap Analysis & Command Alignment Report** (`gap_report.md`) detailing:
1.  **Technical Command Audit (1:1 Table)**: A detailed row-by-row comparison of each task's command sequence with its alignment verification status.
2.  **Inclusions & Exclusions Summary**: Clear listings of platform mechanics stripped (e.g. timer setups, start lab buttons) and target enhancements made.
3.  **Final Audit Decision**: A final clear status declaration of **APPROVED** or **ACTION REQUIRED** depending on code, image, or link verification completeness.
