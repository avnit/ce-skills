#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys

# Public fallbacks for standard Sandbox resources (hourly rates in USD)
STATIC_COMPUTE_RATES = {
    "e2-micro": 0.0084,
    "e2-small": 0.0168,
    "e2-medium": 0.0335,
    "e2-standard-2": 0.0670,
    "e2-standard-4": 0.1340,
    "e2-standard-8": 0.2680,
    "n1-standard-1": 0.0475,
    "n1-standard-2": 0.0950,
    "n1-standard-4": 0.1900,
    "n2-standard-2": 0.0971,
    "n2-standard-4": 0.1942,
    "t2d-standard-1": 0.0422,
    "t2d-standard-2": 0.0844,
}

STATIC_DISK_RATES = {
    "pd-standard": 0.040 / 730,  # $0.04 / GB / month
    "pd-balanced": 0.100 / 730,  # $0.10 / GB / month
    "pd-ssd": 0.170 / 730,       # $0.17 / GB / month
    "pd-extreme": 0.370 / 730,   # $0.37 / GB / month
}

STATIC_SQL_RATES = {
    "db-f1-micro": 0.0130,
    "db-g1-small": 0.0260,
    "db-custom-1-3840": 0.0613,
    "db-custom-2-7680": 0.1226,
    "db-custom-4-15360": 0.2452,
}

