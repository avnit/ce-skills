#!/usr/bin/env python3
"""
Automated Lab Execution Engine (Unified Dual-Mode Controller)

This script automates the step-by-step execution of Google Cloud codelabs inside your
Google Chrome browser using Playwright. It parses executable bash commands from source
markdown files using a deterministic state machine, skips expected console outputs,
normalizes space tokens, drops generic project placeholders, configures target GCP
project parameters, bypasses overlapping xterm screen pointer masks, applies smart
multiline prompt checking, and proactively halts operations if critical error signatures
emerge inside pristine appended output deltas.

Execution Modes:
1. --use-cdp: Attaches directly to your existing open Chrome profile session over port 9222.
2. Native Mode (Default): Automatically launches your installed desktop Chrome application.

Enterprise Resiliency, Scalability, & Self-Healing Features:
- Run-Specific Subdirectories: Automatically routes runbook.json, test_status.md, and run.state logs into isolated runs/run_<timestamp>/ folders.
- Across-Run State Checkpointing: Automatically locates and pre-loads hashes from the most recent previous run folder to support seamless resumption.
- Autonomous Gemini Self-Healing: Integrates Vertex AI reasoning agents to intercept terminal runtime error deltas, diagnose environment pre-requisite gaps, inject targeted JSON recovery command sequences inline, and automatically retry failing steps transparently (toggled via --self-heal).
"""

import asyncio
import argparse
import datetime
import hashlib
import logging
import os
import re
import sys
import json
import glob
from typing import List, Optional, Dict, Tuple
from pydantic import BaseModel, Field
from playwright.async_api import async_playwright, Page

# Configure standard stream logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("LabExecutionEngine")


class Instruction(BaseModel):
    """Structured schema representing a cohesive executable lab instruction block."""
    index: int = Field(..., description="Sequential execution index.")
    block_hash: str = Field(..., description="SHA-256 hermetic hash of the stripped code block content.")
    commands: List[str] = Field(..., description="Ordered list of actionable command statements extracted from the block.")
    raw_block: str = Field(..., description="Original unmodified fenced block text.")
    is_project_init: bool = Field(default=False, description="Flag denoting if instruction injects explicit project scope.")


class ExecutionConfig(BaseModel):
    """Strict validation schema for execution automation input variables."""
    markdown_path: str = Field(..., description="Path to the source markdown lab document.")
    project_id: Optional[str] = Field(default=None, description="Target GCP Project ID to automatically target upon initialization.")
    use_cdp: bool = Field(
        default=False,
        description="Attach directly to existing open browser session via CDP instead of spawning native application profile windows."
    )
    cdp_url: str = Field(
        default="http://localhost:9222",
        description="Base remote debugging host endpoint mapping to active Chrome debug servers."
    )
    executable_path: str = Field(
        default="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        description="Absolute path mapping to the host native system Google Chrome binary."
    )
    user_data_dir: str = Field(
        default=os.path.expanduser("~/.config/gcp_automation_profile"),
        description="Persistent local profile path caching active session cookies and authenticated accounts."
    )
    gcp_console_url: str = Field(
        default="https://console.cloud.google.com/?cloudshell=true",
        description="Target landing URL to load the Google Cloud Shell UI."
    )
    headless: bool = Field(
        default=False,
        description="Run browser headlessly. Defaults to False to support visual side-by-side external screen recording."
    )
    typing_delay_ms: int = Field(default=50, description="Simulated human pacing delay between keystroke streams.")
    post_command_padding_ms: int = Field(default=2000, description="Stabilization wait period after command completion.")
    step_timeout_ms: int = Field(default=300000, description="Maximum timeout threshold per terminal step (default 5 mins).")
    dry_run: bool = Field(default=False, description="Compile JSON execution plan and exit without executing automation streams.")
    force_reset: bool = Field(default=False, description="Ignore existing .state checkpoint file and run all instructions from the beginning.")
    self_heal: bool = Field(default=False, description="Enable autonomous Gemini agent intervention loops to diagnose and recover from terminal errors inline.")
    max_retries: int = Field(default=2, description="Maximum automatic retry attempts per failed instruction block when self-healing is enabled.")
    human_in_the_loop: bool = Field(default=True, description="Enable manual terminal intervention when an unrecovered runtime exception occurs.")
    negative_filters: List[str] = Field(
        default=[
            "Credentialed accounts:", "Status: ACTIVE", "[core] project", "command not found", "Output:",
            "result.bgpPeerStatus", "learnedRoutes"
        ],
        description="Substring signatures used to detect and bypass non-executable terminal output examples."
    )


