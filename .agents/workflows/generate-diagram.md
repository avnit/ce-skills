---
description: Orchestrate the automated generation of high-fidelity Google Cloud architecture diagrams natively from Codelabs, Terraform files, or Design blueprints.
---

# Workflow: Generate GCP Architecture Diagram Natively

This workflow guides you through generating a premium, Google Cloud-styled architecture diagram or visual asset natively on your workstation. You can point to an existing technical document in the workspace (such as a Codelab, Terraform HCL file, or Design Blueprint) for direct ingestion, or supply a custom architectural prompt.

## Operational Workflow

### Phase 0: Pre-Flight Authentication & ADC Verification

1. Consult and enforce the global auth validation standard: [gcloud_auth.md](../rules/gcloud_auth.md).
2. Execute the **gcloud-auth-verification** skill (`python3 .agents/skills/gcloud-auth-verification/scripts/verify_auth.py`).
3. If active account matches target environment, log active identity and proceed automatically.
4. If an account switch or user decision is required, invoke the `ask_question` tool modal to let the user select or confirm the active account.

### Phase 1: Source Material Selection & Ingestion


1.  Invoke the `ask_question` tool to ask the user for their intake preference:
    - **Option A (Workspace File)**: Supply the path to an existing technical file (e.g., `meeting/customer_a/design_blueprint.md` or a Terraform `.tf` file).
    - **Option B (Custom Text)**: Enter a custom architectural description directly into the prompt box.
2.  If the user selects **Option A**:
    - Read and analyze the contents of the specified file in the workspace.
    - Extract the key structural components (VPCs, Subnetworks, GKE Clusters, Load Balancers, Databases, etc.) and their connections.
    - Map out the topology layers (Internet egress, Ingestion/VPC boundaries, Regional placement).
3.  If the user selects **Option B**:
    - Capture their custom text layout description.

### Phase 2: Target Resource Intake

1.  **Image File Name**: Invoke the `ask_question` tool to prompt the user for the target **Image File Name** in standard `snake_case` (e.g., `gke_shared_storage`).
2.  **Destination Folder**: Invoke the `ask_question` tool to prompt the user for the target **Destination Folder** in the workspace (e.g., `meeting/customer_a/assets/` or `labs/dev/gke-filestore/img/`).

### Phase 3: Image Prompt Formulation

1.  Construct the detailed Imagen 3 prompt by wrapping the extracted topology inside the official Google Cloud Architecture Style specifications:
    - **Solid white background** (`#FFFFFF`).
    - **2D flat-vector clean outlines** (Project/VPC boundaries outlines in `#1A73E8` Blue).
    - **GCP Cards**: Border weight 2pt, rounded corner radius 6px, border color `#202124` Gray 900.
    - **Typography**: Legends and labels in legible Google Sans Bold; IP ranges and port names in Roboto Mono.
    - **Connectors**: Solid black horizontal arrows showing unidirectional traffic flow.

### Phase 4: Trigger Generation & Move Asset

1.  Execute the native `generate_image` tool using your formulated prompt and designated `ImageName`:
    ```json
    {
      "ImageName": "<input_image_name>",
      "Prompt": "<formulated_imagen3_prompt>"
    }
    ```
2.  Proactively copy the generated image from your App Data artifacts directory (`{app_data_dir}/artifacts/<image_name>.png`) into your specified destination folder in the workspace.
3.  Output the final Markdown absolute local URI link so the user can paste it directly into their documents:
    ```markdown
    ![GCP Architecture Diagram](file:///{workspace_dir}/<destination_folder>/<image_name>.png)
    ```