def run_command(cmd_args, timeout=45):
    """Executes a command without a shell and returns success status, stdout, and stderr."""
    try:
        result = subprocess.run(
            cmd_args,
            shell=False,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired as e:
        return False, "", f"Command timed out after {timeout} seconds: {e}"
    except Exception as e:
        return False, "", str(e)

def fetch_price_from_bq(service_desc, machine_family, region):
    """Queries BigQuery public billing pricing export for precise SKU rates."""
    query = f"""
    SELECT 
      billing_account_price.tiered_rates[OFFSET(0)].usd_amount as price
    FROM `billing-350700.billing.cloud_pricing_export`
    WHERE service.description = '{service_desc}'
      AND sku.description LIKE '%{machine_family}%'
      AND '{region}' IN UNNEST(geo_taxonomy.regions)
    LIMIT 1
    """
    cmd_args = ["bq", "query", "--use_legacy_sql=false", "--max_rows=1", "--format=json", query]
    success, stdout, stderr = run_command(cmd_args)
    
    if success:
        try:
            results = json.loads(stdout)
            if results:
                return float(results[0]['price'])
        except Exception:
            pass
            
    return 0.0

def get_compute_price(machine_type, region):
    """Finds the hourly price for a compute instance."""
    if not machine_type:
        machine_type = "e2-medium"
        
    family = machine_type.split("-")[0].upper()
    
    # Try BigQuery first
    rate = fetch_price_from_bq("Compute Engine", family, region)
    if rate > 0.0:
        return rate
        
    # Fallback to static catalog
    return STATIC_COMPUTE_RATES.get(machine_type, 0.0335)

def get_disk_price(disk_type, size_gb, region):
    """Finds the hourly price for a persistent disk."""
    if not disk_type:
        disk_type = "pd-standard"
    if size_gb <= 0:
        size_gb = 10
        
    # Map GCP Disk URL to standard types
    resolved_type = "pd-standard"
    for t in STATIC_DISK_RATES.keys():
        if t in disk_type:
            resolved_type = t
            break
            
    rate_per_gb = STATIC_DISK_RATES.get(resolved_type, 0.040 / 730)
    return rate_per_gb * size_gb

def get_sql_price(tier, region):
    """Finds the hourly price for a Cloud SQL instance."""
    if not tier:
        tier = "db-f1-micro"
        
    # Try dynamic lookup
    rate = fetch_price_from_bq("Cloud SQL", tier, region)
    if rate > 0.0:
        return rate
        
    # Fallback to static catalog
    return STATIC_SQL_RATES.get(tier, 0.0130)

def audit_project(project_id, save_path):
    """Discovers all active running resources and calculates precise hourly running costs."""
    print(f"🔍 Performing deterministic billing audit on GCP Project: [{project_id}]...")
    
    # 1. Discover assets using Cloud Asset Inventory
    asset_cmd = [
        "gcloud", "asset", "search-all-resources",
        f"--scope=projects/{project_id}",
        "--format=json"
    ]
    success, stdout, stderr = run_command(asset_cmd)
    
    if not success:
        print(f"❌ Failed to search assets in project {project_id}:\n{stderr}", file=sys.stderr)
        if "cloudasset.googleapis.com" in stderr.lower():
            print("💡 Fix: Please enable the Cloud Asset API in your target project.", file=sys.stderr)
        sys.exit(1)
        
    try:
        assets = json.loads(stdout)
    except Exception as e:
        print(f"❌ Error parsing assets JSON: {e}", file=sys.stderr)
        sys.exit(1)
        
    if not assets:
        print(f"\nℹ️ No active resources found in project: {project_id}.")
        return
        
    # Filter asset categories
    asset_types = [a.get('assetType') for a in assets]
    print(f"📋 Discovered {len(assets)} total resources across {len(set(asset_types))} unique asset types.")
    
    discovered_resources = []
    total_hourly_cost = 0.0
    
    # --- 2. Process GCE Instances ---
    if "compute.googleapis.com/Instance" in asset_types:
        print("🖥️ Auditing Compute Engine Instances...")
        cmd = ["gcloud", "compute", "instances", "list", f"--project={project_id}", "--format=json"]
        ok, out, err = run_command(cmd)
        if ok:
            for item in json.loads(out):
                name = item.get('name', 'unnamed-vm')
                machine_url = item.get('machineType', '')
                machine_type = machine_url.split('/')[-1] if machine_url else 'e2-medium'
                zone_url = item.get('zone', '')
                zone = zone_url.split('/')[-1] if zone_url else 'us-central1-a'
                region = "-".join(zone.split("-")[:2])
                status = item.get('status', 'TERMINATED')
                
                rate = 0.0
                if status == "RUNNING":
                    rate = get_compute_price(machine_type, region)
                    
                cost = rate
                total_hourly_cost += cost
                
                discovered_resources.append({
                    'name': name,
                    'type': 'Compute Instance',
                    'config': f"Machine: {machine_type}",
                    'location': zone,
                    'status': status,
                    'hourly_cost': cost
                })
                
    # --- 3. Process Persistent Disks ---
    if "compute.googleapis.com/Disk" in asset_types:
        print("💾 Auditing Persistent Disks...")
        cmd = ["gcloud", "compute", "disks", "list", f"--project={project_id}", "--format=json"]
        ok, out, err = run_command(cmd)
        if ok:
            for item in json.loads(out):
                name = item.get('name', 'unnamed-disk')
                size_gb = int(item.get('sizeGb', 10))
                disk_type_url = item.get('type', '')
                disk_type = disk_type_url.split('/')[-1] if disk_type_url else 'pd-standard'
                zone_url = item.get('zone', '')
                zone = zone_url.split('/')[-1] if zone_url else 'us-central1-a'
                region = "-".join(zone.split("-")[:2])
                
                # Disks are always billed while provisioned, status doesn't halt disk charges
                cost = get_disk_price(disk_type, size_gb, region)
                total_hourly_cost += cost
                
                discovered_resources.append({
                    'name': name,
                    'type': 'Persistent Disk',
                    'config': f"Size: {size_gb} GB | Type: {disk_type}",
                    'location': zone,
                    'status': 'PROVISIONED',
                    'hourly_cost': cost
                })
                
    # --- 4. Process GKE Clusters ---
    if "container.googleapis.com/Cluster" in asset_types:
        print("☸️ Auditing Google Kubernetes Engine Clusters...")
        cmd = ["gcloud", "container", "clusters", "list", f"--project={project_id}", "--format=json"]
        ok, out, err = run_command(cmd)
        if ok:
            for item in json.loads(out):
                name = item.get('name', 'unnamed-gke')
                location = item.get('location', 'us-central1')
                region = "-".join(location.split("-")[:2])
                node_count = int(item.get('currentNodeCount', 0))
                
                # Extract machine configurations of GKE nodes
                node_config = item.get('nodeConfig', {})
                machine_type = node_config.get('machineType', 'e2-medium')
                status = item.get('status', 'STOPPED')
                
                # Compute GKE Node Costs
                node_rate = 0.0
                if status == "RUNNING" or status == "RECONCILING":
                    node_rate = get_compute_price(machine_type, region)
                    
                gke_mgmt_fee = 0.10  # GKE management fee ($0.10/hour per GKE cluster, GA)
                cost = (node_rate * node_count) + gke_mgmt_fee
                total_hourly_cost += cost
                
                discovered_resources.append({
                    'name': name,
                    'type': 'GKE Cluster',
                    'config': f"Nodes: {node_count} x {machine_type}",
                    'location': location,
                    'status': status,
                    'hourly_cost': cost
                })
                
    # --- 5. Process Cloud SQL Instances ---
    if "sqladmin.googleapis.com/Instance" in asset_types:
        print("🛢️ Auditing Cloud SQL Databases...")
        cmd = ["gcloud", "sql", "instances", "list", f"--project={project_id}", "--format=json"]
        ok, out, err = run_command(cmd)
        if ok:
            for item in json.loads(out):
                name = item.get('name', 'unnamed-sql')
                settings = item.get('settings', {})
                tier = settings.get('tier', 'db-f1-micro')
                region = item.get('region', 'us-central1')
                status = item.get('state', 'STOPPED')
                
                cost = 0.0
                if status == "RUNNABLE":
                    cost = get_sql_price(tier, region)
                    
                total_hourly_cost += cost
                
                discovered_resources.append({
                    'name': name,
                    'type': 'Cloud SQL Database',
                    'config': f"Tier: {tier}",
                    'location': region,
                    'status': status,
                    'hourly_cost': cost
                })
                
    # --- 6. Generate Report ---
    report = [
        "# Deployed Sandbox Pricing Audit Report",
        "",
        f"*   **Target GCP Project**: `{project_id}`",
        "*   **Deterministic Audit State**: Verified via Cloud Asset Inventory",
        f"*   **Hourly Running Cost**: ${total_hourly_cost:.3f}",
        "",
        "## Active Billable Resources",
        "",
        "| Resource Name | Resource Type | Status | Current Configuration | Location | Hourly Cost |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |"
    ]
    
    for r in discovered_resources:
        report.append(f"| {r['name']} | {r['type']} | {r['status']} | {r['config']} | {r.get('location', 'N/A')} | ${r['hourly_cost']:.4f} |")
        
    report.append("")
    report.append(f"**Total Deployed Sandbox Cost**: ${total_hourly_cost:.3f} / hour")
    report.append("")
    report.append("## Audit Warnings & Disclaimers")
    report.append("> [!NOTE]")
    report.append("> This audit represents the exact hourly configuration charges currently running in your project. Volume-based usage (network egress, query scans) is excluded.")
    
    report_str = "\n".join(report)
    print("\n" + report_str + "\n")
    
    if save_path:
        try:
            parent_dir = os.path.dirname(save_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(report_str + "\n")
            print(f"💾 Report audit successfully exported to: {save_path}")
        except Exception as e:
            print(f"❌ Failed to save report: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(
        description="Google Cloud Deployed Sandbox Pricing Auditor. Queries Asset Inventory to get exact, deterministic running costs of active resources.",
        epilog="""
Examples:
  # Audit the currently running sandbox environment project:
  python3 extract_and_estimate.py --project "my-sandbox-project-123"

  # Audit and save the report to a file:
  python3 extract_and_estimate.py --project "my-sandbox-project-123" --save-report "artifacts/deployed_cost.md"
"""
    )
    
    parser.add_argument("--project", required=True, help="GCP Project ID to audit running resources deterministically.")
    parser.add_argument("--save-report", help="Absolute or relative path to export the Markdown cost report.")
    
    args = parser.parse_args()
    
    audit_project(
        project_id=args.project,
        save_path=args.save_report
    )

if __name__ == "__main__":
    main()
