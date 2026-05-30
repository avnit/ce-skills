#!/usr/bin/env python3
"""Central Orchestrator Event Loop for Multi-Subagent Codelab Validation & Self-Healing."""

import argparse
import datetime
import json
import logging
import os
import re
import subprocess
import sys
import time
# Find the repository root based on the location of orchestrator.py
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.append(os.path.join(REPO_ROOT, ".agents/scripts"))
try:
    from mailbox_handler import MailboxBroker
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s INFO: [Orchestrator] %(message)s")

class Orchestrator:
    def __init__(self, markdown_file, artifact_dir=None, skip_cleanup=False):
        self.markdown_file = os.path.abspath(markdown_file)
        self.lab_name = os.path.basename(os.path.dirname(self.markdown_file))
        self.lab_dir = os.path.dirname(self.markdown_file)
        
        # Retrieve or generate conversation-id artifact folder
        if artifact_dir:
            self.artifact_dir = os.path.abspath(artifact_dir)
        else:
            self.artifact_dir = os.path.join(
                os.path.expanduser("~/.gemini/jetski/brain"),
                f"orch-{int(time.time())}"
            )
        os.makedirs(self.artifact_dir, exist_ok=True)
        
        self.skip_cleanup = skip_cleanup
        self.project_id = None
        
        # Path configuration
        self.mailbox_dir = os.path.join(REPO_ROOT, ".agents/mailboxes")
        self.progress_file = os.path.join(self.lab_dir, ".tester_state", "progress.json")
        self.bugs_dir = os.path.join(self.lab_dir, "bugs")
        os.makedirs(self.bugs_dir, exist_ok=True)

    def run_command(self, cmd, cwd=None, capture=True):
        """Executes a system shell command synchronously."""
        logging.info(f"Executing: {cmd}")
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                capture_output=capture,
                text=True,
                check=True,
                encoding="utf-8"
            )
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            logging.error(f"Command failed: {cmd}\nExit code: {e.returncode}\nStderr: {e.stderr}")
            return False, e.stdout, e.stderr

    def phase_0_verify_auth(self):
        """Phase 0: Verify Sandbox Admin active authentication context."""
        logging.info("Starting Phase 0: Pre-Flight Auth Check...")
        verify_script = os.path.join(REPO_ROOT, ".agents/skills/gcloud-auth-verification/scripts/verify_auth.py")
        
        success, stdout, _ = self.run_command(f"python3 {verify_script}")
        if not success:
            logging.error("Auth check script failed.")
            return False
            
        try:
            auth_info = json.loads(stdout)
            active_account = auth_info.get("active_account", "")
            logging.info(f"Currently active gcloud identity: {active_account}")
            
            if "admin" not in active_account:
                logging.warning("Active account does not template to Sandbox Admin (admin@...). Permissions block may occur.")
            return True
        except json.JSONDecodeError:
            logging.error("Failed to parse verify_auth.py JSON output.")
            return False

    def phase_1_preflight_lint(self):
        """Phase 1: Statically parse and audit gcloud commands and formatting layout."""
        logging.info("Starting Phase 1: Pre-Flight Static & Formatting Audit...")
        
        if not os.path.exists(self.markdown_file):
            logging.error(f"Codelab markdown file not found at: {self.markdown_file}")
            return False

        # Ingest pre-generated Codelab Reviewer subagent style audit report
        logging.info("Reading pre-generated Subagent Codelab Style Audit Report...")
        
        report_file = os.path.join(self.lab_dir, "style_audit_report.json")
        
        if not os.path.exists(report_file):
            logging.error(f"LINT ERROR: Style audit report not found at {report_file}!")
            logging.error("Please ensure the 'codelab-reviewer' subagent has executed first.")
            return False

        try:
            with open(report_file, "r", encoding="utf-8") as rf:
                report_data = json.load(rf)
        except Exception as e:
            logging.error(f"Failed to read subagent style audit report: {e}")
            return False

        status = report_data.get("audit_status", "NEEDS_REVISION")
        scorecard = report_data.get("scorecard", {})
        remediations = report_data.get("critical_remediations", [])

        logging.info(f"Subagent Style Audit Verdict: {status} | Scores: {scorecard}")

        if status == "NEEDS_REVISION":
            logging.error("LINT ERROR: Codelab Markdown Formatting standards violated!")
            for rem in remediations:
                step = rem.get("step_number", "N/A")
                issue = rem.get("issue_type", "N/A")
                desc = rem.get("description", "N/A")
                rec = rem.get("recommendation", "N/A")
                logging.error(f"Formatting Check Failure (Step {step} - {issue}): {desc}")
                logging.error(f"  Suggested Recommendation: {rec}")
            return False

        logging.info("Dynamic Markdown Formatting Audit passed successfully.")
            
        with open(self.markdown_file, "r") as f:
            content = f.read()
            
        # Extract bash blocks
        bash_blocks = re.findall(r"```bash\n(.*?)\n```", content, re.DOTALL)
        commands = []
        for block in bash_blocks:
            current_cmd = ""
            for line in block.split("\n"):
                line_s = line.strip()
                if not line_s or line_s.startswith("#"):
                    continue
                if line_s.endswith("\\"):
                    current_cmd += " " + line_s[:-1].strip()
                else:
                    current_cmd += " " + line_s
                    commands.append(current_cmd.strip())
                    current_cmd = ""
            if current_cmd.strip():
                commands.append(current_cmd.strip())
            
        logging.info(f"Extracted {len(commands)} commands for static linting.")
        
        # 1. Build Directed Allocation Ledger for Resource Leak Detection (Pillar 4)
        allocated_resources = set()
        deallocated_resources = set()

        for cmd in commands:
            # Normalize spacing
            cmd_norm = " ".join(cmd.split())
            
            # Match Compute creation command: e.g., gcloud compute networks create glb-network
            create_match = re.search(
                r"gcloud\s+compute\s+([a-z-]+)\s+create\s+([^-\s]\S*)", 
                cmd_norm
            )
            if create_match:
                res_type = create_match.group(1)
                res_name = create_match.group(2)
                # Normalize names and ignore variables
                if not res_name.startswith(("<", "$")):
                    allocated_resources.add((res_type, res_name))
                    logging.info(f"Ledger: Staged allocation for GCE resource: compute {res_type} '{res_name}'")

            # Match Compute delete command: e.g., gcloud compute networks delete glb-network
            delete_match = re.search(
                r"gcloud\s+compute\s+([a-z-]+)\s+delete\s+([^-\s][\S\s]*?)(?:\s+--|$)", 
                cmd_norm
            )
            if delete_match:
                res_type = delete_match.group(1)
                raw_names = delete_match.group(2)
                # Split by whitespace to handle space-separated lists of multiple deleted resources
                for name in raw_names.split():
                    name_s = name.strip()
                    if name_s and not name_s.startswith("-"):
                        deallocated_resources.add((res_type, name_s))
                        logging.info(f"Ledger: Staged deallocation for GCE resource: compute {res_type} '{name_s}'")

        # Reconcile allocation ledger leaks
        leaks = allocated_resources - deallocated_resources
        if leaks:
            logging.error("================ RESOURCE LEAK AUDIT FAILURE ================")
            for leak_type, leak_name in leaks:
                logging.error(f"LINT ERROR: Resource Leak! '{leak_type}' named '{leak_name}' is created but never explicitly deleted in the Cleanup step.")
            logging.error("Codelab rejected. You must explicitly delete all allocated resources to prevent continuous billing.")
            logging.error("=============================================================")
            return False

        # 2. Audit for Raw Asynchronous Edge Queries (Pillar 2)
        for cmd in commands:
            cmd_norm = " ".join(cmd.split())
            if "curl " in cmd_norm or "ping " in cmd_norm:
                # If curl is present, verify if the same command block includes a retry loop
                if not ("for " in cmd_norm or "while " in cmd_norm or "sleep " in cmd_norm):
                    logging.error("================ DX ENDPOINT PROBING FAILURE ================")
                    logging.error(f"LINT ERROR: Blocking Edge Command! Found raw endpoint query command: '{cmd}'")
                    logging.error("Public endpoints and anycast IPs require up to 5 minutes to warm up and propagate edge proxy configurations.")
                    logging.error("You MUST wrap all public HTTP verification commands in a robust retrying loop (e.g., for i in {1..30}; do sleep 10; done) checking for status 200 OK.")
                    logging.error("=============================================================")
                    return False

        # 3. Perform GCE-specific parameter flag validations
        for cmd in commands:
            if "network-firewall-policies rules create" in cmd and "--layer4-configs" not in cmd:
                logging.error("LINT ERROR: Found 'network-firewall-policies rules create' command missing the mandatory --layer4-configs parameter flag!")
                return False
            if "instance-templates create" in cmd and "--region" not in cmd:
                logging.error("LINT ERROR: Found GCE 'instance-templates create' command missing --region tag, which will trigger API parameter blocks!")
                return False
                
        logging.info("Pre-Flight Static Command & Formatting Audit passed successfully.")
        return True

    def phase_2_provision_sandbox(self):
        """Phase 2: Dynamically create a test project and link billing."""
        logging.info("Starting Phase 2: GCP Sandbox Project Provisioning...")
        provision_script = os.path.join(REPO_ROOT, ".agents/skills/gcp-provisioning/scripts/create_project.py")
        
        success, stdout, _ = self.run_command(f"python3 {provision_script} {self.lab_name}")
        if not success:
            logging.error("GCP project provisioning script failed.")
            return False
            
        # Extract project ID from stdout
        match = re.search(r"SUCCESS: Project (.*?) setup complete", stdout)
        if not match:
            logging.error("Failed to parse generated Project ID from provisioning output.")
            return False
            
        self.project_id = match.group(1).strip()
        logging.info(f"Successfully provisioned sandbox Project ID: {self.project_id}")
        
        # Set CLOUDSDK_CORE_PROJECT in the environment to isolate gcloud commands from global configuration collisions
        os.environ["CLOUDSDK_CORE_PROJECT"] = self.project_id
        
        # Disable org policies
        logging.info("Disabling organization policy constraints...")
        policy_script = os.path.join(REPO_ROOT, ".agents/skills/gcp-provisioning/scripts/disable_org_policies.sh")
        success, _, _ = self.run_command(f"bash {policy_script} {self.project_id}")
        if not success:
            logging.error("Failed to override organization policies.")
            return False
            
        # Set active project
        success, _, _ = self.run_command(f"gcloud config set project {self.project_id}")
        if not success:
            logging.error("Failed to configure active gcloud project context.")
            return False
            
        return True

    def phase_3_execute_validation(self):
        """Phase 3: Asynchronously run stateful E2E testing and poll Orchestrator mailbox reactively."""
        logging.info("Starting Phase 3: Reactive Stateful E2E Validation...")
        tester_script = os.path.join(REPO_ROOT, ".agents/skills/codelab-validation/scripts/tester.py")
        
        # Construct validation execution command
        cmd = f"python3 {tester_script} {self.markdown_file} --artifact-dir {self.artifact_dir}"
        if self.skip_cleanup:
            cmd += " --skip-cleanup"
            
        # Launch validation as background subprocess
        logging.info("Invoking stateful tester engine in background...")
        proc = subprocess.Popen(
            cmd,
            shell=True,
            cwd=REPO_ROOT
        )
        
        broker = MailboxBroker()
        
        # Active reactive event polling loop
        while True:
            time.sleep(5)
            
            # Poll Orchestrator Inbox for reactive subagent messages
            messages = broker.poll_inbox("orchestrator")
            for filename, file_path, envelope in messages:
                action_type = envelope.get("action_type")
                sender = envelope.get("sender")
                message_id = envelope.get("message_id")
                pointers = envelope.get("blackboard_pointers", {})
                payload = envelope.get("payload", {})
                
                logging.info(f"Received message '{message_id}' from '{sender}' | Action: {action_type}")
                
                if action_type == "REMEDIATE" or payload.get("status") == "FAILED":
                    bug_id = payload.get("bug_id")
                    bug_report = pointers.get("bug_report")
                    findings = payload.get("findings_summary", "No findings summary provided.")
                    
                    logging.error(f"Validation failure envelope detected: {bug_id}")
                    logging.error(f"Subagent findings: {findings}")
                    
                    # Resolve absolute path of the bug pointer
                    if bug_report and os.path.exists(bug_report):
                        logging.info(f"Loading decentralized Bug File from: {bug_report}")
                        try:
                            with open(bug_report, "r", encoding="utf-8") as bf:
                                bug_details = json.load(bf)
                            failed_command = bug_details.get("error_logs", {}).get("failed_command", "N/A")
                            stderr_output = bug_details.get("error_logs", {}).get("stderr_output", "N/A")
                            
                            # Perform self-healing or diagnose
                            self.execute_self_healing_on_bug(bug_id, failed_command, stderr_output, bug_report)
                        except Exception as e:
                            logging.error(f"Failed to read subagent bug details: {e}")
                    
                    # POSIX Atomic Archive to outbox
                    broker.archive_to_outbox("orchestrator", filename)
                    
                    # Terminate subagent process if running
                    if proc.poll() is None:
                        proc.terminate()
                    return False
                
                # Archive processed message to outbox
                broker.archive_to_outbox("orchestrator", filename)
            
            # Check if process exited
            exit_code = proc.poll()
            if exit_code is not None:
                if exit_code == 0:
                    logging.info("E2E validation completed successfully! Verdict: SUCCESS")
                    return True
                else:
                    logging.error(f"Validation script exited with non-zero return code: {exit_code}")
                    # Check if there's a leftover message in the inbox we missed in this tick
                    leftover_messages = broker.poll_inbox("orchestrator")
                    if leftover_messages:
                        continue
                    return False

    def execute_self_healing_on_bug(self, bug_id, failed_command, stderr_output, bug_path):
        """Executes syntax diagnostic self-healing on target bug files."""
        logging.info(f"Self-Healing Engine triggered for Bug ID: {bug_id}")
        
        # Check if this is the classic Network Firewall policy error (missing --layer4-configs)
        if "network-firewall-policies rules create" in failed_command and "Must be specified" in stderr_output and "--layer4-configs" not in failed_command:
            logging.info("Identified syntax gotcha: Missing --layer4-configs on firewall rules create!")
            
            try:
                with open(bug_path, "r") as bf:
                    bug_data = json.load(bf)
                
                bug_data["status"] = "HEALED"
                bug_data["remediation"] = {
                    "suggested_command": failed_command + " --layer4-configs=tcp:80,tcp:443,icmp",
                    "explanation": "Added missing mandatory --layer4-configs flag for global network firewall ingress rule."
                }
                
                with open(bug_path, "w") as bf:
                    json.dump(bug_data, bf, indent=2)
                
                logging.info(f"Bug file updated to HEALED status with remediation payload: {bug_path}")

                # Perform active in-place source markdown file patching to prevent infinite loops
                suggested_command = bug_data["remediation"]["suggested_command"]
                if os.path.exists(self.markdown_file):
                    logging.info(f"Applying active in-place patch to source Markdown: {self.markdown_file}")
                    with open(self.markdown_file, "r", encoding="utf-8") as mf:
                        md_content = mf.read()
                    
                    # Exact string replacement of the failed command with the healed command
                    patched_md = md_content.replace(failed_command, suggested_command)
                    
                    with open(self.markdown_file, "w", encoding="utf-8") as mf:
                        mf.write(patched_md)
                    logging.info("Source Codelab Markdown patched successfully!")
                else:
                    logging.error(f"Markdown source file does not exist at path: {self.markdown_file}")

                # Perform active in-place patch to cached step JSON file if it exists to prevent stale cache replay
                failed_step = bug_data.get("step_number")
                if failed_step:
                    step_file = os.path.join(self.lab_dir, ".tester_state", f"step-{failed_step:03d}.json")
                    if os.path.exists(step_file):
                        logging.info(f"Applying active in-place patch to cached step JSON file: {step_file}")
                        try:
                            with open(step_file, "r", encoding="utf-8") as sf:
                                step_data = json.load(sf)
                            
                            cmd_list = step_data.get("commands", [])
                            for c_idx, cmd in enumerate(cmd_list):
                                if cmd.strip() == failed_command.strip():
                                    cmd_list[c_idx] = suggested_command
                                    break
                            
                            step_data["commands"] = cmd_list
                            
                            with open(step_file, "w", encoding="utf-8") as sf:
                                json.dump(step_data, sf, indent=2)
                            logging.info("Cached step JSON file patched successfully!")
                        except Exception as e:
                            logging.error(f"Failed to patch cached step JSON file: {e}")

            except Exception as e:
                logging.error(f"Failed to update bug file state or patch source markdown: {e}")
        else:
            logging.warning("Bug matches no predefined syntax remediation signatures. Manual review recommended.")

    def execute_pipeline(self):
        """Orchestrates the full E2E verification loop."""
        if not self.phase_0_verify_auth():
            return False
        if not self.phase_1_preflight_lint():
            return False
        if not self.phase_2_provision_sandbox():
            return False
        if not self.phase_3_execute_validation():
            # Self-healing was triggered. Let user choose to re-engage
            return False
        return True

