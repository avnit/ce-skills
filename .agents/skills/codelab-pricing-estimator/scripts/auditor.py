#!/usr/bin/env python3
"""
Auditor Module for Codelab Pricing Estimator.

Discovers deployed infrastructure via Cloud Asset Inventory and inspects detailed
resource configurations across Compute, GKE, SQL, Networking, Vertex AI, Cloud Run, and Universal assets.
"""

import json
import sys
import billing_client
import cost_engine


def audit_project_resources(project_id):
    """Queries Cloud Asset Inventory and native list APIs to discover active provisioned resources."""
    print(f"🔍 Performing universal billing audit on GCP Project: [{project_id}]...")
    
    asset_cmd = [
        "gcloud", "asset", "search-all-resources",
        f"--scope=projects/{project_id}",
        "--asset-types=compute.googleapis.com/Instance,compute.googleapis.com/Disk,container.googleapis.com/Cluster,sqladmin.googleapis.com/Instance,networkservices.googleapis.com/Gateway,networksecurity.googleapis.com/FirewallEndpoint,compute.googleapis.com/VpnGateway,compute.googleapis.com/Router,compute.googleapis.com/ForwardingRule,aiplatform.googleapis.com/Endpoint,aiplatform.googleapis.com/IndexEndpoint,run.googleapis.com/Service",
        "--format=json"
    ]
    success, stdout, stderr = billing_client.run_command(asset_cmd, timeout=30)
    
    default_asset_types = [
        "compute.googleapis.com/Instance", "compute.googleapis.com/Disk", "container.googleapis.com/Cluster",
        "sqladmin.googleapis.com/Instance", "networkservices.googleapis.com/Gateway", "networksecurity.googleapis.com/FirewallEndpoint",
        "compute.googleapis.com/VpnGateway", "compute.googleapis.com/Router", "compute.googleapis.com/ForwardingRule",
        "aiplatform.googleapis.com/Endpoint", "aiplatform.googleapis.com/IndexEndpoint", "run.googleapis.com/Service"
    ]
    
    if not success or not stdout:
        print(f"⚠️ Cloud Asset Inventory query timed out or unavailable. Falling back to direct native service queries across all supported categories...")
        assets = []
        asset_types = default_asset_types
    else:
        try:
            assets = json.loads(stdout) if stdout else []
            asset_types = [a.get('assetType', '') for a in assets] if assets else default_asset_types
            print(f"📋 Discovered {len(assets)} total resources across {len(set(asset_types))} unique asset types.")
        except Exception as e:
            print(f"⚠️ Error parsing assets JSON: {e}. Falling back to direct native service queries...")
            assets = []
            asset_types = default_asset_types
    
    discovered_resources = []
    handled_resource_names = set()
    total_hourly_cost = 0.0
    
    def add_resource(name, r_type, status, config, location, raw_data):
        nonlocal total_hourly_cost
        handled_resource_names.add(name)
        cost = cost_engine.evaluate_resource_cost(r_type, raw_data, location)
        total_hourly_cost += cost
        discovered_resources.append({
            'name': name,
            'type': r_type,
            'status': status,
            'config': config,
            'location': location,
            'hourly_cost': cost
        })

    # --- 2. Process GCE Instances ---
    if any("compute.googleapis.com/Instance" in t for t in asset_types):
        print("🖥️ Auditing Compute Engine Instances...")
        cmd = ["gcloud", "compute", "instances", "list", f"--project={project_id}", "--format=json"]
        ok, out, _ = billing_client.run_command(cmd)
        if ok and out:
            try:
                for item in json.loads(out):
                    name = item.get('name', 'unnamed-vm')
                    m_url = item.get('machineType', '')
                    machine_type = m_url.split('/')[-1] if m_url else 'e2-medium'
                    z_url = item.get('zone', '')
                    zone = z_url.split('/')[-1] if z_url else 'us-central1-a'
                    status = item.get('status', 'TERMINATED')
                    
                    add_resource(
                        name=name,
                        r_type="Compute Instance",
                        status=status,
                        config=f"Machine: {machine_type}",
                        location=zone,
                        raw_data={"status": status, "machine_type": machine_type}
                    )
            except Exception as e:
                print(f"⚠️ Warning processing compute instances: {e}", file=sys.stderr)

    # --- 3. Process Persistent Disks ---
    if any("compute.googleapis.com/Disk" in t for t in asset_types):
        print("💾 Auditing Persistent Disks...")
        cmd = ["gcloud", "compute", "disks", "list", f"--project={project_id}", "--format=json"]
        ok, out, _ = billing_client.run_command(cmd)
        if ok and out:
            try:
                for item in json.loads(out):
                    name = item.get('name', 'unnamed-disk')
                    size_gb = int(item.get('sizeGb', 10))
                    t_url = item.get('type', '')
                    disk_type = t_url.split('/')[-1] if t_url else 'pd-standard'
                    z_url = item.get('zone', '')
                    zone = z_url.split('/')[-1] if z_url else 'us-central1-a'
                    
                    add_resource(
                        name=name,
                        r_type="Persistent Disk",
                        status="PROVISIONED",
                        config=f"Size: {size_gb} GB | Type: {disk_type}",
                        location=zone,
                        raw_data={"status": "PROVISIONED", "disk_type": disk_type, "size_gb": size_gb}
                    )
            except Exception as e:
                print(f"⚠️ Warning processing persistent disks: {e}", file=sys.stderr)

    # --- 4. Process GKE Clusters ---
    if any("container.googleapis.com/Cluster" in t for t in asset_types):
        print("☸️ Auditing Google Kubernetes Engine Clusters...")
        cmd = ["gcloud", "container", "clusters", "list", f"--project={project_id}", "--format=json"]
        ok, out, _ = billing_client.run_command(cmd)
        if ok and out:
            try:
                for item in json.loads(out):
                    name = item.get('name', 'unnamed-gke')
                    location = item.get('location', 'us-central1')
                    node_count = int(item.get('currentNodeCount', 0))
                    node_config = item.get('nodeConfig', {})
                    machine_type = node_config.get('machineType', 'e2-medium')
                    status = item.get('status', 'STOPPED')
                    
                    add_resource(
                        name=name,
                        r_type="GKE Cluster",
                        status=status,
                        config=f"Nodes: {node_count} x {machine_type} (+ Mgmt Fee)",
                        location=location,
                        raw_data={"status": status, "node_count": node_count, "machine_type": machine_type}
                    )
            except Exception as e:
                print(f"⚠️ Warning processing GKE clusters: {e}", file=sys.stderr)

    # --- 5. Process Cloud SQL Instances ---
    if any("sqladmin.googleapis.com/Instance" in t for t in asset_types):
        print("🛢️ Auditing Cloud SQL Databases...")
        cmd = ["gcloud", "sql", "instances", "list", f"--project={project_id}", "--format=json"]
        ok, out, _ = billing_client.run_command(cmd)
        if ok and out:
            try:
                for item in json.loads(out):
                    name = item.get('name', 'unnamed-sql')
                    settings = item.get('settings', {})
                    tier = settings.get('tier', 'db-f1-micro')
                    region = item.get('region', 'us-central1')
                    status = item.get('state', 'STOPPED')
                    
                    add_resource(
                        name=name,
                        r_type="Cloud SQL Database",
                        status=status,
                        config=f"Tier: {tier}",
                        location=region,
                        raw_data={"status": status, "tier": tier}
                    )
            except Exception as e:
                print(f"⚠️ Warning processing Cloud SQL instances: {e}", file=sys.stderr)

    # --- 6. Process Networking & Security Endpoints ---
    print("🌐 Auditing Networking & Security Endpoints...")
    # SWP Gateways
    ok, out, _ = billing_client.run_command(["gcloud", "network-services", "gateways", "list", f"--project={project_id}", "--format=json"])
    if ok and out:
        try:
            for item in json.loads(out):
                name = item.get("name", "unnamed-swp").split("/")[-1]
                scope = item.get("scope", "us-central1")
                region = scope.split("/")[-1] if "/" in scope else scope
                add_resource(name, "Networking / Security", "ACTIVE", "Secure Web Proxy Gateway", region, {"status": "ACTIVE", "subtype": "swp_gateway", "count": 1})
        except Exception:
            pass
    swp_assets = [a for a in assets if "networkservices.googleapis.com/Gateway" in a.get("assetType", "")]
    for a in swp_assets:
        name = a.get("name", "").split("/")[-1] or "swp-gateway"
        if name not in handled_resource_names:
            loc = a.get("location", "global")
            add_resource(name, "Networking / Security", "ACTIVE", "Secure Web Proxy Gateway", loc, {"status": "ACTIVE", "subtype": "swp_gateway", "count": 1})

    # Cloud Firewall Endpoints
    ok, out, _ = billing_client.run_command(["gcloud", "network-security", "firewall-endpoints", "list", f"--project={project_id}", "--format=json"])
    if ok and out:
        try:
            for item in json.loads(out):
                name = item.get("name", "unnamed-fw").split("/")[-1]
                location = item.get("location", "global")
                add_resource(name, "Networking / Security", "ACTIVE", "Cloud Firewall Plus Endpoint", location, {"status": "ACTIVE", "subtype": "firewall_endpoint", "count": 1})
        except Exception:
            pass
    fw_assets = [a for a in assets if "networksecurity.googleapis.com/FirewallEndpoint" in a.get("assetType", "")]
    for a in fw_assets:
        name = a.get("name", "").split("/")[-1] or "firewall-endpoint"
        if name not in handled_resource_names:
            loc = a.get("location", "global")
            add_resource(name, "Networking / Security", "ACTIVE", "Cloud Firewall Endpoint", loc, {"status": "ACTIVE", "subtype": "firewall_endpoint", "count": 1})

    # Cloud VPN Gateways
    ok, out, _ = billing_client.run_command(["gcloud", "compute", "vpn-gateways", "list", f"--project={project_id}", "--format=json"])
    if ok and out:
        try:
            for item in json.loads(out):
                name = item.get("name", "unnamed-vpn")
                region_url = item.get("region", "")
                region = region_url.split("/")[-1] if region_url else "us-central1"
                tunnels = item.get("vpnInterfaces", [{}, {}])
                add_resource(name, "Networking / Security", "ACTIVE", f"HA VPN Gateway ({len(tunnels)} Interfaces)", region, {"status": "ACTIVE", "subtype": "vpn_gateway", "count": max(1, len(tunnels))})
        except Exception:
            pass
    vpn_assets = [a for a in assets if "compute.googleapis.com/VpnGateway" in a.get("assetType", "")]
    for a in vpn_assets:
        name = a.get("name", "").split("/")[-1] or "vpn-gateway"
        if name not in handled_resource_names:
            loc = a.get("location", "us-central1")
            add_resource(name, "Networking / Security", "ACTIVE", "HA VPN Gateway (2 Tunnels Est.)", loc, {"status": "ACTIVE", "subtype": "vpn_gateway", "count": 2})

    # Cloud NAT Gateways (via Routers)
    if any("compute.googleapis.com/Router" in t for t in asset_types):
        cmd = ["gcloud", "compute", "routers", "list", f"--project={project_id}", "--format=json"]
        ok, out, _ = billing_client.run_command(cmd)
        if ok and out:
            try:
                for item in json.loads(out):
                    nats = item.get('nats', [])
                    if nats:
                        name = item.get('name', 'router')
                        region_url = item.get('region', '')
                        region = region_url.split('/')[-1] if region_url else 'us-central1'
                        add_resource(f"{name}-nat", "Networking / Security", "ACTIVE", f"Cloud NAT ({len(nats)} gateways)", region, {"status": "ACTIVE", "subtype": "nat_gateway", "count": len(nats)})
            except Exception:
                pass

    # Forwarding Rules
    ok, out, _ = billing_client.run_command(["gcloud", "compute", "forwarding-rules", "list", f"--project={project_id}", "--format=json"])
    if ok and out:
        try:
            items = json.loads(out)
            if items:
                add_resource("load-balancer-rules", "Networking / Security", "ACTIVE", f"{len(items)} Forwarding Rules", "global", {"status": "ACTIVE", "subtype": "forwarding_rule", "count": len(items)})
        except Exception:
            pass
    if "load-balancer-rules" not in handled_resource_names:
        fwd_assets = [a for a in assets if "compute.googleapis.com/ForwardingRule" in a.get("assetType", "")]
        if fwd_assets:
            add_resource("load-balancer-rules", "Networking / Security", "ACTIVE", f"{len(fwd_assets)} Forwarding Rules", "global", {"status": "ACTIVE", "subtype": "forwarding_rule", "count": len(fwd_assets)})

    # --- 7. Process Vertex AI Endpoints ---
    if any("aiplatform.googleapis.com" in t for t in asset_types):
        print("🤖 Auditing Vertex AI Endpoints...")
        ok, out, _ = billing_client.run_command(["gcloud", "ai", "endpoints", "list", f"--project={project_id}", "--format=json"])
        if ok and out:
            try:
                for item in json.loads(out):
                    name = item.get("displayName", item.get("name", "unnamed-ep").split("/")[-1])
                    parts = item.get("name", "").split("/")
                    region = parts[3] if len(parts) > 3 else "us-central1"
                    deployed_models = item.get("deployedModels", [])
                    total_nodes = 0
                    mtype = "n1-standard-4"
                    models_desc = []
                    for dm in deployed_models:
                        machine_spec = dm.get("dedicatedResources", {}).get("machineSpec", {})
                        mtype = machine_spec.get("machineType", "n1-standard-4")
                        rep_count = int(dm.get("dedicatedResources", {}).get("minReplicaCount", 1))
                        total_nodes += rep_count
                        models_desc.append(f"{rep_count}x{mtype}")

                    if total_nodes > 0:
                        cfg_str = ", ".join(models_desc)
                        add_resource(name, "Vertex AI Endpoint", "ACTIVE", f"Dedicated VM ({cfg_str})", region, {"status": "ACTIVE", "subtype": "model_endpoint", "machine_type": mtype, "node_count": total_nodes})
            except Exception:
                pass

        mdl_assets = [a for a in assets if "aiplatform.googleapis.com/Endpoint" in a.get("assetType", "")]
        for a in mdl_assets:
            asset_name = a.get("name", "").split("/")[-1] or "model-endpoint"
            if asset_name not in handled_resource_names:
                loc = a.get("location", "us-central1")
                add_resource(asset_name, "Vertex AI Endpoint", "ACTIVE", "Dedicated Model Endpoint VM", loc, {"status": "ACTIVE", "subtype": "model_endpoint", "node_count": 1})

        ok, out, _ = billing_client.run_command(["gcloud", "ai", "index-endpoints", "list", f"--project={project_id}", "--format=json"])
        if ok and out:
            try:
                for item in json.loads(out):
                    name = item.get("displayName", item.get("name", "unnamed-idx").split("/")[-1])
                    parts = item.get("name", "").split("/")
                    region = parts[3] if len(parts) > 3 else "us-central1"
                    add_resource(name, "Vertex AI Endpoint", "ACTIVE", "Provisioned Vector Search Node", region, {"status": "ACTIVE", "subtype": "index_endpoint", "node_count": 1})
            except Exception:
                pass

        idx_assets = [a for a in assets if "aiplatform.googleapis.com/IndexEndpoint" in a.get("assetType", "")]
        for a in idx_assets:
            asset_name = a.get("name", "").split("/")[-1] or "index-endpoint"
            if asset_name not in handled_resource_names:
                loc = a.get("location", "us-central1")
                add_resource(asset_name, "Vertex AI Endpoint", "ACTIVE", "Provisioned Vector Search Node", loc, {"status": "ACTIVE", "subtype": "index_endpoint", "node_count": 1})

    # --- 8. Process Cloud Run Services ---
    if any("run.googleapis.com/Service" in t for t in asset_types):
        print("⚡ Auditing Cloud Run Services...")
        cmd = ["gcloud", "run", "services", "list", f"--project={project_id}", "--format=json"]
        ok, out, _ = billing_client.run_command(cmd)
        if ok and out:
            try:
                for item in json.loads(out):
                    metadata = item.get("metadata", {})
                    name = metadata.get("name", "unnamed-service")
                    spec = item.get("spec", {})
                    template = spec.get("template", {})
                    t_meta = template.get("metadata", {})
                    annotations = t_meta.get("annotations", {})
                    
                    min_scale_str = annotations.get("autoscaling.knative.dev/minScale") or \
                                    annotations.get("run.googleapis.com/minScale") or "0"
                    min_scale = int(min_scale_str)
                    
                    cpu_throttling = annotations.get("run.googleapis.com/cpu-throttling", "true").lower()
                    
                    if min_scale > 0 or cpu_throttling == "false":
                        instances_to_bill = max(min_scale, 1 if cpu_throttling == "false" else 0)
                        containers = template.get("spec", {}).get("containers", [{}])
                        resources = containers[0].get("resources", {}).get("limits", {}) if containers else {}
                        cpu_str = resources.get("cpu", "1")
                        mem_str = resources.get("memory", "512Mi")
                        
                        vcpu = float(cpu_str.replace("m", "")) / 1000.0 if "m" in cpu_str else float(cpu_str)
                        mem_gb = float(mem_str.replace("Mi", "")) / 1024.0 if "Mi" in mem_str else (float(mem_str.replace("Gi", "")) if "Gi" in mem_str else 0.5)
                        
                        region = metadata.get("labels", {}).get("cloud.googleapis.com/location", "us-central1")
                        add_resource(
                            name=name,
                            r_type="Cloud Run Service",
                            status="ALLOCATED",
                            config=f"Min Instances: {instances_to_bill} ({vcpu} vCPU, {mem_gb:.2f} GB)",
                            location=region,
                            raw_data={"status": "ALLOCATED", "min_instances": instances_to_bill, "vcpu": vcpu, "memory_gb": mem_gb}
                        )
            except Exception as e:
                print(f"⚠️ Warning processing Cloud Run services: {e}", file=sys.stderr)

    # --- 9. Process Universal Catch-All Provisioned Resources ---
    known_handled_prefixes = (
        "compute.googleapis.com/", "container.googleapis.com/", "sqladmin.googleapis.com/",
        "networkservices.googleapis.com/", "networksecurity.googleapis.com/", "aiplatform.googleapis.com/",
        "run.googleapis.com/"
    )
    for a in assets:
        a_type = a.get("assetType", "")
        name = a.get("name", "").split("/")[-1] or "provisioned-resource"
        if name in handled_resource_names:
            continue
        if not any(a_type.startswith(p) for p in known_handled_prefixes):
            if any(k in a_type.lower() for k in ("redis", "memorystore", "spanner", "alloydb", "dataproc", "bigtable", "kafka", "memcache", "tpu", "composer", "datafusion", "apigee", "filestore", "elasticsearch", "mongo")):
                loc = a.get("location", "global")
                service_name = a_type.split("/")[0].replace(".googleapis.com", "").upper()
                add_resource(name, "Universal Provisioned Resource", "PROVISIONED", f"Service: {service_name}", loc, {"status": "PROVISIONED", "asset_type": a_type})

    return discovered_resources, total_hourly_cost
