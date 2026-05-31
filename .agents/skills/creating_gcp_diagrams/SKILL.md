---
name: creating-gcp-diagrams
description: >-
  Delegates professional Google Cloud architecture diagram generation to the diagram-generator specialized sub-agent.
---

# Skill: Creating Google Cloud Architecture Diagrams & Assets (Delegated Flow)

This skill guides you to delegate the creation of professional, high-fidelity architectural diagrams, network topologies, flow sequences, and mockups to the specialized **`diagram-generator`** sub-agent. By delegating this compute-intensive and time-consuming image-generation task, the Central Commander remains responsive and focused on active validation and human pair-programming.

---

## Dynamic Delegation Workflow

Copy this checklist to your active `task.md` progress tracker and execute:

### 📋 Step 1: Spawn the Diagram Specialist Sub-Agent
Spawn the specialized **`diagram-generator`** sub-agent asynchronously using the `invoke_subagent` tool. 
Pass the target technical file path (e.g., a blueprint markdown, narrative lab steps, or HCL configuration) as the parameter.

#### Execution Example:
```json
{
  "Subagents": [
    {
      "TypeName": "diagram-generator",
      "Role": "Diagram Specialist Generator",
      "Prompt": "Please parse the network topology and VPC resources defined in the design blueprint. Construct a highly descriptive visual prompt conforming to Google Cloud design guidelines, execute the generate_image tool to render the flat-vector diagram, and write your standard findings JSON envelope to diagram_response.json. Target file path: labs/dev/session-balancing-l7/blueprint.md"
    }
  ]
}
```

### 🎨 Step 2: Google Cloud Design Guidelines (For Specialist Steering)
Ensure your prompt instructs the Specialist to apply the official Google Cloud visual standards:
1.  **Background**: Clean, solid white background (`#FFFFFF`). Never use dark, black, or busy backgrounds.
2.  **Containers**: Use flat 2D vector style cards with rounded corners (6px corner radius):
    *   **Project / VPC Boundaries**: Thin Google Cloud Blue (`#1A73E8`) outlines.
    *   **Component Cards**: Border weight 2pt, rounded corner radius 6px, border color Gray 900 (`#202124`).
3.  **Typography**: Clean, legible sans-serif font (Google Sans style). Components should use clear, short abbreviations (e.g., `VM`, `MIG`, `GCLB`, `NAT`, `NEG`) to prevent text garbling.
4.  **Flow Paths**: Crisp solid black horizontal or vertical arrows (`#202124`) for primary data paths; dashed black arrows for secondary or control paths.

### 📁 Step 3: Ingest findings JSON Envelope
Once the sub-agent completes, read its standardized `diagram_response.json` findings envelope from the sub-agent's brain folder. Verify that the status is `SUCCESS`.

### 📁 Step 4: Image Verification & Target Placement
1.  Verify that the generated PNG diagram file has been saved to the active artifacts directory.
2.  **Mandatory Placement**: Copy the generated image from the artifacts folder into the target project/codelab subdirectory (e.g., `./img/` or `./assets/`).
3.  Reference the diagram in your narrative markdown tutorial or design blueprint using the relative path (e.g., `![](./img/my_generated_diagram.png)`).

---

## Gotchas & Troubleshooting

*   **Misspelled Text inside Cards**: If the generated diagram contains scrambled or misspelled words, request the sub-agent to simplify card labels in its prompt formulation to short standard acronyms (e.g., use `VM` instead of `Virtual Machine Instance`).
*   **Do Not Block the Main Timeline**: Never execute the raw `generate_image` tool inside the Central Commander's timeline if a `diagram-generator` sub-agent is available. Always delegate this job.