def main():
    parser = argparse.ArgumentParser(description="Master Orchestrator Runner Script.")
    parser.add_argument("markdown_file", nargs="?", default=None, help="Path to the target codelab .lab.md file.")
    parser.add_argument("--artifact-dir", help="Optional custom artifact folder.")
    parser.add_argument("--skip-cleanup", action="store_true", help="Retain GCP test resources.")
    parser.add_argument("--generate-only", action="store_true", help="Generate the lab artifacts to the target directory.")
    parser.add_argument("--target-base-path", default=REPO_ROOT, help="Base directory for file generation.")
    
    args = parser.parse_args()
    
    if args.generate_only:
        import os
        target_dir = os.path.join(args.target_base_path, "labs/dev/multi-region-glb-mig")
        os.makedirs(target_dir, exist_ok=True)
        logging.info(f"Generating premium E2E Codelab artifacts under: {target_dir}")
        
        # 1. Write OWNERS
        with open(os.path.join(target_dir, "OWNERS"), "w") as f:
            f.write("approvers:\n  - shacharb\n")
            
        # 2. Write implementation_plan.md
        implementation_plan = """# Implementation Plan: Multi-Region Global External Application Load Balancer with VM MIG Backends

## 1. Objective & Scope
This Codelab guides Enterprise Cloud Architects (Practice CE Level 300/400) through setting up a highly available, low-latency Global External Application Load Balancer (ALB) spanning two GCP regions (`us-central1` and `europe-west1`). The backends are powered by Managed Instance Groups (MIGs) running web servers.

## 2. Architecture Design
```mermaid
graph TD
    Client["Client Traffic (Anycast IP)"] --> GLB["Global External Application Load Balancer"]
    GLB --> URLMap["URL Map (Routing rules)"]
    URLMap --> TargetProxy["Target HTTP Proxy"]
    TargetProxy --> BackendService["Global Backend Service"]
    
    subgraph Region_US [us-central1 Region]
        BackendService --> MIG_US["MIG US (us-central1-a)"]
        MIG_US --> VM_US["Web Server VMs (us-central1)"]
    end
    
    subgraph Region_EU [europe-west1 Region]
        BackendService --> MIG_EU["MIG EU (europe-west1-b)"]
        MIG_EU --> VM_EU["Web Server VMs (europe-west1)"]
    end
```

## 3. Step-by-Step Deployment Flow
- **Step 1**: Set up the custom VPC network and subnets.
- **Step 2**: Create firewall rules for load balancer health checks.
- **Step 3**: Create instance templates and regional MIGs.
- **Step 4**: Provision backend services, health checks, and load balancer.
- **Step 5**: Verify routing and traffic distribution.
- **Step 6**: Clean up resources.
"""
        with open(os.path.join(target_dir, "implementation_plan.md"), "w") as f:
            f.write(implementation_plan)
            
        # 3. Write blueprint.md
        blueprint = """# Technical Blueprint: Multi-Region Global External Application Load Balancer

This blueprint describes the technical design and configurations for setting up a Global External Application Load Balancer with MIG backends in two regions.

## 1. Network Topology
- VPC Network: `glb-network`
- Subnet US: `us-subnet` (`10.10.10.0/24` in `us-central1`)
- Subnet EU: `eu-subnet` (`10.20.10.0/24` in `europe-west1`)

## 2. Firewall Policy
- Allow HTTP health checks from ranges `35.191.0.0/16` and `130.211.0.0/22` to instances tagged with `http-server`.
- Allow SSH from standard IAP range `35.235.240.0/20`.

## 3. Compute Backends
- GCE Instance Template US & EU:
  - Machine Type: `e2-micro`
  - Tags: `http-server`
  - Startup Script: Installs Apache/Nginx and writes a custom response showing hostname and region.
- Regional MIG US:
  - Region: `us-central1`
  - Target Size: 2
- Regional MIG EU:
  - Region: `europe-west1`
  - Target Size: 2

## 4. Load Balancing Stack
- External IP: `glb-ip-address` (Global Static)
- Backend Service: `glb-backend-service` (Global HTTP, Protocol: HTTP, Port: 80, Balancer Mode: UTILIZATION)
- Health Check: `glb-health-check` (HTTP port 80)
- URL Map: `glb-url-map`
- Target HTTP Proxy: `glb-target-proxy`
- Forwarding Rule: `glb-forwarding-rule` (Global, Port 80)
"""
        with open(os.path.join(target_dir, "blueprint.md"), "w") as f:
            f.write(blueprint)
            
        # 4. Write multi-region-glb-mig.lab.md (Narrative)
        narrative = """---
description: Deploy a Global External Application Load Balancer spanning two GCP regions with GCE MIG backends.
id: multi-region-glb-mig
keywords: docType:Codelab, global load balancer, multi-region, mig, gce
authors: shacharb
layout: scrolling
---

# Deploy a Global External Application Load Balancer with MIG Backends in Two Regions

## 1. Introduction
Duration: 05:00

In this codelab, you will deploy a highly available Global External Application Load Balancer (ALB) spanning two different Google Cloud regions: `us-central1` and `europe-west1`. 

The load balancer acts as an Anycast single IP frontend that dynamically routes user traffic to the closest backend instance group based on latency and load.

### Architecture Diagram
```mermaid
graph TD
    Client["Client Traffic (Anycast IP)"] --> GLB["Global External Application Load Balancer"]
    GLB --> URLMap["URL Map (Routing rules)"]
    URLMap --> TargetProxy["Target HTTP Proxy"]
    TargetProxy --> BackendService["Global Backend Service"]
    
    subgraph Region_US [us-central1 Region]
        BackendService --> MIG_US["MIG US (us-central1-a)"]
        MIG_US --> VM_US["Web Server VMs (us-central1)"]
    end
    
    subgraph Region_EU [europe-west1 Region]
        BackendService --> MIG_EU["MIG EU (europe-west1-b)"]
        MIG_EU --> VM_EU["Web Server VMs (europe-west1)"]
    end
```

### What You Will Learn
- How to provision a custom VPC network and regional subnets.
- How to design instance templates running web servers and deploy them as Managed Instance Groups (MIGs).
- How to configure the Global Load Balancing stack (Health Checks, Backend Services, URL Maps, Target Proxies, and Forwarding Rules).
- How to verify dynamic geo-routing and failover behaviors.

---

## 2. Setting Up the Custom VPC and Subnets
Duration: 07:00

First, configure the VPC and regional subnets.

### Create custom VPC network
```bash
gcloud compute networks create glb-network --subnet-mode=custom
```

### Create subnet in us-central1
```bash
gcloud compute networks subnets create us-subnet \\
    --network=glb-network \\
    --region=us-central1 \\
    --range=10.10.10.0/24
```

### Create subnet in europe-west1
```bash
gcloud compute networks subnets create eu-subnet \\
    --network=glb-network \\
    --region=europe-west1 \\
    --range=10.20.10.0/24
```

> aside positive
> Using custom subnet mode is highly recommended for production environments to prevent IP address conflicts and maintain complete firewall isolation.

---

## 3. Configuring Firewall Rules
Duration: 05:00

Configure firewall rules to allow health check traffic and administrative SSH access via IAP.

### Allow Load Balancer Health Checks
Google Cloud External Application Load Balancers connect to backends from specific health check IP blocks (`130.211.0.0/22` and `35.191.0.0/16`).
```bash
gcloud compute firewall-rules create allow-health-check \\
    --network=glb-network \\
    --action=allow \\
    --direction=ingress \\
    --source-ranges=130.211.0.0/22,35.191.0.0/16 \\
    --target-tags=http-server \\
    --rules=tcp:80
```

### Allow SSH via Identity-Aware Proxy (IAP)
```bash
gcloud compute firewall-rules create allow-ssh \\
    --network=glb-network \\
    --action=allow \\
    --direction=ingress \\
    --source-ranges=35.235.240.0/20 \\
    --target-tags=http-server \\
    --rules=tcp:22
```

---

## 4. Provisioning GCE Managed Instance Groups
Duration: 10:00

Create an instance template and deploy two regional Managed Instance Groups.

### Create the regional instance templates
To maintain strict regional isolation, create regional instance templates in each target region:

#### Create US Regional Template
```bash
gcloud compute instance-templates create glb-template-us \\
    --network=glb-network \\
    --subnet=us-subnet \\
    --tags=http-server \\
    --image-family=debian-11 \\
    --image-project=debian-cloud \\
    --machine-type=e2-micro \\
    --region=us-central1 \\
    --metadata=startup-script="apt-get update && apt-get install -y apache2 && systemctl start apache2 && echo 'Hello from the US-CENTRAL backend!' > /var/www/html/index.html"
```

#### Create EU Regional Template
```bash
gcloud compute instance-templates create glb-template-eu \\
    --network=glb-network \\
    --subnet=eu-subnet \\
    --tags=http-server \\
    --image-family=debian-11 \\
    --image-project=debian-cloud \\
    --machine-type=e2-micro \\
    --region=europe-west1 \\
    --metadata=startup-script="apt-get update && apt-get install -y apache2 && systemctl start apache2 && echo 'Hello from the EUROPE-WEST backend!' > /var/www/html/index.html"
```

### Create the US Managed Instance Group (us-central1)
```bash
gcloud compute instance-groups managed create mig-us \\
    --template=glb-template-us \\
    --size=2 \\
    --region=us-central1
```

### Create the EU Managed Instance Group (europe-west1)
```bash
gcloud compute instance-groups managed create mig-eu \\
    --template=glb-template-eu \\
    --size=2 \\
    --region=europe-west1
```

### Configure MIG Named Ports
Define standard port names so the Load Balancer knows how to route to HTTP service port 80.
```bash
gcloud compute instance-groups managed set-named-ports mig-us --named-ports=http:80 --region=us-central1
```
```bash
gcloud compute instance-groups managed set-named-ports mig-eu --named-ports=http:80 --region=europe-west1
```

---

## 5. Configuring the Load Balancing Stack
Duration: 12:00

Configure the Global Load Balancer.

### Create HTTP Health Check
```bash
gcloud compute health-checks create http glb-health-check --port=80
```

### Create Backend Service
```bash
gcloud compute backend-services create glb-backend-service \\
    --protocol=HTTP \\
    --port-name=http \\
    --health-checks=glb-health-check \\
    --global
```

### Attach MIGs as Backends to the Global Backend Service
```bash
gcloud compute backend-services add-backend glb-backend-service \\
    --instance-group=mig-us \\
    --instance-group-region=us-central1 \\
    --global \\
    --balancing-mode=UTILIZATION \\
    --max-utilization=0.8
```
```bash
gcloud compute backend-services add-backend glb-backend-service \\
    --instance-group=mig-eu \\
    --instance-group-region=europe-west1 \\
    --global \\
    --balancing-mode=UTILIZATION \\
    --max-utilization=0.8
```

### Create URL Map
```bash
gcloud compute url-maps create glb-url-map --default-service=glb-backend-service
```

### Create Target HTTP Proxy
```bash
gcloud compute target-http-proxies create glb-target-proxy --url-map=glb-url-map
```

### Reserve Static Global External IP Address
```bash
gcloud compute addresses create glb-ip-address --global
```

### Create Forwarding Rule
```bash
gcloud compute forwarding-rules create glb-forwarding-rule \\
    --address=glb-ip-address \\
    --global \\
    --target-http-proxy=glb-target-proxy \\
    --ports=80
```

---

## 6. E2E Verification and Geo-Routing Testing
Duration: 05:00

Verify routing and high availability.

### Get your Load Balancer IP
```bash
gcloud compute forwarding-rules describe glb-forwarding-rule --global --format="value(IPAddress)"
```

### Perform curl requests
Run curl multiple times to see a response from the active web servers. Since the load balancer can take 2-4 minutes to warm up, we will use a robust verification loop:
```bash
LB_IP=$(gcloud compute forwarding-rules describe glb-forwarding-rule --global --format="value(IPAddress)")
echo "Waiting for Global Load Balancer anycast IP ($LB_IP) to warm up..."
for i in {1..30}; do
    if curl -m 5 -s -o /dev/null -w "%{http_code}" "http://$LB_IP" | grep -q "200"; then
        echo "Global Load Balancer responded successfully!"
        curl -m 5 "http://$LB_IP"
        break
    fi
    echo "Still warming up, retrying in 10 seconds ($i/30)..."
    sleep 10
done
```

> aside positive
> Requests sent from a VM inside `us-central1` will automatically route to `mig-us`, while requests sent from `europe-west1` will route to `mig-eu` to optimize user latency!

---

## 7. Cleanup
Duration: 05:00

Delete resources to avoid cloud costs.

```bash
gcloud compute forwarding-rules delete glb-forwarding-rule --global --quiet
gcloud compute target-http-proxies delete glb-target-proxy --quiet
gcloud compute url-maps delete glb-url-map --quiet
gcloud compute backend-services delete glb-backend-service --global --quiet
gcloud compute health-checks delete glb-health-check --quiet
gcloud compute instance-groups managed delete mig-us --region=us-central1 --quiet
gcloud compute instance-groups managed delete mig-eu --region=europe-west1 --quiet
gcloud compute instance-templates delete glb-template-us glb-template-eu --quiet
gcloud compute firewall-rules delete allow-health-check allow-ssh --quiet
gcloud compute networks subnets delete us-subnet --region=us-central1 --quiet
gcloud compute networks subnets delete eu-subnet --region=europe-west1 --quiet
gcloud compute networks delete glb-network --quiet
gcloud compute addresses delete glb-ip-address --global --quiet
```

### Congratulations!
You have successfully deployed a Multi-Region Global HTTP Application Load Balancer with GCE MIG backends!
"""
        with open(os.path.join(target_dir, "multi-region-glb-mig.lab.md"), "w") as f:
            f.write(narrative)
            
        logging.info("All artifacts successfully written!")
        sys.exit(0)
        
    if not args.markdown_file:
        logging.error("markdown_file is required when not using --generate-only")
        sys.exit(1)
        
    orchestrator = Orchestrator(args.markdown_file, args.artifact_dir, args.skip_cleanup)
    success = orchestrator.execute_pipeline()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
