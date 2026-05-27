---
description: Orchestrate the end-to-end automated conversion of hosted Qwiklabs tutorials into standalone, self-run Google Cloud Codelabs
---

Consult the **qwiklabs-to-codelab** skill to steer the multi-phase content extraction, boilerplate filtering, and document compilation sequence ensuring 100% technical execution consistency.

Required parameters from the user:
1. Target Input Source: Google Doc link, plain text submission/file path, or a target hosted laboratory web URL for live capture (e.g., `https://partner.cloudskillsboost.google/focuses/...`).

Overall Orchestration Lifecycle:
1. **Phase 0: Interactive Parameter Elicitation Gate**
   - **Interactive Parameter Inquiry**: Before initiating the capture or parser, the orchestrator MUST invoke the **`ask_question`** tool to present a parameter configuration modal to the user:
     *   **Authors**: Prompt the user to specify the author list (propose `Practice CE` as the recommended choice).
     *   **Codelab ID & Suggested Folder Name**: Proactively suggest a clean, lowercase hyphenated directory name and identifier based on the source lab title, and allow the user to modify or accept it.
     *   **Suggested Keywords**: Proactively suggest a set of technical keywords based on the lab technology, and allow the user to modify or accept them.
2. **Phase 1: Source Intake & Ingestion Sequence**
   - Consult the **qwiklabs-to-codelab** skill instructions alongside core repository formatting standards.
   - **Live Browser Extraction**: If the user provides a specific hosted web URL, immediately invoke the **`browser_subagent`** tool to retrieve target content using these explicit parameters:
     - `TaskName`: 'Capturing Hosted Lab Tutorial Content'
     - `TaskSummary`: 'Open target hosted lab URL, wait for manual user authentication if prompted, and extract the full tutorial markdown/text content.'
     - `RecordingName`: 'hosted_lab_capture'
     - `Task`: 'Navigate to the provided URL using open_browser_url. If an authentication or sign-in gateway is displayed, pause actions and wait for the user to complete authentication manually. Once the tutorial content page is fully visible, extract the complete tutorial steps, headers, text descriptions, and terminal command code blocks. Return the extracted tutorial content in your final report formatted cleanly as structured markdown.'
   - Initialize the mandatory unindented HTML task tracking table (`task.md`) mapping out active extraction and conversion steps.
3. **Phase 2: Content Filtering & Technical Extraction**
   - Update active step status in `task.md` to `RUNNING`.
   - Scan the raw extracted source blocks applying strict separation logic to strip out hosted platform mechanics (e.g., "Click Start Lab", temporary student user profiles, mandatory Incognito alerts, pre-provisioned project strings).
   - **CRITICAL RULE - ZERO TECHNICAL DEVIATION**: Preserve every terminal command, script flag, localized variable identifier, and code file snippet exactly as presented in the original lab. Do not attempt to modify, optimize, or reinvent underlying execution sequences.
4. **Phase 3: Codelab Assembly & Codebase Persistence**
   - Inject the standard self-paced Google Cloud introductory sections and mandatory self-paced setup boilerplate (Section 2) mandated by the **qwiklabs-to-codelab** skill.
   - Map hardcoded hosted environment variables cleanly to standard programmatic environment discovery calls (e.g., `export PROJECT_ID=$(gcloud config get-value project)`).
   - Format the output block into an **amazing codelab** file (.lab.md) strictly implementing core **codelab-formatting** frontmatter metadata standards (zero inner blank lines, standard keys) and explicit `Duration: MM:SS` sub-heading annotations.
   - **Link Enforcement**: Identify external reference terms (e.g. library repositories, API references, helper tools like Tunix or Hugging Face keys) and actively format them as working Markdown links.
   - Save the finalized tutorial file natively to the targeting local repository directory (`labs/dev/[lab-name]/[lab-name].lab.md`).
   - **Image Asset Isolation & Local Mapping**: Run the local Python image downloader (`python3 .agents/skills/qwiklabs-to-codelab/scripts/download_images.py labs/dev/[lab-name]/[lab-name].lab.md`) to pull all remote image URLs down into a dedicated local `/img` directory alongside the codelab, and automatically rewrite asset reference tags.
   - Render clickable output links directly inside the view buffer and mark final overall execution state as `COMPLETED` in `task.md`.
