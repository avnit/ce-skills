---
name: creating-gcp-diagrams
description: >-
  Guides the generation of high-fidelity Google Cloud architecture diagrams (PNG) and/or lightweight Mermaid markdown code based on a configurable output mode, utilizing the pre-packaged official GCP Category Icons library for style anchoring and hallucination-free rendering.
---

# Skill: GCP Architecture Diagramming & Asset Generation

This skill guides you to create professional architectural diagrams, network topologies, and request flows using a configurable representation standard. It supports generating **high-definition flat-vector images** (conforming to Google Cloud design standards) and **lightweight Mermaid markdown flowcharts** depending on the document's specific requirements.

To eliminate hallucinations and enforce absolute brand-consistency in generated images, this skill leverages a **pre-packaged official Google Cloud Category Icons library** for local style and layout anchoring.

---

## 🎛️ Skill Configuration & Inputs

When invoking this skill, the calling context or steering instructions must specify:

1.  **`Mode`**:
    - `"dual"` (Default): Generates both Mermaid code and the HD PNG image, embedding both sequentially (Mermaid within a collapsible block).
    - `"mermaid-only"`: Generates only the lightweight GFM-compliant Mermaid flowchart.
    - `"image-only"`: Generates only the high-fidelity vector PNG diagram.
2.  **`ImageName`** (Required for `"dual"` and `"image-only"`): Unique snake_case filename (e.g., `peered_vpc_mesh`).
3.  **`DestinationFolder`** (Required for `"dual"` and `"image-only"`): Target workspace folder (e.g., `meeting/customer_a/assets/` or `labs/dev/gke-filestore/img/`).

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

### Phase 2: Generate GCP-Styled Mermaid Code & Local PNG Rendering (Pre-Approval)

#### 1. Write GFM-Compliant Mermaid Code

Generate a clean, well-structured, GFM-compliant Mermaid.js flowchart. Follow these architectural mapping standards:

- **Direction**: Use `graph TD` (Top-to-Bottom) for regional/hierarchical layers, or `graph LR` (Left-to-Right) for sequential request paths.
- **Subgraphs**: Enclose logical boundaries in subgraphs with clear, capitalized labels (e.g., `subgraph VPC_A ["VPC Network A (10.10.0.0/16)"]`).
- **Node Names**: Use short, uppercase abbreviations (e.g., `GCLB`, `MIG`, `NAT`, `PSC`) to keep elements compact.

#### 2. Apply Google Cloud Theme Classes & Styling

To ensure that Mermaid diagrams rendered inside documents look professional and follow official Google Cloud aesthetics, **you MUST define and append standard GCP color classes** at the end of every Mermaid code block:

```mermaid
%% GCP Style Classes
classDef default fill:#ffffff,stroke:#202124,stroke-width:2px,rx:6px,ry:6px,color:#202124,font-family:'Google Sans';
classDef header fill:#1A73E8,stroke:#1A73E8,stroke-width:2px,color:#ffffff,font-weight:bold,font-family:'Google Sans';
classDef region fill:#F1F3F4,stroke:#202124,stroke-width:1px,color:#202124,font-family:'Google Sans';
classDef vpc fill:#AECBFA,stroke:#202124,stroke-width:1.5px,color:#202124,font-family:'Google Sans';
classDef subnet fill:#E8EAED,stroke:#202124,stroke-width:1px,color:#202124,font-family:'Google Sans';
classDef zone fill:#CEEAD6,stroke:#202124,stroke-width:1px,color:#202124,font-family:'Google Sans';
```

Apply style classes explicitly to key nodes or subgraphs using the `:::` syntax:

- Apply `:::header` to the main title card.
- Apply `:::vpc` to VPC network subgraph boundaries.
- Apply `:::subnet` or `:::region` to nested environment subgraphs.
- Apply `:::zone` to active zones.

#### 3. Compile Mermaid Code to Local PNG (Pre-Approval Embed)

To prevent unrendered raw text code blocks from cluttering the IDE markdown preview, **you MUST compile the Mermaid diagram locally to a static PNG asset** and embed that image directly into the document before submitting for user approval:

