#!/usr/bin/env python3
"""
Billing Client Module for Codelab Pricing Estimator.

Provides pricing lookups via BigQuery Cloud Billing public export with static
fallback catalog rates for compute, storage, networking, AI, and serverless infrastructure.
"""

import json
import pathlib
import subprocess
import sys

def _setup_ce_config():
    current = pathlib.Path(__file__).resolve().parent
    for parent in current.parents:
        if (parent / ".agents").is_dir():
            lib_path = str(parent / ".agents" / "lib")
            if lib_path not in sys.path:
                sys.path.insert(0, lib_path)
            return

_setup_ce_config()
import ce_config  # noqa: E402

# Static hourly fallback rates in USD
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
    "n1-standard-8": 0.3800,
    "n2-standard-2": 0.0971,
    "n2-standard-4": 0.1942,
    "t2d-standard-1": 0.0422,
    "t2d-standard-2": 0.0844,
    "c2-standard-4": 0.2088,
    "a2-highgpu-1g": 3.6730,
}

STATIC_DISK_RATES = {
    "pd-standard": 0.040 / 730.0,  # ~$0.04 / GB / month
    "pd-balanced": 0.100 / 730.0,  # ~$0.10 / GB / month
    "pd-ssd": 0.170 / 730.0,       # ~$0.17 / GB / month
    "pd-extreme": 0.370 / 730.0,   # ~$0.37 / GB / month
}

STATIC_SQL_RATES = {
    "db-f1-micro": 0.0130,
    "db-g1-small": 0.0260,
    "db-custom-1-3840": 0.0613,
    "db-custom-2-7680": 0.1226,
    "db-custom-4-15360": 0.2452,
}

# Fixed hourly rates for Networking & Security resources
STATIC_NETWORKING_RATES = {
    "swp_gateway": 0.0800,         # Secure Web Proxy gateway instance
    "firewall_endpoint": 1.2500,   # Cloud Firewall Plus endpoint
    "vpn_gateway": 0.0500,         # Cloud VPN gateway tunnel interface hour
    "nat_gateway": 0.0440,         # Cloud NAT gateway hour
    "forwarding_rule": 0.0250,     # Load Balancer forwarding rule base rate
}

# Fixed hourly rates for Vertex AI provisioned nodes
STATIC_VERTEX_RATES = {
    "index_endpoint": 0.0840,      # Provisioned Vector Search shard / node hour (e2-standard-2 equivalent)
    "model_endpoint": 0.1900,      # Deployed model dedicated VM fallback (n1-standard-4 equivalent)
}

# Cloud Run rates per unit per hour
STATIC_CLOUD_RUN_RATES = {
    "vcpu_hour": 0.0864,           # ~$0.000024 per vCPU-second
    "memory_gb_hour": 0.0090,      # ~$0.0000025 per GB-second
}

# Catch-all rates for universal provisioned services
STATIC_UNIVERSAL_RATES = {
    "redis": 0.0490,               # Memorystore for Redis basic
    "memcache": 0.0350,            # Memorystore for Memcached node
    "spanner": 0.9000,             # Cloud Spanner node hour
    "alloydb": 0.3500,             # AlloyDB instance fallback
    "dataproc": 0.1000,            # Dataproc cluster fee + base estimate
    "bigtable": 0.6500,            # Cloud Bigtable node hour
    "kafka": 0.2500,               # Managed Service for Apache Kafka
    "tpu": 1.5000,                 # Cloud TPU slice base estimate
    "composer": 0.4500,            # Cloud Composer environment hour
    "datafusion": 0.3500,          # Cloud Data Fusion instance hour
    "apigee": 0.8000,              # Apigee API Management node hour
    "filestore": 0.2000,           # Filestore instance hour
    "elasticsearch": 0.3000,       # Elastic Cloud deployment hour
    "mongo": 0.2500,               # MongoDB Atlas managed instance
}


def run_command(cmd_args, timeout=60):
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


def fetch_price_from_bq(service_desc, sku_pattern, region):
    """Queries BigQuery public billing pricing export for precise SKU rates."""
    pricing_table = ce_config.get("pricing_table")
    if not pricing_table:
        return 0.0
    query = f"""
    SELECT 
      billing_account_price.tiered_rates[OFFSET(0)].usd_amount as price
    FROM `{pricing_table}`
    WHERE service.description = '{service_desc}'
      AND sku.description LIKE '%{sku_pattern}%'
      AND '{region}' IN UNNEST(geo_taxonomy.regions)
    LIMIT 1
    """
    cmd_args = ["bq", "query", "--use_legacy_sql=false", "--max_rows=1", "--format=json", query]
    success, stdout, _ = run_command(cmd_args, timeout=15)
    
    if success and stdout:
        try:
            results = json.loads(stdout)
            if results and isinstance(results, list) and len(results) > 0 and 'price' in results[0]:
                return float(results[0]['price'])
        except Exception:
            pass
            
    return 0.0