class SelfHealingAgent:
    """Integrated inline Gemini reasoning module providing autonomous runtime CLI error diagnosis and recovery."""
    
    def __init__(self, config: ExecutionConfig):
        self.config = config
        self.initialized = False
        self.model = None
        self._initialize_vertex_ai()

    def _initialize_vertex_ai(self):
        """Dynamically imports and initializes Vertex AI generative models utilizing workspace authentication parameters."""
        if not self.config.self_heal:
            return
            
        try:
            import google.auth
            import vertexai
            from vertexai.generative_models import GenerativeModel
            
            # Inherit workspace project context bindings dynamically via ADC flows
            _, credentials_project_id = google.auth.default()
            project = credentials_project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
            location = "us-central1"
            
            if project:
                vertexai.init(project=project, location=location)
                # Utilize optimized reasoning model profile ensuring low latency inline evaluation
                self.model = GenerativeModel("gemini-2.5-flash")
                self.initialized = True
                logger.info(f"Successfully initialized integrated Gemini Self-Healing Agent subsystem targeting project context: {project}")
            else:
                logger.warning("Gemini Self-Healing Agent initialization skipped: Failed to resolve active Google Cloud Project context via ADC.")
        except ImportError:
            logger.warning("Gemini Self-Healing Agent initialization skipped: Vertex AI SDK packages not discovered in current runtime environment.")
        except Exception as e:
            logger.warning(f"Failed initializing integrated Gemini Self-Healing Agent subsystem: {e}")

    async def diagnose_and_recover(self, failing_cmd: str, error_delta: str, raw_block: str) -> Tuple[bool, str, List[str]]:
        """Queries Gemini to analyze terminal output deltas and returns structured JSON recovery runbooks."""
        if not self.initialized or not self.model:
            logger.debug("Self-healing agent bypass triggered: Module remains uninitialized or unauthenticated.")
            return False, "Agent subsystem uninitialized.", []
            
        logger.info("🤖 Triggering autonomous Gemini Self-Healing reasoning cycle to evaluate terminal runtime exception...")
        
        prompt = f"""You are an expert Google Cloud platform infrastructure automation technician.
A deterministic codelab tutorial step has failed during live execution inside a Google Cloud Shell terminal.

Context of the current tutorial block:
{raw_block}

Failing Command:
{failing_cmd}

Observed Terminal Error/Output Delta:
{error_delta}

Your task is to diagnose the root cause (e.g., API non-activation, missing IAM binding, race condition, or propagation lag) and output a targeted sequence of zero or more non-breaking recovery bash commands to execute in the shell to resolve the prerequisite failure.
CRITICAL RULE: Do NOT change or skip the core tutorial commands. Provide ONLY pre-requisite fixes (e.g., enabling an API, sleeping, or adding a permission) that will allow the original failing command to succeed upon automatic retry.

Return your response strictly as a JSON object matching this schema:
{{
  "diagnosis": "Brief explanation of the root cause",
  "recovery_commands": ["gcloud ...", "sleep ..."]
}}
"""
        try:
            # Offload synchronous network execution thread safely
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config={"temperature": 0.1}
            )
            
            text_resp = response.text
            # Robust JSON block extraction stripping conversational prose or raw markdown boundaries
            json_match = re.search(r"\{.*\}", text_resp, re.DOTALL)
            if not json_match:
                logger.warning(f"Failed parsing structured JSON payload from Gemini recovery response:\n{text_resp}")
                return False, "Non-JSON output returned.", []
                
            data = json.loads(json_match.group(0))
            diagnosis = data.get("diagnosis", "No explicit diagnosis provided.")
            recovery_cmds = data.get("recovery_commands", [])
            
            logger.info(f"🤖 Gemini Diagnosis: {diagnosis}")
            logger.info(f"🤖 Proposed Recovery Sequences: {len(recovery_cmds)} commands scheduled.")
            return True, diagnosis, recovery_cmds
            
        except Exception as e:
            logger.error(f"Gemini Self-Healing reasoning pipeline query failed: {e}")
            return False, f"Query exception: {e}", []