1.  Save the generated Mermaid syntax (including GCP classes) into a temporary file in your scratch folder (e.g., `/usr/local/google/home/shacharb/.gemini/jetski/scratch/temp_mermaid.mermaid`).
2.  Run `mermaid-cli` locally in the shell to compile it into a high-definition PNG image with a white background and appropriate padding:
    ```bash
    npx -y @mermaid-js/mermaid-cli -i /usr/local/google/home/shacharb/.gemini/jetski/scratch/temp_mermaid.mermaid -o /path/to/destination/assets/mermaid_render.png -b white -p 20
    ```
3.  Embed the generated `mermaid_render.png` in the document:
    `markdown
![Architecture Diagram](assets/mermaid_render.png)
`
    This guarantees that the IDE markdown preview renders a beautiful, brand-aligned layout of the architecture diagram immediately!

---

### Phase 3: Generate High-Definition Visual Asset (Executed for `dual` and `image-only` modes)

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
  "Prompt": "Generate a professional flat 2D vector Google Cloud architecture diagram. Replicate the exact visual style, clean geometry, and color palette of the attached 'SecurityIdentity-512-color.png' and 'Networking-512-color.png' reference files. Draw a secure mesh peering between 'vpc-frontend' (Networking style) protected by 'cloud-armor' (Security Identity style). Target Mermaid: <Mermaid Code Block>",
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

Use sentence case for all text labels. Monospace must be used for code to distinguish it from copy.

- **Project Main Header**: 24px Google Cloud Logo, reverse text (White `#FFFFFF`) on Blue 600 background.
- **Region & Zone Headings**: 17pt, Google Sans Text Normal, Google Gray 900 (`#202124`).
- **Product Card (No Icon)**: 14pt, Google Sans Text Bold, Google Gray 900 (`#202124`).
- **Product Card (With Icon)**: Title 14pt Google Sans Text Bold, Subtext 12pt Google Sans Text Normal, Google Gray 900 (`#202124`).
- **Product Card (With Icon & Code)**: Title 14pt Google Sans Text Bold, Subtext 12pt Google Sans Text Normal, Code 12pt Roboto Mono Normal (monospace), Google Gray 900 (`#202124`).
- **User Card**: 14pt, Google Sans Text Bold, Google Gray 900 (`#202124`).
- **Path Description / Labels**: 10pt, Google Sans Text Bold, Google Gray 900 (`#202124`).

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
- **GCP Logo**: Display a White/Reverse Google Cloud Logo inside the Blue 600 header (25px height).
- **Product Icons**: Square icons, scaled to `24px` inside product cards.

##### D. Flow & User Path Specifications

Use line patterns to convey structural hierarchy and status:

- **Primary Data Path**: Solid, dark line (`2pt` weight, Google Gray 900 `#202124`).
- **Secondary Control Path**: Dashed line (`2pt` weight, Google Gray 900 `#202124`).
- **Tertiary / Async Path**: Dotted line (`2pt` weight, Google Gray 900 `#202124`).
- **Status Indicator**: Use checkmarks (green check for success, red X for failure).
- **Colored Paths**: Limit colored paths to Blue 700 (`#1967D2`), Green 600 (`#34A853`), Red 700 (`#C5221F`), or Yellow 600 (`#F9AB00`).

---

### Phase 4: Embed & Verify

1. Integrate the generated assets into your final document using the layout corresponding to the selected `Mode` (collapsible layout for `dual`, standard image link for `image-only`, raw mermaid block for `mermaid-only`).
2. Verify that all image file paths resolve correctly in the workspace and that the Mermaid code compiles successfully.

---

## 💡 Gotchas & Troubleshooting

- **Scrambled Text inside Images**: If the generated PNG contains scrambled letters, instruct the generator to simplify text labels to standard acronyms (e.g., use `VM` instead of `Virtual Machine`).
- **Mermaid Rendering Errors**: Ensure there are no special characters, unmatched brackets `()`, or HTML tags inside your Mermaid node names, as these break Markdown rendering.
