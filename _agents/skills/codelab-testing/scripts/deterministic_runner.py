"""Deterministic command extractor and runner with state management (Hash-based)."""

import argparse
import datetime
import hashlib
import logging
import os
import re
import select
import subprocess
import sys
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def _filter_hermetic_commands(commands: list[str]) -> list[str]:
  """Filters out interactive or continuous loops from extracted commands."""
  clean = []
  for cmd in commands:
    if "while true" in cmd.lower():
      continue
    clean.append(cmd)
  return clean

def extract_bash_commands(markdown_content: str) -> list[str]:
  """Extracts all fenced bash code blocks from markdown content."""
  pattern = re.compile(r"```bash\n(.*?)\n```", re.DOTALL)
  matches = pattern.findall(markdown_content)
  commands = [match.strip() for match in matches]
  return _filter_hermetic_commands(commands)

def get_cmd_hash(cmd: str) -> str:
  """Computes SHA-256 hash of a command string."""
  return hashlib.sha256(cmd.encode("utf-8")).hexdigest()

def get_active_project():
  """Gets the active gcloud project."""
  try:
    result = subprocess.run(["gcloud", "config", "get-value", "project"], capture_output=True, text=True, check=True)
    return result.stdout.strip()
  except Exception:
    return "Unknown"
    
def update_status_file(status_file, project_id, commands, current_idx, step_results):
  """Updates the test_status.md file."""
  with open(status_file, "w") as f:
    f.write(f"# Test Status: Codelab Validation\n\n")
    f.write(f"**Project ID**: `{project_id}`\n\n")
    f.write(f"## Detailed Progress (Step Level)\n\n")
    for idx, cmd in enumerate(commands):
      status_icon = "[ ]"
      if idx < current_idx:
        status_icon = "[x]" if step_results.get(idx, False) else "[!]"
      elif idx == current_idx:
        if step_results.get(idx) is False:
          status_icon = "[!]"
        else:
          status_icon = "[/]"
        
      cmd_preview = cmd.split('\n')[0][:50] + "..." if len(cmd.split('\n')[0]) > 50 else cmd.split('\n')[0]
      f.write(f"- {status_icon} {idx + 1}. `{cmd_preview}`\n")
      
    f.write(f"\n## Progress Details\n")
    f.write(f"- **Last Checked**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    if current_idx < len(commands):
      f.write(f"- **Current Action**: Running step {current_idx + 1}\n")
    else:
      f.write(f"- **Current Action**: Completed\n")

def run_validation_suite(commands: list[str], cwd: str, state_file: str, env_file: str, status_file: str, timeout=300) -> dict:
  """Executes commands one by one, skipping already executed ones based on hash."""
  if not commands:
    return {"success": True, "stdout": "No commands to run.", "stderr": ""}

  executed_hashes = []
  if os.path.exists(state_file):
    with open(state_file, "r") as f:
      executed_hashes = [line.strip() for line in f.readlines()]
    logging.info("[Runner] Found %d previously executed commands.", len(executed_hashes))

  # Start a persistent bash shell
  process = subprocess.Popen(
      ["bash"],
      cwd=cwd,
      stdin=subprocess.PIPE,
      stdout=subprocess.PIPE,
      stderr=subprocess.STDOUT,
      text=True,
  )

  # Function to send command and wait for completion
  def run_cmd(cmd_str, timeout=300):
    assert process.stdin is not None
    assert process.stdout is not None
    
    # We use a unique token to mark the end of a command execution
    token = "___CMD_DONE_TOKEN___"
    full_cmd = f"set -x\n{cmd_str}\nstatus=$?\necho {token} $status\n"
    process.stdin.write(full_cmd)
    process.stdin.flush()

    output = []
    start_time = time.time()
    while True:
      # Use select to wait for output with timeout
      ready, _, _ = select.select([process.stdout], [], [], 1.0)
      if ready:
        line = process.stdout.readline()
        if not line:
          break
        if token in line:
          status = int(line.split()[-1])
          return status, "".join(output)
        print(line, end="", flush=True)
        output.append(line)
        start_time = time.time() # Reset timeout on activity
        
      if time.time() - start_time > timeout:
        logging.error(f"[Runner] Command timed out after {timeout} seconds.")
        return -2, "".join(output)
        
    return -1, "".join(output)

  # Restore environment if resuming
  if executed_hashes and os.path.exists(env_file):
    logging.info("[Runner] Restoring environment...")
    status, _ = run_cmd(f"source {env_file}")
    if status != 0:
      logging.warning("[Runner] Failed to restore environment.")

  project_id = get_active_project()
  step_results = {idx: True for idx in range(len(commands)) if get_cmd_hash(commands[idx]) in executed_hashes}
  
  update_status_file(status_file, project_id, commands, 0, step_results) # Initial status

  for idx, cmd in enumerate(commands):
    cmd_hash = get_cmd_hash(cmd)
    if cmd_hash in executed_hashes:
      logging.info("[Runner] Skipping step %d (already executed)", idx)
      continue

    logging.info("[Runner] Running step %d...", idx)
    update_status_file(status_file, project_id, commands, idx, step_results)
    
    status, _ = run_cmd(cmd, timeout=timeout)

    if status != 0:
      logging.error("[Runner] Step %d failed with status %d", idx, status)
      step_results[idx] = False
      update_status_file(status_file, project_id, commands, idx, step_results)
      return {"success": False, "failed_idx": idx}

    step_results[idx] = True
    # Save state (append hash)
    with open(state_file, "a") as f:
      f.write(cmd_hash + "\n")
    executed_hashes.append(cmd_hash)
    
    # Save environment (only exported variables)
    run_cmd(f"export -p > {env_file}")

  update_status_file(status_file, project_id, commands, len(commands), step_results)

  # We keep the state files to allow incremental additions in future runs.
  # To do a full clean run, delete the .state and .env files manually.

  return {"success": True}

def main():
  parser = argparse.ArgumentParser(description="Deterministic command runner for Codelab testing.")
  parser.add_argument("markdown_file", help="Path to the markdown file containing bash commands.")
  parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds for each command.")
  
  args = parser.parse_args()
  
  md_path = args.markdown_file
  if not os.path.exists(md_path):
    print(f"File not found: {md_path}")
    sys.exit(1)

  with open(md_path, "r") as f:
    content = f.read()

  commands = extract_bash_commands(content)
  print(f"Extracted {len(commands)} bash blocks.")

  cwd = os.getcwd()
  state_file = md_path + ".state"
  env_file = md_path + ".env"
  status_file = os.path.join(os.path.dirname(md_path), "test_status.md")

  result = run_validation_suite(commands, cwd, state_file, env_file, status_file, timeout=args.timeout)

  print("\n--- Validation Summary ---")
  if result.get("success"):
    print("Validation successful!")
    sys.exit(0)
  else:
    print(f"Validation failed at step {result.get('failed_idx')}")
    sys.exit(1)

if __name__ == "__main__":
  main()
