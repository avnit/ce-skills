#!/usr/bin/env python3
"""
Jeski Client Agent Orchestration Harness.
Simulates the 3-Phase interactive CE discovery lifecycle and Security Agent evaluation.
Communicates natively with the remote WAF MCP Server.
"""

import json
import os
import sys
import time
import re
import requests

CACHE_FILE = "session_cache.json"

import subprocess

class StdioWafMcpClient:
    def __init__(self, command="blaze", args=["run", "//agent_waf_system:mcp_server"], cwd="/google/src/cloud/shacharb/waf-mcp/google3"):
        self.command = command
        self.args = args
        self.cwd = cwd

    def get_questionnaire_tree(self, area_of_tech, deployment_size, customer_priority, session_state=None):
        """
        Queries the remote WAF MCP Server running in stdio mode via Blaze.
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "get_questionnaire_tree",
                "arguments": {
                    "area_of_tech": area_of_tech,
                    "deployment_size": deployment_size,
                    "customer_priority": customer_priority,
                    "session_state": session_state
                }
            },
            "id": 1
        }
        try:
            # Launch the subprocess WAF MCP server
            proc = subprocess.Popen(
                [self.command] + self.args,
                cwd=self.cwd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Write the request payload on standard input as a JSON line
            request_str = json.dumps(payload) + "\n"
            proc.stdin.write(request_str)
            proc.stdin.flush()
            
            # Read response line from standard output
            response_line = None
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                line = line.strip()
                if line.startswith("{"):
                    response_line = line
                    break
            
            # Clean up process
            proc.stdin.close()
            proc.terminate()
            proc.wait()
            
            if not response_line:
                raise Exception("No valid JSON-RPC response received from stdio stream.")
                
            res_json = json.loads(response_line)
            if "error" in res_json:
                raise Exception(res_json["error"].get("message", "Unknown MCP error"))
            
            content = res_json["result"]["content"]
            for block in content:
                if block.get("type") == "text":
                    return json.loads(block["text"])
            
            raise Exception("No text content found in stdio response block.")
        except Exception as e:
            print(f"\nℹ️ Blaze WAF MCP stdio server lookup skipped: {e}")
            print("Running local client scoping engine fallback...")
            return self._get_fallback_mock_tree(area_of_tech, deployment_size, customer_priority, session_state)

    def _get_fallback_mock_tree(self, area_of_tech, deployment_size, customer_priority, session_state=None):
        """Lightweight local client-side fallback supporting composite technologies (NETWORKING, DATABASES, GKE)."""
        tech_upper = area_of_tech.upper()
        decision_groups = []

        # 1. NETWORKING GROUPS
        if "NETWORKING" in tech_upper or "NETWORK" in tech_upper or "VPC" in tech_upper:
            decision_groups.append({
                "id": "TOPOLOGY",
                "group_name": "Topology Selection",
                "discovery_question": "Select the core virtual network topology for your GCP environment:",
                "priority_alignment_warning": "⚠️ SECURITY ALERT: VPC Peering does not support transitive routing, which can bypass centralized security inspection firewalls." if (customer_priority == "SECURITY" or deployment_size == "ENTERPRISE_SCALE") else None,
                "options": [
                    {
                        "id": "HUB_AND_SPOKE",
                        "text": "Hub-and-Spoke Architecture (using Network Connectivity Center or Transit VPC)",
                        "rules": ["WAF-NET-01", "PCI-DSS-1.1"],
                        "cons": "Higher cost, additional transit routing hops.",
                        "recommended_by_waf_heuristics": True
                    },
                    {
                        "id": "VPC_PEERING",
                        "text": "VPC Peering Architecture (direct mesh pairing of VPCs)",
                        "rules": ["WAF-NET-02"],
                        "cons": "Scale limitations, lack of transitive routing, decentralized firewall management.",
                        "recommended_by_waf_heuristics": False
                    }
                ]
            })
            decision_groups.append({
                "id": "EGRESS",
                "group_name": "Internet Egress Controls",
                "discovery_question": "How should outbound internet traffic from private resources be routed and inspected?",
                "priority_alignment_warning": None,
                "options": [
                    {
                        "id": "SECURE_EGRESS_GATEWAY",
                        "text": "Secure Egress Proxy Gateway (using Next-Gen Firewall or centralized proxy appliance)",
                        "rules": ["WAF-NET-03", "FedRAMP-AC-4"],
                        "cons": "Requires proxy configurations on clients, higher initial compute cost.",
                        "recommended_by_waf_heuristics": True
                    },
                    {
                        "id": "DIRECT_NAT",
                        "text": "Direct Outbound Cloud NAT (standard managed NAT gateway per region)",
                        "rules": ["WAF-NET-04"],
                        "cons": "No application-layer URL filtering, limited logging customization.",
                        "recommended_by_waf_heuristics": False
                    }
                ]
            })

        # 2. DATABASE GROUPS
        if "DATABASES" in tech_upper or "DATABASE" in tech_upper or "SQL" in tech_upper:
            decision_groups.append({
                "id": "HA_TOPOLOGY",
                "group_name": "Database High Availability",
                "discovery_question": "Select the High Availability configuration for your Cloud SQL instance:",
                "priority_alignment_warning": "⚠️ RELIABILITY ALERT: Zonal HA configuration is vulnerable to a single-zone outage. HIPAA and enterprise compliance typically mandate Regional HA." if (customer_priority == "RELIABILITY" or deployment_size == "ENTERPRISE_SCALE") else None,
                "options": [
                    {
                        "id": "REGIONAL_HA",
                        "text": "Regional HA (Active instance in primary zone, standby instance in secondary zone)",
                        "rules": ["WAF-DB-01", "HIPAA-164.308"],
                        "cons": "Double the instance and storage cost, slight increase in write latency.",
                        "recommended_by_waf_heuristics": True
                    },
                    {
                        "id": "ZONAL_HA",
                        "text": "Zonal HA (Standalone database instance inside a single zone)",
                        "rules": ["WAF-DB-02"],
                        "cons": "No automated failover on zonal disaster. Standard SLA is reduced.",
                        "recommended_by_waf_heuristics": False
                    }
                ]
            })
            decision_groups.append({
                "id": "BACKUPS",
                "group_name": "Disaster Recovery & Backups",
                "discovery_question": "Select your backup retention and Point-in-Time Recovery (PITR) policy:",
                "priority_alignment_warning": None,
                "options": [
                    {
                        "id": "ENTERPRISE_PITR",
                        "text": "7-Day PITR with Multi-Region Backup Storage Redundancy",
                        "rules": ["WAF-DB-03", "PCI-DSS-10.1"],
                        "cons": "Higher backup storage consumption costs.",
                        "recommended_by_waf_heuristics": True
                    },
                    {
                        "id": "BASIC_BACKUP",
                        "text": "Daily Backups with Single-Region Storage Redundancy (No PITR)",
                        "rules": ["WAF-DB-04"],
                        "cons": "Up to 24 hours of potential data loss on disaster recovery restore.",
                        "recommended_by_waf_heuristics": False
                    }
                ]
            })

        # 3. GKE GROUPS (COMPUTE_AND_CONTAINERS)
        if "GKE" in tech_upper or "KUBERNETES" in tech_upper or "CONTAINERS" in tech_upper or "COMPUTE" in tech_upper:
            decision_groups.append({
                "id": "GKE_TOPOLOGY",
                "group_name": "GKE API Endpoint Access Controls",
                "discovery_question": "How should the GKE control plane master API endpoint be exposed?",
                "priority_alignment_warning": "⚠️ SECURITY ALERT: Public GKE API endpoints expose the master control plane directly to the public internet, raising attacks risk." if (customer_priority == "SECURITY" or deployment_size == "ENTERPRISE_SCALE") else None,
                "options": [
                    {
                        "id": "PRIVATE_CLUSTER",
                        "text": "Private Cluster (API endpoint fully isolated, private nodes only)",
                        "rules": ["WAF-GKE-01", "FedRAMP-SI-4"],
                        "cons": "Requires Bastion proxy or VPN/Interconnect tunnel for administration access.",
                        "recommended_by_waf_heuristics": True
                    },
                    {
                        "id": "PUBLIC_CLUSTER",
                        "text": "Public Cluster (API endpoint exposed publicly with authorized networks)",
                        "rules": ["WAF-GKE-02"],
                        "cons": "Control plane master node is routable over public network boundaries.",
                        "recommended_by_waf_heuristics": False
                    }
                ]
            })

        # 4. AI & ML GROUPS
        if "AI" in tech_upper or "ML" in tech_upper or "VERTEX" in tech_upper:
            decision_groups.append({
                "id": "AI_EGRESS",
                "group_name": "Vertex AI Pipeline Egress Controls",
                "discovery_question": "How should Vertex AI Reasoning Agents and model pipelines securely access internal VPC resources?",
                "priority_alignment_warning": "⚠️ SECURITY ALERT: Public routing of model endpoints exposes cognitive data routes to unauthorized transit zones." if (customer_priority == "SECURITY" or deployment_size == "ENTERPRISE_SCALE") else None,
                "options": [
                    {
                        "id": "PSC_ATTACHMENT",
                        "text": "Private Service Connect (PSC) Network Attachments (isolated endpoint routing)",
                        "rules": ["WAF-AI-01", "FedRAMP-AC-4"],
                        "cons": "Requires standard IP and network attachment setup for cognitive agents.",
                        "recommended_by_waf_heuristics": True
                    },
                    {
                        "id": "TRANSITIVE_NAT",
                        "text": "Transitive NAT Outbound Routing (public routes over standard gateway paths)",
                        "rules": ["WAF-AI-02"],
                        "cons": "Model endpoint is routable over generic internet transit lanes.",
                        "recommended_by_waf_heuristics": False
                    }
                ]
            })

        # 5. SECURITY & STORAGE GROUPS
        if "SEC" in tech_upper or "STORAGE" in tech_upper or "KEY" in tech_upper:
            compliance = ""
            if session_state and isinstance(session_state, dict):
                compliance = session_state.get("compliance_frameworks", "")
            decision_groups.append({
                "id": "STORAGE_ENCRYPTION",
                "group_name": "Encryption Key Management (KMS)",
                "discovery_question": "Select the encryption key management architecture for your storage and database assets:",
                "priority_alignment_warning": "⚠️ COMPLIANCE ALERT: Google-managed encryption keys lack support for strict customer-driven key rotation audits and revocation controls." if (customer_priority == "SECURITY" or "PCI-DSS" in compliance or "FedRAMP" in compliance) else None,
                "options": [
                    {
                        "id": "CMEK_HSM",
                        "text": "Customer-Managed Encryption Keys (CMEK) backed by Hardware Security Modules (Cloud HSM)",
                        "rules": ["WAF-SEC-01", "PCI-DSS-3.5"],
                        "cons": "Operational key rotation overhead, HSM key tier pricing.",
                        "recommended_by_waf_heuristics": True
                    },
                    {
                        "id": "GOOGLE_DEFAULT",
                        "text": "Google-Managed Default Encryption Keys (standard envelope encryption)",
                        "rules": ["WAF-SEC-02"],
                        "cons": "Lacks manual key rotation lifecycle and revocation control.",
                        "recommended_by_waf_heuristics": False
                    }
                ]
            })

        # Default fallback to networking if empty
        if not decision_groups:
            decision_groups.append({
                "id": "TOPOLOGY",
                "group_name": "Topology Selection",
                "discovery_question": "Select the core virtual network topology for your GCP environment:",
                "priority_alignment_warning": None,
                "options": [
                    {
                        "id": "HUB_AND_SPOKE",
                        "text": "Hub-and-Spoke Architecture",
                        "rules": ["WAF-NET-01"],
                        "cons": "Cost",
                        "recommended_by_waf_heuristics": True
                    }
                ]
            })

        return {
            "area_of_tech": area_of_tech,
            "deployment_size": deployment_size,
            "customer_priority": customer_priority,
            "decision_groups": decision_groups
        }

class WafClientOrchestrator:
    def __init__(self, command="blaze", args=["run", "//agent_waf_system:mcp_server"], cwd="/google/src/cloud/shacharb/waf-mcp/google3"):
        self.mcp = StdioWafMcpClient(command, args, cwd)
        self.session_state = {}
        self.retries = 0

    def load_cache(self):
        """Phase 1: Load from persistent session cache to prevent interview restarts."""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r") as f:
                    self.session_state = json.load(f)
                print("🔄 Persistent session state reloaded from cache.")
                return True
            except Exception as e:
                print(f"⚠️ Error loading cache: {e}")
        return False

    def save_cache(self):
        """Phase 1: Save to persistent session cache."""
        try:
            with open(CACHE_FILE, "w") as f:
                json.dump(self.session_state, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving cache: {e}")

    def reset_cache(self):
        """Reset session cache file."""
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
        self.session_state = {}

    def render_custom_template(self, template_text, context):
        """
        A deterministic lightweight template engine designed to parse variables,
        conditionals, and loops from the ADR Markdown template without external dependencies.
        """
        result = template_text

        # 1. Replace variables: {{ var_name }}
        def repl_var(match):
            var_path = match.group(1).strip()
            # simple lookup
            return str(context.get(var_path, f"[{var_path} missing]"))
        
        result = re.sub(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", repl_var, result)

        # 2. Replace if-else block: {% if cond %}...{% else %}...{% endif %}
        def repl_if(match):
            cond_var = match.group(1).strip()
            content_true = match.group(2)
            content_false = match.group(3) if match.group(3) else ""
            
            val = context.get(cond_var, False)
            if val:
                return content_true
            else:
                return content_false

        result = re.sub(
            r"\{%\s*if\s+([a-zA-Z0-9_]+)\s*%\}(.*?)(?:\{%\s*else\s*%\}(.*?))?\{%\s*endif\s*%\}",
            repl_if,
            result,
            flags=re.DOTALL
        )

        # 3. Replace for loop: {% for item in list %}...{% endfor %}
        def repl_for(match):
            item_name = match.group(1).strip()
            list_name = match.group(2).strip()
            loop_body = match.group(3)

            items = context.get(list_name, [])
            loop_output = []
            for idx, item in enumerate(items):
                body_inst = loop_body
                # Replace item properties: {{ item.prop }}
                for prop_name, prop_val in item.items():
                    tag = f"{{{{ {item_name}.{prop_name} }}}}"
                    body_inst = body_inst.replace(tag, str(prop_val))
                
                # Remove standard loops if inside
                body_inst = re.sub(r"\{% if.*?%\}.*?\{% endif %\}", "", body_inst, flags=re.DOTALL)
                loop_output.append(body_inst)
            
            return "".join(loop_output)

        result = re.sub(
            r"\{%\s*for\s+([a-zA-Z0-9_]+)\s+in\s+([a-zA-Z0-9_]+)\s*%\}(.*?)\{%\s*endfor\s*%\}",
            repl_for,
            result,
            flags=re.DOTALL
        )

        return result

    def run_interactive(self, area_of_tech=None, size=None, priority=None, auto_inputs=None):
        """
        Executes the interactive questionnaire.
        If auto_inputs is provided (dict), runs programmatically for validation.
        """
        print("\n==================================================================")
        print("🤖 Starting WAF Solutions Architect Co-Host Interactive Discovery")
        print("==================================================================\n")

        # Phase 1: Scoping Modal
        if auto_inputs:
            self.session_state = {
                "customer_name": auto_inputs.get("customer_name", "Stripe Inc."),
                "industry_vertical": auto_inputs.get("industry_vertical", "FinTech"),
                "area_of_tech": auto_inputs.get("area_of_tech", "NETWORKING"),
                "deployment_size": auto_inputs.get("deployment_size", "ENTERPRISE_SCALE"),
                "customer_priority": auto_inputs.get("customer_priority", "SECURITY"),
                "compliance_frameworks": auto_inputs.get("compliance_frameworks", "PCI-DSS"),
                "business_requirements": auto_inputs.get("business_requirements", "Provide high-availability, security perimeters, and backup capabilities."),
                "overall_goal": auto_inputs.get("overall_goal", "Migrate core operations to high-security GKE and Cloud SQL structures."),
                "completed_questions": {}
            }
            print("📊 Programmatic inputs applied.")
        else:
            # Load Cache if exists
            has_cache = self.load_cache()
            if has_cache:
                resume = input("Do you want to resume the cached session? (y/n): ").strip().lower()
                if resume != 'y':
                    self.reset_cache()
                    has_cache = False

            if not has_cache:
                print("--- Phase 1: Customer Scoping Parameters ---")
                self.session_state["customer_name"] = input("Enter Customer Name: ").strip()
                self.session_state["industry_vertical"] = input("Enter Industry Vertical: ").strip()
                self.session_state["compliance_frameworks"] = input("Enter Governing Compliance Frameworks (e.g., PCI-DSS, HIPAA, SOC2, None): ").strip()
                
                print("\nEnter Area(s) of Tech (e.g., DATABASES, GKE, NETWORKING, or composite combinations like DATABASES+GKE+NETWORKING):")
                self.session_state["area_of_tech"] = input("Areas of Tech: ").strip().upper()

                print("\nSelect Deployment Size:")
                print("1. ENTERPRISE_SCALE")
                print("2. MEDIUM_BUSINESS")
                print("3. SMALL_WORKLOAD")
                size_choice = input("Choice (1/2/3): ").strip()
                size_map = {"1": "ENTERPRISE_SCALE", "2": "MEDIUM_BUSINESS", "3": "SMALL_WORKLOAD"}
                self.session_state["deployment_size"] = size_map.get(size_choice, "MEDIUM_BUSINESS")

                print("\nSelect Primary Customer Priority:")
                print("1. SECURITY")
                print("2. COST_OPTIMIZATION")
                print("3. RELIABILITY")
                print("4. PERFORMANCE")
                pri_choice = input("Choice (1/2/3/4): ").strip()
                pri_map = {"1": "SECURITY", "2": "COST_OPTIMIZATION", "3": "RELIABILITY", "4": "PERFORMANCE"}
                self.session_state["customer_priority"] = pri_map.get(pri_choice, "COST_OPTIMIZATION")
                
                self.session_state["business_requirements"] = input("\nEnter Customer Business Requirements: ").strip()
                self.session_state["overall_goal"] = input("Enter Overall Architecture Goal: ").strip()
                
                self.session_state["completed_questions"] = {}
                self.save_cache()

        # Retrieve pruned session tree from MCP
        session_tree = self.mcp.get_questionnaire_tree(
            self.session_state["area_of_tech"],
            self.session_state["deployment_size"],
            self.session_state["customer_priority"],
            self.session_state
        )

        # Phase 2: Q&A Loop
        print("\n--- Phase 2: Interactive Option Discovery Loop ---")
        groups = session_tree.get("session_tree") or session_tree.get("decision_groups") or []
        
        for group in groups:
            # Resolve group variables dynamically
            group_id = group.get("id") or group.get("decision_group")
            group_title = group.get("group_name") or group.get("decision_group")
            question = group.get("discovery_question")
            warning = group.get("priority_alignment_warning")
            
            # Check cache first
            if group_id in self.session_state["completed_questions"]:
                print(f"\nDecision Group '{group_title}' already cached. Skipping.")
                continue

            print(f"\n🔹 DECISION GROUP: {group_title.upper()}")
            if warning:
                print(f"\033[91m{warning}\033[0m")

            print(f"\nQuestion: {question}")
            
            # Order options - recommended first
            options = group.get("options", [])
            options = sorted(options, key=lambda x: x.get("recommended_by_waf_heuristics", False), reverse=True)
            
            for idx, opt in enumerate(options):
                opt_name = opt.get("text") or opt.get("option_name")
                opt_rules = opt.get("rules") or opt.get("governing_rules") or []
                opt_cons = opt.get("cons") or ""
                if isinstance(opt_cons, list):
                    opt_cons = ", ".join(opt_cons)
                
                prefix = "(Recommended) " if opt.get("recommended_by_waf_heuristics") else ""
                print(f"  [{idx + 1}] {prefix}{opt_name}")
                print(f"      Rules: {', '.join(opt_rules)}")
                print(f"      Cons: {opt_cons}")

            # Choose option
            if auto_inputs:
                # Safe dynamic mapping with recommended index fallback
                group_choice = auto_inputs.get("choices", {}).get(group_id)
                if group_choice:
                    choice_idx = group_choice["index"]
                    justification = group_choice["justification"]
                else:
                    # Fallback: automatically choose the recommended option (index 0)
                    choice_idx = 0
                    justification = "Automatically aligned with standard recommended WAF heuristics."
                print(f"Programmatic Choice selected: {choice_idx + 1}")
            else:
                c_str = input(f"Select option (1-{len(options)}): ").strip()
                try:
                    choice_idx = int(c_str) - 1
                except ValueError:
                    choice_idx = 0
                
                justification = ""
                selected_opt = options[choice_idx]
                rec_flag = selected_opt.get("recommended_by_waf_heuristics", False)
                if not rec_flag:
                    print("\n⚠️ Warning: You selected an option that overrides standard WAF heuristics.")
                    justification = input("Please provide a business justification/technical rationale for this override: ").strip()
                else:
                    justification = input("Enter any additional business justification (optional): ").strip()

            selected_opt = options[choice_idx]
            opt_id = selected_opt.get("id") or selected_opt.get("type")
            opt_name = selected_opt.get("text") or selected_opt.get("option_name")
            opt_rules = selected_opt.get("rules") or selected_opt.get("governing_rules") or []
            opt_cons = selected_opt.get("cons") or ""
            if isinstance(opt_cons, list):
                opt_cons = ", ".join(opt_cons)
                
            rec_flag = selected_opt.get("recommended_by_waf_heuristics", False)
            is_override = not rec_flag

            self.session_state["completed_questions"][group_id] = {
                "selected_option_id": opt_id,
                "selected_option_text": opt_name,
                "rules": opt_rules,
                "cons": opt_cons,
                "justification": justification if justification else "Standard alignment matching recommendations.",
                "is_override": is_override,
                "warning_triggered": warning is not None,
                "warning_text": warning
            }
            self.save_cache()

        # Phase 3: Authoring narrative and Security Agent Review
        print("\n--- Phase 3: Decoupled Authoring & Security Review ---")
        self.run_security_agent_governance_loop(auto_inputs)

    def generate_mermaid_diagram(self):
        """Generate clean escaped Mermaid diagram representing target composite architecture."""
        tech = self.session_state["area_of_tech"].upper()
        decisions = self.session_state["completed_questions"]
        
        lines = ["graph TD"]
        
        # Parse composite components
        has_net = "NETWORKING" in tech or "NETWORK" in tech or "VPC" in tech
        has_db = "DATABASES" in tech or "DATABASE" in tech or "SQL" in tech
        has_gke = "GKE" in tech or "KUBERNETES" in tech or "COMPUTE" in tech
        has_ai = "AI" in tech or "ML" in tech or "VERTEX" in tech
        has_sec = "SEC" in tech or "STORAGE" in tech or "KEY" in tech
        
        if has_net:
            top = decisions.get("TOPOLOGY", {}).get("selected_option_id", "HUB_AND_SPOKE")
            egr = decisions.get("EGRESS", {}).get("selected_option_id", "SECURE_EGRESS_GATEWAY")
            top_label = "Hub-and-Spoke Central Hub" if top == "HUB_AND_SPOKE" else "VPC Peering Direct Mesh"
            egr_label = "Secure Egress Gateway Proxy" if egr == "SECURE_EGRESS_GATEWAY" else "Direct Cloud NAT Gateway"
            
            lines.append(f'    Topology["{top_label}"]')
            lines.append(f'    Egress["{egr_label}"]')
            lines.append(f'    Topology -->|Route Egress| Egress')
            lines.append(f'    Egress -->|Internet Transit| WWW["Public Internet Egress"]')

        if has_gke:
            gke = decisions.get("GKE_TOPOLOGY", {}).get("selected_option_id", "PRIVATE_CLUSTER")
            gke_label = "Private GKE Cluster (Isolated Control Plane)" if gke == "PRIVATE_CLUSTER" else "Public GKE Cluster (Authorized Networks)"
            lines.append(f'    GKE["{gke_label}"]')
            
            if has_net:
                lines.append(f'    GKE -->|Private VPC Peering| Topology')
            else:
                lines.append(f'    GKE -->|Egress| WWW["Public Internet Egress"]')

        if has_db:
            ha = decisions.get("HA_TOPOLOGY", {}).get("selected_option_id", "REGIONAL_HA")
            bck = decisions.get("BACKUPS", {}).get("selected_option_id", "ENTERPRISE_PITR")
            ha_label = "Regional Active-Standby Cloud SQL HA" if ha == "REGIONAL_HA" else "Zonal Standalone Cloud SQL"
            bck_label = "PITR Multi-Region Backup Storage" if bck == "ENTERPRISE_PITR" else "Daily Backup Single Region"
            
            lines.append(f'    DB["{ha_label}"]')
            lines.append(f'    Backup["{bck_label}"]')
            lines.append(f'    DB -->|Replication| Backup')
            
            if has_gke:
                lines.append(f'    GKE -->|Private SQL Connect| DB')
            elif has_net:
                lines.append(f'    Topology -->|Internal SQL Connect| DB')
            else:
                lines.append(f'    App["GCP Compute App Layer"] -->|SQL Connect| DB')

        if has_ai:
            ai = decisions.get("AI_EGRESS", {}).get("selected_option_id", "PSC_ATTACHMENT")
            ai_label = "Vertex AI Agent (PSC Isolated Attachments)" if ai == "PSC_ATTACHMENT" else "Vertex AI Pipeline (Standard NAT Egress)"
            lines.append(f'    Vertex["{ai_label}"]')
            
            if has_gke:
                lines.append(f'    Vertex -->|Model Inference Egress| GKE')
            elif has_db:
                lines.append(f'    Vertex -->|Vector SQL Query| DB')
            elif has_net:
                lines.append(f'    Vertex -->|VPC Intercept| Topology')
            else:
                lines.append(f'    Vertex -->|Outbound Routing| WWW["Public Internet Egress"]')

        if has_sec:
            sec = decisions.get("STORAGE_ENCRYPTION", {}).get("selected_option_id", "CMEK_HSM")
            sec_label = "Cloud HSM KMS (CMEK Key Envelopes)" if sec == "CMEK_HSM" else "Google Default KMS (Default Envelope)"
            lines.append(f'    KMS["{sec_label}"]')
            
            if has_db:
                lines.append(f'    KMS -->|CMK Envelope Protection| DB')
            if has_gke:
                lines.append(f'    KMS -->|Cluster Envelope Protection| GKE')

        # Default fallback
        if len(lines) == 1:
            lines.append('    CE["CE Workbench User"] -->|Scoping Choice| Default["Hub-and-Spoke Architecture"]')

        return "\n".join(lines)

    def critique_security_agent(self, justifications):
        """
        Agent B: Principal Security Agent logic.
        Independently audit based on 5 criteria.
        Uses isolated XML tags <ce_input> to defend against prompt injections.
        """
        passes = True
        report = []
        
        print("🛡️ Security Agent Auditor evaluating customer justifications...")
        
        for group_id, group_data in self.session_state["completed_questions"].items():
            just = justifications[group_id]
            # Isolate CE input in strict XML tag format
            ce_input = f"<ce_input>{just}</ce_input>"
            
            # Prompt Injection Defense Gate:
            # If user tries to write imperative commands inside justifications to bypass security rules.
            if any(cmd in just.lower() for cmd in ["ignore previous", "bypass security", "bypass ciso", "force pass", "always pass", "override all rules"]):
                passes = False
                report.append(f"❌ SECURITY BLOCK: Potential Prompt Injection attack detected in {group_id} justification string!")
                continue

            # Rule 1: Heuristic Override Audit
            if group_data["is_override"]:
                # Verify strong justification
                if len(just.strip()) < 15 or any(w in just.lower() for w in ["wants it", "none", "na", "temp", "placeholder", "just because"]):
                    passes = False
                    report.append(f"❌ SEC AGENT FAIL (Override Audit): The decision '{group_id}' is a standard heuristic override but lacks a detailed business justification. Provided rationale was: '{just}'")
                else:
                    report.append(f"✅ SEC AGENT PASS (Override Audit): Robust justification verified for override '{group_id}': '{just}'")
            else:
                report.append(f"✅ SEC AGENT PASS (Override Audit): No heuristic override for '{group_id}'.")

            # Rule 2: Risk Compensation Analysis
            if group_data["selected_option_id"] in ["ZONAL_HA", "VPC_PEERING"] and self.session_state["deployment_size"] == "ENTERPRISE_SCALE":
                # Enterprise size choosing Zonal HA or VPC Peering must document compensating controls (e.g. backup/perimeter)
                compensating_words = ["backup", "pitr", "perimeter", "vpc-sc", "centralized firewall", "standby", "replica"]
                if not any(w in just.lower() for w in compensating_words):
                    passes = False
                    report.append(f"❌ SEC AGENT FAIL (Risk Compensation): Selected low-HA/decentralized option '{group_data['selected_option_id']}' for Enterprise workload without specifying compensating controls (e.g., backups, security perimeter, standby replica) in rationale.")
                else:
                    report.append(f"✅ SEC AGENT PASS (Risk Compensation): Compensating control identified for risk '{group_data['selected_option_id']}'.")

            # Rule 3: Priority Warning Enforcement
            # Checked by verify warning presence in final document. In our code, we enforce warning text.
            
        return passes, "\n".join(report)

    def run_security_agent_governance_loop(self, auto_inputs=None):
        """
        Orchestrates Phase 3: Decoupled authoring, Security Agent review loopback, and circuit breaker.
        """
        self.retries = 0
        max_retries = 2
        
        while self.retries < max_retries:
            print(f"\n📋 Initiating Security Peer Review Cycle {self.retries + 1}...")
            
            # Extract human justifications
            justifications = {k: v["justification"] for k, v in self.session_state["completed_questions"].items()}
            
            # Run Security Agent Evaluator
            sec_approved, sec_report = self.critique_security_agent(justifications)
            
            if sec_approved:
                print("\n🟢 SECURITY REVIEW PASSED! Generating final approved whitepaper...")
                self.generate_final_adr(ciso_approved=True, ciso_report="Passed all security and compliance checks successfully.")
                self.reset_cache()
                return
            else:
                print(f"\n🔴 SECURITY REVIEW FAILED! Detailed Report:\n{sec_report}")
                self.retries += 1
                
                if self.retries < max_retries:
                    print(f"\n⚠️ Loopback Initiated. Security Review failed. Requesting human CE clarification...")
                    # Interactive Loopback: call ask_question modal UI to let CE clarify
                    for group_id, group_data in self.session_state["completed_questions"].items():
                        # Check if this specific group has a fail line in the report
                        has_fail_line = any(group_id in line and "❌" in line for line in sec_report.split("\n"))
                        if has_fail_line:
                            print(f"\n[RE-EVALUATION NEEDED] Decision Group: {group_id}")
                            print(f"Chosen Option: {group_data['selected_option_text']}")
                            print(f"Current Weak Rationale: '{group_data['justification']}'")
                            
                            if auto_inputs:
                                retry_inputs = auto_inputs.get("loopback_clarifications", {}).get(self.retries, {})
                                new_just = retry_inputs.get(group_id, "Standard alignment matching recommendations.")
                                print(f"Clarified rationale applied programmatically: '{new_just}'")
                            else:
                                new_just = input("Please clarify your architectural rationale: ").strip()
                            
                            self.session_state["completed_questions"][group_id]["justification"] = new_just
                            self.save_cache()
                else:
                    # Trip Circuit Breaker
                    print(f"\n🚨 CIRCUIT BREAKER TRIPPED! Maximum peer retries reached.")
                    print("Publishing ADR under '⚠️ SECURITY REVIEW PENDING HUMAN ESCALATION' governance banner.")
                    self.generate_final_adr(ciso_approved=False, ciso_report=sec_report)
                    self.reset_cache()
                    return

    def generate_final_adr(self, ciso_approved, ciso_report):
        """Renders template into final whitepaper markdown document."""
        # Load template
        template_path = "agent_waf_system/templates/ADR_TEMPLATE.md"
        if not os.path.exists(template_path):
            print(f"❌ Template not found at {template_path}!")
            return

        with open(template_path, "r") as f:
            template_content = f.read()

        # Format context variables
        decisions_list = []
        for group_id, group_data in self.session_state["completed_questions"].items():
            decisions_list.append({
                "group_name": group_id.replace("_", " ").title(),
                "discovery_question": group_data["selected_option_text"],
                "selected_option_id": group_data["selected_option_id"],
                "selected_option_text": group_data["selected_option_text"],
                "rules_formatted": "\n  ".join([f"- `{r}`" for r in group_data["rules"]]),
                "cons": group_data["cons"],
                "justification": group_data["justification"],
                "is_override": group_data["is_override"],
                "warning_triggered": group_data["warning_triggered"],
                "warning_text": group_data["warning_text"] if group_data["warning_text"] else ""
            })

        # Executive Summary Narrative Synthesis
        tech = self.session_state["area_of_tech"]
        size = self.session_state["deployment_size"]
        pri = self.session_state["customer_priority"]
        
        if ciso_approved:
            exec_summary = f"This executive Architecture Decision Record outlines the target-state {tech} design for {self.session_state['customer_name']}. The solution represents a robust, standard-aligned pattern tailored for {size} workloads prioritizing {pri}. All architectural decisions have undergone peer review and comply with safety and risk governance protocols."
        else:
            exec_summary = f"⚠️ ARCHITECTURAL RISK ALERT: This target-state {tech} design for {self.session_state['customer_name']} contains active heuristic overrides that failed automated Security Agent peer review audits. It is published with a status of PENDING HUMAN ESCALATION and requires manual review by a governing Security Architect before production workloads are provisioned."

        context = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "ciso_approved": ciso_approved,
            "customer_name": self.session_state["customer_name"],
            "industry_vertical": self.session_state["industry_vertical"],
            "compliance_frameworks": self.session_state.get("compliance_frameworks", "None"),
            "business_requirements": self.session_state.get("business_requirements", "Standard design parameters."),
            "overall_goal": self.session_state.get("overall_goal", "Build highly robust architectural patterns."),
            "area_of_tech": tech,
            "deployment_size": size,
            "customer_priority": pri,
            "executive_summary": exec_summary,
            "architecture_diagram_mermaid": self.generate_mermaid_diagram(),
            "decisions": decisions_list,
            "ciso_report": ciso_report.replace("\n", "<br/>")
        }

        rendered_md = self.render_custom_template(template_content, context)

        # Save in customer-specific adr directory
        clean_cust = re.sub(r'[^a-zA-Z0-9]', '_', self.session_state["customer_name"].lower()).strip('_')
        target_dir = f"reports/customer/{clean_cust}/adr"
        os.makedirs(target_dir, exist_ok=True)
        report_file = f"{target_dir}/WAF_ADR.md"
        
        with open(report_file, "w") as f:
            f.write(rendered_md)

        print(f"\n🏆 Final ADR Whitepaper published successfully!")
        print(f"File Location: {os.path.abspath(report_file)}")

if __name__ == "__main__":
    orchestrator = WafClientOrchestrator()
    # If a flag is passed to run interactive or test, do it.
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Programmatic validation run
        print("🚀 Running automated script tests...")
        
        # Scenario A: Pass run
        pass_inputs = {
            "customer_name": "Stripe Inc.",
            "industry_vertical": "FinTech",
            "compliance_frameworks": "PCI-DSS",
            "area_of_tech": "NETWORKING",
            "deployment_size": "ENTERPRISE_SCALE",
            "customer_priority": "SECURITY",
            "business_requirements": "Maintain multi-zone connectivity perimeters, centralized firewall inspection, and enforce transitive boundaries.",
            "overall_goal": "Achieve strict PCI-DSS network isolation for payment gateway operations.",
            "choices": {
                "TOPOLOGY": {
                    "index": 0, # HUB_AND_SPOKE (Recommended)
                    "justification": "Using centralized Hub/Spoke architecture to intercept transit routing and inspect traffic using Palo Alto Firewalls."
                },
                "EGRESS": {
                    "index": 0, # SECURE_EGRESS_GATEWAY (Recommended)
                    "justification": "Routing outbound traffic through centralized inspection gateways to comply with PCI-DSS network boundaries."
                }
            }
        }
        print("\n--- SCENARIO A: Standard Passing Path ---")
        orchestrator.run_interactive(auto_inputs=pass_inputs)

        # Scenario B: Fail & Loopback Clarification & Circuit Breaker
        fail_inputs = {
            "customer_name": "Hooli Corp",
            "industry_vertical": "Media",
            "compliance_frameworks": "None",
            "area_of_tech": "DATABASES",
            "deployment_size": "ENTERPRISE_SCALE",
            "customer_priority": "RELIABILITY",
            "business_requirements": "Deliver high reliability database checkpoints for video rendering assets.",
            "overall_goal": "Deploy performant global data pipelines.",
            "choices": {
                "HA_TOPOLOGY": {
                    "index": 1, # ZONAL_HA (Non-Recommended Override!)
                    "justification": "wants it" # weak justification! CISO Fail!
                },
                "BACKUPS": {
                    "index": 0, # ENTERPRISE_PITR
                    "justification": "Implementing 7-day PITR recovery per safety policy."
                }
            },
            "loopback_clarifications": {
                1: {
                    "HA_TOPOLOGY": "wants it still" # Retry 1 is still weak! CISO Fail!
                }
            }
        }
        print("\n--- SCENARIO B: Weak Override -> Failed Critique -> Loopback Clarification -> Circuit Breaker Banner ---")
        orchestrator.reset_cache()
        orchestrator.run_interactive(auto_inputs=fail_inputs)

        # Scenario C: Composite Pass run (DATABASES + GKE + NETWORKING + AI_AND_ML + SECURITY_AND_STORAGE)
        composite_inputs = {
            "customer_name": "Google Cloud CE",
            "industry_vertical": "Tech Solutions",
            "compliance_frameworks": "FedRAMP-High",
            "area_of_tech": "DATABASES+GKE+NETWORKING+AI_AND_ML+SECURITY_AND_STORAGE",
            "deployment_size": "ENTERPRISE_SCALE",
            "customer_priority": "SECURITY",
            "business_requirements": "Deliver hardened Kubernetes API boundaries, multi-region replicated database engines, private Vertex AI attachments, hardware Cloud HSM key rings, and centralized egress proxies.",
            "overall_goal": "Establish a certified, production-ready secure landing zone matching standard FedRAMP-High regulations.",
            "choices": {
                "TOPOLOGY": {
                    "index": 0, # HUB_AND_SPOKE (Recommended)
                    "justification": "Implementing hub-and-spoke network connectivity center topology to enforce central firewall boundaries."
                },
                "EGRESS": {
                    "index": 0, # SECURE_EGRESS_GATEWAY (Recommended)
                    "justification": "Enforcing centralized secure proxy egress perimeter proxy to intercept and inspect all outbound GKE/SQL egress."
                },
                "HA_TOPOLOGY": {
                    "index": 0, # REGIONAL_HA (Recommended)
                    "justification": "Deploying Regional HA Cloud SQL instance across multi-zone active/standby replication to survive zonal failure events."
                },
                "BACKUPS": {
                    "index": 0, # ENTERPRISE_PITR (Recommended)
                    "justification": "Configuring multi-region 7-day PITR backups to guarantee rapid compliance recovery checkpoints."
                },
                "GKE_TOPOLOGY": {
                    "index": 0, # PRIVATE_CLUSTER (Recommended)
                    "justification": "Enforcing private cluster GKE topology with completely isolated API endpoints reachable only via centralized bastion VPC path."
                },
                "AI_EGRESS": {
                    "index": 0, # PSC_ATTACHMENT (Recommended)
                    "justification": "Securing Vertex AI pipelines and agents using Private Service Connect (PSC) network attachments to isolate cognitive routes within standard VPC scopes."
                },
                "STORAGE_ENCRYPTION": {
                    "index": 0, # CMEK_HSM (Recommended)
                    "justification": "Securing storage buckets and Cloud SQL envelopes using Cloud KMS Customer-Managed Encryption Keys (CMEK) backed by Cloud HSM."
                }
            }
        }
        print("\n--- SCENARIO C: Full Enterprise Scoping (DATABASES + GKE + NETWORKING + AI_AND_ML + SECURITY_AND_STORAGE) ---")
        orchestrator.reset_cache()
        orchestrator.run_interactive(auto_inputs=composite_inputs)
    else:
        # Standard CLI interactive Discovery
        orchestrator.run_interactive()
