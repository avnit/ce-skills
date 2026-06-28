---
name: creating-gcp-diagrams
description: >-
  Guides the generation of high-fidelity Google Cloud architecture diagrams (PNG) utilizing the pre-packaged official GCP Category Icons library for style anchoring and hallucination-free rendering.
---

# Skill: GCP Architecture Diagramming & Asset Generation

This skill guides you to create professional architectural diagrams, network topologies, and request flows using the `generate_image` tool. 

To eliminate hallucinations and enforce absolute brand-consistency in generated images, this skill leverages a **pre-packaged official Google Cloud Category Icons library** for local style and layout anchoring.

---

## 🎛️ Skill Configuration & Inputs

When invoking this skill, the calling context or steering instructions must specify:

1.  **`ImageName`** (Required): Unique snake_case filename (e.g., `peered_vpc_mesh`).
2.  **`DestinationFolder`** (Required): Target workspace folder (e.g., `meeting/customer_a/assets/` or `labs/dev/gke-filestore/img/`).

---

## 📋 Step-by-Step Operations Workflow

### Phase 1: Ingest & Model Topology

1. Analyze the target technical file path or architectural description (e.g., a blueprint markdown, lab steps, or Terraform HCL configurations).
2. Identify all core structural layers:
   - **Security/Ingress Perimeters** (Internet, Cloud NAT, Load Balancers, Cloud Armor, IAP).
   - **Network Boundaries** (Shared VPCs, Peerings, Hub-and-Spoke, Subnets, IP ranges).
   - **Compute & Data Assets** (Compute VMs, GKE Clusters, MIGs, Cloud SQL, AlloyDB).
   - **Directional Data Flows** (Ports, unidirectional protocols, API ingress/egress).

---

### Phase 2: Generate High-Definition Visual Asset

#### 1. Select Reference Brand Anchors from the Local Library

To ensure perfect brand-accurate rendering, select up to 3 matching category icons from the pre-packaged local library:

- **Path**: `/usr/local/google/home/shacharb/skynet/.agents/skills/creating_gcp_diagrams/assets/category-icons/Category Icons/`

| Architectural Component     | Target Local Reference Asset Path                                   |
| :-------------------------- | :------------------------------------------------------------------ |
| **VMs, Compute, MIGs**      | `Compute/PNG/Compute-512-color.png`                                 |
| **VPCs, Routers, VPNs**     | `Networking/PNG/Networking-512-color.png`                           |
| **Cloud SQL, Databases**    | `Databases/PNG/Databases-512-color.png`                             |
| **IAP, Cloud Armor, IAM**   | `Security Identity/PNG/SecurityIdentity-512-color.png`              |
| **GKE, Clusters, Pods**     | `Containers/PNG/Containers-512-color.png`                           |
| **Buckets, Filestore**      | `Storage/PNG/Storage-512-color.png`                                 |
| **Cloud Functions, Run**    | `Serverless Computing/PNG/ServerlessComputing-512-color.png`        |
| **Agents, AI Orchestrator** | `Agents/PNG/Agents-512-color.png` (or custom user logo if provided) |

#### 2. Execute Image Generation Directly

Call the `generate_image` tool directly in the active context to render the diagram. Pass the selected local category icon paths inside the `ImagePaths` parameter (max 3 images) for direct style injection.

##### Execution Example:

```json
{
  "Prompt": "Generate a professional flat 2D vector Google Cloud architecture diagram. Replicate the exact visual style, clean geometry, and color palette of the attached 'SecurityIdentity-512-color.png' and 'Networking-512-color.png' reference files. Draw a secure mesh peering between 'vpc-frontend' (Networking style) protected by 'cloud-armor' (Security Identity style). Layout: Left to right. Top: VPC A. Bottom: VPC B.",
  "ImageName": "secure_peering",
  "AspectRatio": "16:9",
  "ImagePaths": [
    "/usr/local/google/home/shacharb/skynet/.agents/skills/creating_gcp_diagrams/assets/category-icons/Category Icons/Security Identity/PNG/SecurityIdentity-512-color.png",
    "/usr/local/google/home/shacharb/skynet/.agents/skills/creating_gcp_diagrams/assets/category-icons/Category Icons/Networking/PNG/Networking-512-color.png"
  ]
}
```

#### 3. Steering Guidelines & Brand Compliance (For Premium Aesthetics)

Ensure your prompt instructs the image generation model to strictly follow the official Google Cloud Architecture Diagram Style Guidelines (go/diagram-style):

##### A. Typography Specifications

Use sentence case for all text labels. Monospace must be used for code to distinguish it from copy. Keep text labels extremely brief to prevent generation scrambling.

##### B. Harmonious Color Palette

Always map components and boundaries to these specific Hex codes. Avoid default browser primaries:

- **Header Block**: Google Blue 600 (`#1A73E8`) background.
- **Text & Borders**: Google Gray 900 (`#202124`) for crisp high-contrast legibility.
- **Region Containers**: Google Gray 100 (`#F1F3F4`) background.
- **Zone / Network Containers**: Select from standard Google theme colors:
  - _Blue theme_: Google Blue 200 (`#AECBFA`) or Blue 300 (`#8AB4F8`).
  - _Gray theme_: Google Gray 200 (`#E8EAED`) or Gray 300 (`#DADCE0`).
  - _Yellow theme_: Google Yellow 100 (`#FEEFC3`) or Yellow 200 (`#FDE293`).
  - _Green theme_: Google Green 100 (`#CEEAD6`) or Green 200 (`#A8DAB5`).
  - _Red theme_: Google Red 100 (`#FAD2CF`) or Red 200 (`#F6AEA9`).
- **Annotations & Captions**: Google Blue 700 (`#1967D2`).

##### C. Containers & Card Elements Geometry

Maintain structural alignment and visual spacing using flat 2D vector elements:

- **Borders**: `2pt` border stroke weight, with a `6pt` (rounded) corner radius.
- **Sizing**: Product cards should have a standard card height of `110px` with unified internal margins of `15px`.
- **Product Icons**: Square icons, scaled to `24px` inside product cards.

##### D. Flow & User Path Specifications

Use line patterns to convey structural hierarchy and status:

- **Primary Data Path**: Solid, dark line (`2pt` weight, Google Gray 900 `#202124`).
- **Secondary Control Path**: Dashed line (`2pt` weight, Google Gray 900 `#202124`).
- **Colored Paths**: Limit colored paths to Blue 700 (`#1967D2`), Green 600 (`#34A853`), Red 700 (`#C5221F`), or Yellow 600 (`#F9AB00`).

---

### Phase 3: Embed & Verify

1. Integrate the generated assets into your final document as standard markdown image links.
2. Verify that all image file paths resolve correctly in the workspace.

---

## 💡 Gotchas & Troubleshooting

- **Scrambled Text inside Images**: If the generated PNG contains scrambled letters, instruct the generator to simplify text labels to standard acronyms (e.g., use `VM` instead of `Virtual Machine`) or remove text completely and rely entirely on icons and structural lines.
