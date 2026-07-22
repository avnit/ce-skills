"""Reusable Python subprocess wrapper to invoke csa_cli.par natively on Cloudtop."""

import os
import subprocess
import sys


def query_workspace_context(prompt, corpora="GMAIL,DRIVE,CALENDAR,CHAT", latency_budget=45):
  """Executes csa_cli.par via subprocess and returns the parsed semantic search output."""
  csa_bin = os.environ.get("CSA_CLI", "/google/bin/releases/csa-cli/csa_cli.par")
  
  # Check if binary is available
  if not os.path.exists(csa_bin):
    print(f"❌ Error: Context Service CLI not found at [{csa_bin}]", file=sys.stderr)
    return None
    
  cmd = [
      csa_bin,
      f"--user_prompt={prompt}",
      f"--allowed_corpora={corpora}",
      f"--latency_budget_seconds={latency_budget}",
      "--max_output_tokens=20000"
  ]
  
  print(f"⚡ Routing GMR query natively via: {csa_bin}")
  try:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        check=True
    )
    return result.stdout.strip()
    
  except subprocess.CalledProcessError as e:
    print(f"❌ csa_cli.par execution failed with exit code {e.returncode}", file=sys.stderr)
    print(e.stderr or e.stdout, file=sys.stderr)
    if "loas" in (e.stderr + e.stdout).lower() or "cert" in (e.stderr + e.stdout).lower():
      print("\n💡 Tip: Your active LOAS / gcert session might have expired. Run `gcert` in your shell first.", file=sys.stderr)
    return None
  except Exception as e:
    print(f"❌ Unexpected exception: {e}", file=sys.stderr)
    return None