class ParsingEngine:
    """Scans markdown structures using deterministic state loops to compile ordered instruction graphs."""
    
    def __init__(self, config: ExecutionConfig):
        self.config = config

    def _get_sha256_hash(self, content: str) -> str:
        """Computes SHA-256 hermetic hash ensuring alignment with deterministic runner state tracking."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def parse(self, markdown_content: str) -> List[Instruction]:
        """Extracts instruction blocks line-by-line compiling a JSON-ready decoupled runbook graph."""
        instructions: List[Instruction] = []
        in_block = False
        current_block_lines: List[str] = []
        step_counter = 1
        
        if self.config.project_id:
            init_cmd = f"gcloud config set project {self.config.project_id}"
            init_hash = self._get_sha256_hash(init_cmd)
            instructions.append(
                Instruction(
                    index=step_counter,
                    block_hash=init_hash,
                    commands=[init_cmd],
                    raw_block=f"```bash\n{init_cmd}\n```",
                    is_project_init=True
                )
            )
            step_counter += 1

        for line in markdown_content.splitlines():
            line_stripped = line.strip()
            
            if not in_block and (line_stripped.startswith("```bash") or line_stripped.startswith("```console")):
                in_block = True
                current_block_lines = []
                continue
                
            if in_block and line_stripped.startswith("```"):
                in_block = False
                block_content = "\n".join(current_block_lines).strip()
                if not block_content:
                    continue
                    
                b_strip = block_content.strip()
                if b_strip == "10.20.30.150" or b_strip.startswith("10.20.30.99"):
                    continue
                    
                is_output = any(f.lower() in block_content.lower() for f in self.config.negative_filters)
                if is_output:
                    continue
                    
                lines = block_content.split('\n')
                extracted_commands: List[str] = []
                current_cmd = ""
                
                for line in lines:
                    l_str = line.strip()
                    if not l_str or l_str.startswith('#'):
                        continue
                        
                    if l_str.startswith('$ '):
                        l_str = l_str[2:].strip()
                        
                    if l_str.endswith('\\'):
                        current_cmd += l_str[:-1] + " "
                    else:
                        current_cmd += l_str
                        if current_cmd.strip():
                            cleaned = re.sub(r'\s+', ' ', current_cmd.strip())
                            if cleaned != "gcloud config set project <PROJECT_ID>":
                                extracted_commands.append(cleaned)
                        current_cmd = ""
                        
                if current_cmd.strip():
                    cleaned = re.sub(r'\s+', ' ', current_cmd.strip())
                    if cleaned != "gcloud config set project <PROJECT_ID>":
                        extracted_commands.append(cleaned)
                        
                if extracted_commands:
                    b_hash = self._get_sha256_hash(block_content)
                    instructions.append(
                        Instruction(
                            index=step_counter,
                            block_hash=b_hash,
                            commands=extracted_commands,
                            raw_block=f"```bash\n{block_content}\n```"
                        )
                    )
                    step_counter += 1
                    
                continue
                
            if in_block:
                current_block_lines.append(line)
                
        return instructions

    def export_json_plan(self, instructions: List[Instruction], output_path: str):
        """Serializes compiled instruction mapping graph cleanly to standard JSON output files."""
        plan = {
            "source_lab": self.config.markdown_path,
            "target_project": self.config.project_id,
            "compiled_timestamp": datetime.datetime.now().isoformat(),
            "total_steps": len(instructions),
            "execution_plan": [inst.model_dump() for inst in instructions]
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2)
        logger.info(f"Successfully exported decoupled JSON execution runbook map to: {output_path}")


class ExecutionEngine:
    """Orchestrates Cloud Shell commands utilizing run-specific subdirectories and inline self-healing loops."""
    
    def __init__(self, config: ExecutionConfig):
        self.config = config
        self.base_dir = os.path.dirname(config.markdown_path)
        self.lab_basename = os.path.splitext(os.path.basename(config.markdown_path))[0]
        
        # Initialize robust dynamic Run Subdirectory paths isolating artifacts per recording attempt
        timestamp_tag = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_folder_name = f"run_{timestamp_tag}"
        self.run_dir = os.path.join(self.base_dir, "runs", self.run_folder_name)
        os.makedirs(self.run_dir, exist_ok=True)
        logger.info(f"📁 Created isolated recording run output subdirectory: {self.run_dir}")
        
        # Map run-specific diagnostic artifact file trajectories
        self.json_plan_path = os.path.join(self.run_dir, "runbook.json")
        self.status_file = os.path.join(self.run_dir, "test_status.md")
        self.state_file = os.path.join(self.run_dir, "run.state")
        
        # Write global top-level directory tracker referencing currently active run folders
        pointer_path = os.path.join(self.base_dir, "latest_run_dir.txt")
        with open(pointer_path, "w", encoding="utf-8") as f:
            f.write(os.path.join("runs", self.run_folder_name))
            
        self.executed_hashes: List[str] = []
        self.self_healing_agent = SelfHealingAgent(config=config)
        self._synchronize_historical_state()

    def _synchronize_historical_state(self):
        """Intelligently discovers across-run history pre-loading completed hashes from recent run checkpoints."""
        if self.config.force_reset:
            logger.info("Force reset triggered. Initiating pristine state cache logs bypassing historical run checks.")
            return
            
        # Scan base runs array to identify historical state files sorted chronologically
        runs_pattern = os.path.join(self.base_dir, "runs", "run_*", "run.state")
        existing_states = sorted(glob.glob(runs_pattern), key=os.path.getmtime, reverse=True)
        
        if existing_states:
            latest_prev_state = existing_states[0]
            # Prevent reading from our dynamically created current file if matched
            if os.path.abspath(latest_prev_state) != os.path.abspath(self.state_file):
                logger.info(f"Across-Run state synchronization: Synchronizing completed hashes from preceding run checkpoint: {latest_prev_state}")
                with open(latest_prev_state, "r", encoding="utf-8") as f:
                    self.executed_hashes = [line.strip() for line in f.readlines() if line.strip()]
                logger.info(f"Successfully loaded {len(self.executed_hashes)} verified instruction block hashes from historical runs.")
                
                # Mirror populated historical hashes into active run state cache log instantly
                with open(self.state_file, "w", encoding="utf-8") as f:
                    for h in self.executed_hashes:
                        f.write(f"{h}\n")

    def _save_hash_state(self, block_hash: str):
        """Appends successfully completed instruction block hashes to isolated run state logs."""
        if block_hash not in self.executed_hashes:
            with open(self.state_file, "a", encoding="utf-8") as f:
                f.write(f"{block_hash}\n")
            self.executed_hashes.append(block_hash)

    def _update_status_markdown(self, instructions: List[Instruction], current_idx: int, step_results: Dict[int, bool]):
        """Updates local test_status.md tracking file dynamically inside run folders."""
        try:
            project_disp = self.config.project_id or "Not specified"
            with open(self.status_file, "w", encoding="utf-8") as f:
                f.write(f"# Test Status: Codelab Execution ({self.run_folder_name})\n\n")
                f.write(f"**Project ID**: `{project_disp}`\n\n")
                f.write("## Detailed Progress (Step Level)\n\n")
                
                for idx, inst in enumerate(instructions):
                    status_icon = "[ ]"
                    if idx < current_idx:
                        status_icon = "[x]" if step_results.get(idx, False) else "[!]"
                    elif idx == current_idx:
                        status_icon = "[!]" if step_results.get(idx) is False else "[/]"
                        
                    cmd_preview = inst.commands[0][:60] + "..." if len(inst.commands[0]) > 60 else inst.commands[0]
                    f.write(f"- {status_icon} {inst.index}. `{cmd_preview}`\n")
                    
                f.write("\n## Progress Details\n")
                f.write(f"- **Last Checked**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                if current_idx < len(instructions):
                    f.write(f"- **Current Action**: Running Step {current_idx + 1}\n")
                else:
                    f.write("- **Current Action**: Completed\n")
        except Exception as e:
            logger.warning(f"Failed updating run status tracking file {self.status_file}: {e}")

    async def _run_cdp_attachment(self, instructions: List[Instruction]) -> bool:
        """Attaches directly to root-level browser debug pipes to resolve global tab descriptors reliably."""
        logger.info(f"Attaching Playwright automation channels directly to root CDP endpoint: {self.config.cdp_url}")
        async with async_playwright() as p:
            try:
                browser = await p.chromium.connect_over_cdp(self.config.cdp_url, timeout=30000)
            except Exception as e:
                logger.error(f"Failed establishing CDP transport pipe to base endpoint {self.config.cdp_url}: {e}", exc_info=True)
                logger.error(
                    "Ensure Google Chrome is open and launched from your terminal with remote debugging active:\n"
                    "open -a 'Google Chrome' --args --remote-debugging-port=9222"
                )
                return False
                
            context = browser.contexts[0]
            # Stabilization loop allowing async background page arrays to fully resolve
            for _ in range(10):
                if context.pages:
                    break
                await asyncio.sleep(0.5)
                
            pages = context.pages
            if not pages:
                logger.error("Connected to base CDP endpoint successfully, but global page descriptor map remained empty.")
                await browser.close()
                return False
                
            # Traverse exposed page array to discover loaded Google Cloud Console dashboards
            target_page: Optional[Page] = None
            for page in pages:
                try:
                    if "console.cloud.google.com" in page.url:
                        target_page = page
                        logger.info(f"Discovered active Google Cloud Console tab: {page.url}")
                        break
                except Exception:
                    continue
                    
            if not target_page:
                logger.info("No explicit console page discovered in background array. Utilizing primary active document scope...")
                target_page = pages[0]
                
            try:
                logger.info(f"Ensuring dashboard navigation parameters map to: {self.config.gcp_console_url}")
                if "cloudshell=" not in target_page.url:
                    await target_page.goto(self.config.gcp_console_url, timeout=60000)
                return await self._drive_terminal_execution(target_page, instructions)
            finally:
                logger.info("Disconnecting CDP automation channels from targeted browser context...")
                await browser.close()

    async def _run_native_launcher(self, instructions: List[Instruction]) -> bool:
        """Launches installed native system browser profile windows directly in the foreground."""
        logger.info("Launching host system Google Chrome application visibly via persistent profiles...")
        if not os.path.exists(self.config.executable_path):
            logger.error(f"Target host system browser executable binary not found: {self.config.executable_path}")
            return False
            
        os.makedirs(self.config.user_data_dir, exist_ok=True)
        async with async_playwright() as p:
            try:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=self.config.user_data_dir,
                    executable_path=self.config.executable_path,
                    headless=self.config.headless,
                    viewport={"width": 1280, "height": 720},
                    args=["--disable-blink-features=AutomationControlled"]
                )
            except Exception as e:
                logger.error(f"Failed launching host system browser persistent context: {e}", exc_info=True)
                return False
                
            pages = context.pages
            page: Page = pages[-1] if pages else await context.new_page()
            try:
                logger.info(f"Navigating active tab dashboard URL: {self.config.gcp_console_url}")
                await page.goto(self.config.gcp_console_url, timeout=60000)
                
                logger.info("Identity Gateway Check: Observing authentication state redirects...")
                for _ in range(600):
                    current_pages = context.pages
                    if current_pages:
                        page = current_pages[-1]
                    if page.is_closed():
                        break
                    if "accounts.google.com" not in page.url and "console.cloud.google.com" in page.url:
                        logger.info(f"Successfully authenticated reaching primary console dashboard view: {page.url}")
                        break
                    await page.wait_for_timeout(500)
                    
                if page.is_closed():
                    raise RuntimeError("Active browser page tracking handle was closed before console stabilization.")
                    
                if "cloudshell=" not in page.url:
                    logger.info("Re-applying explicit ?cloudshell=true dashboard activation parameter...")
                    await page.goto(self.config.gcp_console_url, timeout=60000)
                    
                return await self._drive_terminal_execution(page, instructions)
            finally:
                logger.info("Closing active native system browser profile context window...")
                await context.close()

    async def _drive_terminal_execution(self, page: Page, instructions: List[Instruction]) -> bool:
        """Core execution engine driving iframe resolution, humanized keystrokes, output delta checks, and integrated self-healing retries."""
        step_results: Dict[int, bool] = {}
        for idx, inst in enumerate(instructions):
            if inst.block_hash in self.executed_hashes:
                step_results[idx] = True
                
        self._update_status_markdown(instructions, 0, step_results)
        
        try:
            logger.info("Awaiting Google Cloud Shell embedded iframe initialization...")
            # Ensure the iframe node is fully attached to DOM context scope before evaluating nested locators
            await page.wait_for_selector('iframe[src*="cloudshell"]', state="attached", timeout=90000)
            
            logger.info("Locating xterm.js text output rows matrix via persistent frame locators...")
            terminal = page.frame_locator('iframe[src*="cloudshell"]').locator('.xterm-rows, gcp-shell-fallback-terminal').first
            await terminal.wait_for(state="visible", timeout=60000)
            
            await terminal.click(force=True)
            await page.wait_for_timeout(3000)
            
            logger.info("Flushing historical screen content buffer via initial terminal clear pass...")
            await page.keyboard.type("clear", delay=self.config.typing_delay_ms)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(2000)
            
            logger.info(f"Automation execution active. Processing {len(instructions)} scheduled instruction units.")
            for idx, inst in enumerate(instructions):
                self._update_status_markdown(instructions, idx, step_results)
                
                if inst.block_hash in self.executed_hashes:
                    logger.info(f"Skipping Step [{inst.index}/{len(instructions)}]: Block hash verified in across-run state tracking logs.")
                    continue
                    
                logger.info(f"Executing Step [{inst.index}/{len(instructions)}] containing {len(inst.commands)} sub-commands.")
                
                for c_idx, cmd in enumerate(inst.commands, start=1):
                    # Core Sub-Command Injector function supporting transparent retry loop recursion
                    async def inject_subcommand_with_recovery(target_cmd: str, current_retry: int = 0) -> bool:
                        logger.info(f"-> Sub-command [{c_idx}/{len(inst.commands)}] (Attempt {current_retry + 1}): {target_cmd}")
                        await terminal.click(force=True)
                        
                        pre_content = await terminal.inner_text()
                        pre_line_count = len(pre_content.split('\n'))
                        
                        await page.keyboard.type(target_cmd, delay=self.config.typing_delay_ms)
                        await page.keyboard.press("Enter")
                        
                        prompt_stabilized = False
                        error_detected = False
                        err_msg = ""
                        
                        error_patterns = [
                            "ERROR:", "CRITICAL:", "command not found", "Permission denied", 
                            "does not exist", "invalid argument", "FAILED:", "Error:", "Exception:"
                        ]
                        interactive_patterns = [r"\[Y/n\]", r"\[y/N\]", r"Do you want to continue\?", r"Enter passphrase:"]
                        
                        poll_interval_ms = 500
                        max_polls = int(self.config.step_timeout_ms / poll_interval_ms)
                        
                        for p_cnt in range(max_polls):
                            content = await terminal.inner_text()
                            lines = [line.strip() for line in content.split('\n') if line.strip()]
                            
                            if lines:
                                last_line = lines[-1]
                                if last_line.endswith('$') or last_line.endswith('>'):
                                    prompt_stabilized = True
                                    break
                                    
                                current_lines = content.split('\n')
                                delta_lines = current_lines[max(0, pre_line_count - 2):] if len(current_lines) >= pre_line_count else current_lines
                                delta_output = "\n".join(delta_lines)
                                
                                for pattern in error_patterns:
                                    if pattern in delta_output:
                                        if target_cmd not in delta_output or delta_output.count(pattern) > target_cmd.count(pattern):
                                            error_detected = True
                                            err_msg = delta_output
                                            break
                                            
                                if error_detected:
                                    break
                                    
                                is_interactive = any(re.search(ip, last_line, re.IGNORECASE) for ip in interactive_patterns)
                                if is_interactive and p_cnt > 10:
                                    logger.warning(f"Detected interactive terminal stall prompt: '{last_line}'. Automatically injecting default affirmation override...")
                                    await page.keyboard.type("y", delay=50)
                                    await page.keyboard.press("Enter")
                                    await page.wait_for_timeout(2000)
                                    
                            await page.wait_for_timeout(poll_interval_ms)
                            
                        if error_detected:
                            logger.error(f"Execution exception intercepted during Step [{inst.index}]:\n{err_msg}")
                            
                            # 1. Trigger Autonomous Self-Healing pipeline loop if toggled and retry caps remain
                            if self.config.self_heal and current_retry < self.config.max_retries:
                                logger.info(f"🛡️ Initiating autonomous self-healing intercept loop (Attempt {current_retry + 1}/{self.config.max_retries})...")
                                success, diagnosis, recovery_cmds = await self.self_healing_agent.diagnose_and_recover(target_cmd, err_msg, inst.raw_block)
                                
                                if success and recovery_cmds:
                                    logger.info("🛡️ Applying non-breaking inline recovery instructions dynamically...")
                                    for r_cmd in recovery_cmds:
                                        logger.info(f"🛡️ -> Injecting recovery action: {r_cmd}")
                                        await terminal.click(force=True)
                                        await page.keyboard.type(r_cmd, delay=self.config.typing_delay_ms)
                                        await page.keyboard.press("Enter")
                                        await page.wait_for_timeout(5000) 
                                        
                                    logger.info("🛡️ Recovery commands applied successfully. Automatically retrying original target instruction...")
                                    return await inject_subcommand_with_recovery(target_cmd, current_retry + 1)
                                else:
                                    logger.warning("🛡️ Self-healing agent was unable to compile functional recovery scripts.")
                            
                            # 2. HUMAN-IN-THE-LOOP FALLBACK GATEWAY
                            if self.config.human_in_the_loop:
                                logger.warning(f"\n🚨 [HUMAN INTERVENTION REQUIRED] Sub-command failed at Step [{inst.index}].")
                                logger.warning(f"❌ Failing Statement: {target_cmd}")
                                logger.warning("💡 Action Required: Click into the browser window, triage the state, fix the error manually, and return here.")
                                
                                hitl_loop = True
                                while hitl_loop:
                                    # Thread-off blocking inputs safely within async loops
                                    user_choice = await asyncio.to_thread(
                                        input, 
                                        "\nChoose next operational step — [r]etry command, [s]kip step, [a]bort runbook: "
                                    )
                                    user_choice = user_choice.strip().lower()
                                    
                                    if user_choice == 'r':
                                        logger.info("🔄 Human action captured: Retrying the original command statement now...")
                                        return await inject_subcommand_with_recovery(target_cmd, current_retry=0)
                                    elif user_choice == 's':
                                        logger.warning("⏭️ Human action captured: Skipping this failing statement block. Moving to next sequence step.")
                                        await page.wait_for_timeout(self.config.post_command_padding_ms)
                                        return True
                                    elif user_choice == 'a':
                                        logger.error("🛑 Human action captured: Ordering immediate shutdown protocols.")
                                        hitl_loop = False # Break out to cascade standard exit failure paths
                                    else:
                                        print("Invalid validation parameter token. Enter exactly 'r', 's', or 'a'.")

                            # Raise fatal termination if unrecovered or human explicitly chose to abort
                            step_results[idx] = False
                            self._update_status_markdown(instructions, idx, step_results)
                            raise RuntimeError(f"Command execution exception at Step [{inst.index}]: {target_cmd}")
                            
                        if not prompt_stabilized:
                            logger.warning(f"Prompt stabilization wait timed out after running Step [{inst.index}]. Advancing safely...")
                            
                        await page.wait_for_timeout(self.config.post_command_padding_ms)
                        return True
                        
                    # Drive sub-command execution block
                    await inject_subcommand_with_recovery(cmd)
                    
                # Save code block hash verification key to persistent state history checkpoint
                self._save_hash_state(inst.block_hash)
                step_results[idx] = True
                self._update_status_markdown(instructions, idx, step_results)
                
            self._update_status_markdown(instructions, len(instructions), step_results)
            logger.info("All scheduled lab instructions completed successfully.")
            return True
            
        except Exception as e:
            logger.error(f"Terminal execution automation stream failed: {e}", exc_info=True)
            return False

    async def run(self, instructions: List[Instruction]) -> bool:
        """Routes execution cleanly based on user-specified operation modes."""
        if self.config.use_cdp:
            return await self._run_cdp_attachment(instructions)
        else:
            return await self._run_native_launcher(instructions)


async def orchestrate(config: ExecutionConfig) -> bool:
    """Coordinates file validation, instruction parsing, JSON plan serialization, and browser execution automation."""
    logger.info(f"Reading raw source document: {config.markdown_path}")
    if not os.path.exists(config.markdown_path):
        logger.error(f"Target lab markdown path does not exist: {config.markdown_path}")
        return False
        
    with open(config.markdown_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    parser = ParsingEngine(config=config)
    instructions = parser.parse(content)
    
    if not instructions:
        logger.warning("No actionable CLI sequences identified after scanning target markdown contents.")
        return False
        
    logger.info(f"Compiled ordered automation runbook containing {len(instructions)} distinct instruction units.")
    
    # Initialize ExecutionEngine establishing dynamic output routing maps inside run-specific folders
    engine = ExecutionEngine(config=config)
    parser.export_json_plan(instructions, engine.json_plan_path)
    
    if config.dry_run:
        logger.info(f"Dry-run validation pass specified. Compiled JSON runbook successfully generated inside run folder: {engine.run_dir}")
        return True
        
    return await engine.run(instructions=instructions)


def main():
    """Parses runtime CLI parameters to drive advanced automated codelab runbooks."""
    parser = argparse.ArgumentParser(description="Automated Cloud Shell Lab Execution Engine (Unified Dual-Mode)")
    parser.add_argument("--lab", required=True, help="Absolute or relative path to target source lab markdown.")
    parser.add_argument("--project", default=None, help="Target pre-provisioned GCP Project ID to configure upon initialization.")
    parser.add_argument("--use-cdp", action="store_true", help="Attach directly to existing open browser session via CDP.")
    parser.add_argument("--cdp-url", default="http://localhost:9222", help="Base debugging server HTTP/WS host URL mapping.")
    parser.add_argument("--chrome-path", default="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", help="Absolute binary path mapping to natively installed desktop Google Chrome.")
    parser.add_argument("--profile", default=os.path.expanduser("~/.config/gcp_automation_profile"), help="Path mapping to local session preservation profile directory.")
    parser.add_argument("--url", default="https://console.cloud.google.com/?cloudshell=true", help="Base landing URL pointing to active GCP terminal.")
    parser.add_argument("--headless", action="store_true", help="Launch browser silently in background (Hides UI from external screen recorders).")
    parser.add_argument("--dry-run", action="store_true", help="Compile JSON execution plan and route subdirectories without launching browser streams.")
    parser.add_argument("--force-reset", action="store_true", help="Ignore historical across-run .state tracking logs and restart execution from Step 1.")
    parser.add_argument("--self-heal", action="store_true", help="Activate integrated inline Gemini reasoning loop to autonomously diagnose and fix terminal error deltas.")
    parser.add_argument("--max-retries", type=int, default=2, help="Maximum automated self-healing recovery attempts per failing instruction sub-command.")
    parser.add_argument("--no-hitl", action="store_false", dest="hitl", help="Disable manual human-in-the-loop terminal triage gates upon unrecovered terminal errors.")
    
    args = parser.parse_args()
    
    try:
        config = ExecutionConfig(
            markdown_path=os.path.abspath(args.lab),
            project_id=args.project,
            use_cdp=args.use_cdp,
            cdp_url=args.cdp_url,
            executable_path=args.chrome_path,
            user_data_dir=os.path.abspath(args.profile),
            gcp_console_url=args.url,
            headless=args.headless,
            dry_run=args.dry_run,
            force_reset=args.force_reset,
            self_heal=args.self_heal,
            max_retries=args.max_retries,
            human_in_the_loop=getattr(args, 'hitl', True)
        )
    except Exception as e:
        logger.error(f"Input validation failure for startup variables:\n{e}")
        sys.exit(1)
        
    success = asyncio.run(orchestrate(config=config))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