def get_compute_price(machine_type, region="us-central1"):
    """Finds the hourly price for a compute instance."""
    if not machine_type:
        machine_type = "e2-medium"
        
    family = machine_type.split("-")[0].upper()
    rate = fetch_price_from_bq("Compute Engine", family, region)
    if rate > 0.0:
        return rate
        
    return STATIC_COMPUTE_RATES.get(machine_type, 0.0335)


def get_disk_price(disk_type, size_gb, region="us-central1"):
    """Finds the hourly price for a persistent disk."""
    if not disk_type:
        disk_type = "pd-standard"
    if size_gb <= 0:
        size_gb = 10
        
    resolved_type = "pd-standard"
    for t in STATIC_DISK_RATES.keys():
        if t in disk_type:
            resolved_type = t
            break
            
    rate_per_gb = STATIC_DISK_RATES.get(resolved_type, 0.040 / 730.0)
    return rate_per_gb * float(size_gb)


def get_sql_price(tier, region="us-central1"):
    """Finds the hourly price for a Cloud SQL instance."""
    if not tier:
        tier = "db-f1-micro"
        
    rate = fetch_price_from_bq("Cloud SQL", tier, region)
    if rate > 0.0:
        return rate
        
    return STATIC_SQL_RATES.get(tier, 0.0130)


def get_gke_price(node_count, machine_type, region="us-central1", status="RUNNING"):
    """Finds the hourly price for a GKE cluster including nodes and management fee."""
    node_rate = 0.0
    if status in ("RUNNING", "RECONCILING"):
        node_rate = get_compute_price(machine_type, region)
        
    gke_mgmt_fee = 0.10  # Standard $0.10/hour cluster fee
    return (node_rate * float(node_count)) + gke_mgmt_fee


def get_networking_price(resource_subtype, count=1):
    """Calculates hourly fixed charges for Networking and Security endpoints."""
    c = float(max(0, count))
    if resource_subtype == "swp_gateway":
        return STATIC_NETWORKING_RATES["swp_gateway"] * c
    elif resource_subtype == "firewall_endpoint":
        return STATIC_NETWORKING_RATES["firewall_endpoint"] * c
    elif resource_subtype == "vpn_gateway":
        return STATIC_NETWORKING_RATES["vpn_gateway"] * c
    elif resource_subtype == "nat_gateway":
        return STATIC_NETWORKING_RATES["nat_gateway"] * c
    elif resource_subtype == "forwarding_rule":
        if c <= 5:
            return STATIC_NETWORKING_RATES["forwarding_rule"] * c
        else:
            return (STATIC_NETWORKING_RATES["forwarding_rule"] * 5) + (0.010 * (c - 5))
    return 0.0


def get_vertex_price(resource_subtype, machine_type=None, node_count=1, region="us-central1"):
    """Calculates hourly charges for Vertex AI Index Endpoints and Model Endpoints."""
    c = float(max(1, node_count))
    if resource_subtype == "index_endpoint":
        return STATIC_VERTEX_RATES["index_endpoint"] * c
    elif resource_subtype == "model_endpoint":
        if machine_type:
            vm_rate = get_compute_price(machine_type, region)
            return vm_rate * c
        return STATIC_VERTEX_RATES["model_endpoint"] * c
    return 0.0


def get_cloud_run_price(min_instances=0, vcpu=1.0, memory_gb=0.5):
    """Calculates continuous hourly charges for Cloud Run services with min-instances > 0 or always-allocated CPU."""
    if min_instances <= 0:
        return 0.0
        
    hourly_per_instance = (float(vcpu) * STATIC_CLOUD_RUN_RATES["vcpu_hour"]) + \
                          (float(memory_gb) * STATIC_CLOUD_RUN_RATES["memory_gb_hour"])
    return hourly_per_instance * float(min_instances)


def get_universal_fallback_price(asset_type):
    """Estimates hourly burn rates for other common provisioned GCP resources."""
    asset_lower = asset_type.lower()
    for key, rate in STATIC_UNIVERSAL_RATES.items():
        if key in asset_lower:
            return rate
    return 0.0500
