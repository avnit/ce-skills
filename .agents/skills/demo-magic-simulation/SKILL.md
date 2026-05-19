---
name: demo-magic-simulation
description: Parses Google Cloud Codelab markdown tutorials to extract terminal instructions via negative output filtering, compiling standalone, self-contained executable bash scripts that simulate realistic human typing pacing via an embedded demo-magic engine.
---

# Skill: Demo-Magic Human Simulation

The **Demo-Magic Human Simulation Skill** automates the creation of dynamic command-line presentations from standard Google Cloud Codelab markdown files (`.lab.md`). 

Instead of manually copying and pasting terminal commands during live demonstrations or screen recordings, this skill parses tutorial instructions, strips out inline terminal sample outputs using smart negative filtering, and generates a fully self-contained, standalone executable bash script. When executed, the generated script simulates realistic human typing speeds character-by-character and pauses for the presenter to press `ENTER` before firing each instruction.

## 🌟 Key Capabilities

1. **Embedded Demonstration Engine**: Directly embeds custom multi-platform `demo-magic` logic (`pe`, `p`, `cmd`) at the top of the compiled file, guaranteeing the final bash script runs flawlessly on macOS/Linux without requiring any external file dependencies.
2. **Smart Negative Filtering**: Scans fenced `bash` or `console` blocks to isolate actual execution commands from sample terminal output blocks (e.g., automatically discards blocks matching `Output:`, `ACTIVE`, `Credentialed accounts:`).
3. **Automatic Presentation Preservation (No Cleanup Audits)**: Automatically tracks active markdown section headings during parsing to proactively bypass any instructions contained inside **Clean up** or **Delete** sections. This guarantees that your presentation infrastructure remains fully alive and operational at the end of the demonstration script, giving audiences ample time to witness and inspect final working states.
4. **Automated System Variable Normalization**: Automatically normalizes prose-style placeholders (e.g., `<PROJECT_ID>`, `YOUR_PROJECT_ID`) into standardized `$PROJECT_ID` shell variables. Pre-injects a default system parameters header that automatically resolves `$PROJECT_ID` to your active Cloud Shell environment (`$GOOGLE_CLOUD_PROJECT`).
5. **Seamless Google Cloud Shell Integration**: Automatically outputs a secondary copy-pasteable launcher wrapper using quoted heredocs (`cat << 'EOF'`) that generates, permissions, and runs the demo script instantly when pasted into a web terminal while preserving inner dynamic variable inheritance perfectly.
6. **Clean Subfolder Organization**: Automatically creates a dedicated `demo/` subdirectory under your target lab folder to place compiled output scripts cleanly, eliminating root folder clutter.
7. **Customizable Humanized Pacing**: Configures typing speeds (default 20 characters per second) and beautiful colored prompt prefixes directly via CLI generation arguments.

---

## 🚀 Operational Usage

### Generating a Self-Contained Demonstration Script

Execute the generation engine script against any target codelab markdown file. By default, it cleanly organizes output scripts into a `demo/` subfolder directly under the source lab directory:

```bash
python3 .agents/skills/demo-magic-simulation/scripts/generate_demo.py \
    --lab labs/dev/multi-vpc-dns-forwarding/multi-vpc-dns-forwarding.lab.md
```

**Default Generated Output Paths**:
- Standalone Script: `labs/dev/multi-vpc-dns-forwarding/demo/multi-vpc-dns-forwarding_demo.sh`
- Cloud Shell Wrapper: `labs/dev/multi-vpc-dns-forwarding/demo/multi-vpc-dns-forwarding_demo_cloudshell_launcher.sh`

### Advanced Compilation Arguments

You can tailor the generated output script's behavior using extra flags:

```bash
python3 .agents/skills/demo-magic-simulation/scripts/generate_demo.py \
    --lab labs/dev/multi-vpc-dns-forwarding/multi-vpc-dns-forwarding.lab.md \
    --output /path/to/custom_presentation.sh \
    --speed 25 \
    --prompt "gcp-demo$ " \
    --region "us-east1" \
    --vars BUCKET_NAME="my-demo-bucket" CLUSTER_NAME="demo-cluster"
```

| Flag | Description | Default Value |
| :--- | :--- | :--- |
| `--lab` | Absolute or relative path to the source `.lab.md` file. | **Required** |
| `--output` | Custom destination path for the generated bash script. | `<lab_dir>/demo/<lab_basename>_demo.sh` |
| `--speed` | Simulated human typing speed (characters per second). | `20` |
| `--prompt` | Custom prompt prefix displayed before simulated commands. | `"$ "` |
| `--region` | Default GCP region parameter injected into script setup. | `"us-central1"` |
| `--zone` | Default GCP zone parameter injected into script setup. | `"us-central1-a"` |
| `--vars` | Additional system parameter overrides in `KEY=VALUE` format. | `[]` |

---

## 🎬 Running the Generated Presentation

### Option A: Local Execution
Navigate to your generated demo folder and execute the standalone script directly:
```bash
./labs/dev/multi-vpc-dns-forwarding/demo/multi-vpc-dns-forwarding_demo.sh
```

### Option B: Google Cloud Shell Web Terminal (Single-Block Paste)
Open the companion `_cloudshell_launcher.sh` file generated inside your `demo/` folder. It contains a single copy-pasteable heredoc block that writes out the file, applies execution permissions, and triggers the simulation automatically:

```bash
cat << 'EOF' > multi-vpc-dns-forwarding_demo.sh
#!/usr/bin/env bash
# ... complete embedded script content ...
EOF
chmod +x multi-vpc-dns-forwarding_demo.sh
./multi-vpc-dns-forwarding_demo.sh
```
Simply copy the block, paste it directly into your Cloud Shell console, and the demonstration starts instantly. Because the heredoc uses quoted `'EOF'`, variables like `$PROJECT_ID` remain fully dynamic and automatically adopt your active Cloud Shell session's project mapping upon execution.

---

### Presentation Flow
1. The prompt prefix appears.
2. The script automatically simulates typing the command out character-by-character as a human.
3. The simulation pauses, waiting for you to press **`ENTER`**.
4. The command executes live, displaying output directly to the viewport.
