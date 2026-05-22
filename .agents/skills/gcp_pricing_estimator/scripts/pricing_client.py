#!/usr/bin/env python3
"""Mock Python Pricing Client for CWP.PricingService to enable zero-dependency local testing."""

import argparse
import json
import os
import sys


def calculate_mock_costs(payload: dict) -> dict:
    """Natively calculates realistic GCP pre-sales pricing estimates based on the extracted topology."""
    region = payload.get("region", "us-central1")
    resources = payload.get("resources", [])
    
    line_items = []
    total_monthly_cost = 0.0
    
    for res in resources:
        name = res.get("name", "generic-resource")
        res_type = res.get("type", "unknown")
        
        sku_id = "UNKNOWN-SKU"
        sku_desc = "Unclassified Resource SKU"
        
        if res_type == "gke_node_pool":
            machine_type = res.get("machine_type", "e2-standard-4")
            node_count = int(res.get("node_count", 3))
            # E2-standard-4 is approx $146.00/month
            monthly_cost = 146.00 * node_count
            config_desc = f"Machine: {machine_type} | Nodes: {node_count}"
            sku_id = "72CE-4387-B81D"
            sku_desc = "E2 instance Core running in Americas"
            
        elif res_type == "alloydb_instance":
            storage_gb = int(res.get("storage_gb", 100))
            # AlloyDB storage is approx $0.30/GB/month + compute baseline of $350/month
            monthly_cost = 350.00 + (storage_gb * 0.30)
            config_desc = f"Tier: db-alloydb-default | Storage: {storage_gb} GB"
            sku_id = "99BA-FF2A-8320"
            sku_desc = "AlloyDB instance Enterprise Capacity"
            
        elif "filestore" in name.lower() or res_type == "filestore":
            storage_gb = int(res.get("storage_gb", 1000))
            # Filestore Enterprise is approx $0.30/GB/month
            monthly_cost = storage_gb * 0.30
            config_desc = f"Enterprise | Capacity: {storage_gb} GB"
            sku_id = "C6AA-884C-91B7"
            sku_desc = "Filestore Enterprise capacity in us-central1"
            
        elif "hyperdisk" in name.lower() or res_type == "hyperdisk":
            storage_gb = int(res.get("storage_gb", 500))
            # Hyperdisk Extreme baseline is approx $0.12/GB/month
            monthly_cost = storage_gb * 0.12
            config_desc = f"Extreme | Capacity: {storage_gb} GB"
            sku_id = "5D81-FF8E-48A1"
            sku_desc = "Hyperdisk Extreme Provisioned Capacity"
            
        else:
            monthly_cost = 50.00
            config_desc = "Standard Provisioned Resource"
            sku_id = "E431-ABCB-4FA8"
            sku_desc = "Standard GCP Infrastructure resource unit"
            
        total_monthly_cost += monthly_cost
        line_items.append({
            "Resource Name": name,
            "Resource Type": res_type.upper().replace("_", " "),
            "SKU ID": sku_id,
            "SKU Description": sku_desc,
            "Status": "PROVISIONED",
            "Current Configuration": config_desc,
            "Location": region,
            "Monthly Cost": f"${monthly_cost:.2f}"
        })
        
    return {
        "project_id": payload.get("project_id", "customer-sandbox-99"),
        "region": region,
        "line_items": line_items,
        "total_monthly_cost": f"${total_monthly_cost:.2f}"
    }


def main():
    parser = argparse.ArgumentParser(description="Local Mock pre-sales Pricing Client for testing.")
    parser.add_argument("--payload_path", required=True, help="Path to local JSON file containing infrastructure topology.")
    parser.add_argument("--output_path", required=True, help="Path to save calculated pricing estimate JSON.")
    args = parser.parse_args()
    
    if not os.path.exists(args.payload_path):
        print(f"❌ Error: Payload file not found at [{args.payload_path}]", file=sys.stderr)
        sys.exit(1)
        
    try:
        with open(args.payload_path, 'r', encoding='utf-8') as f:
            payload = json.load(f)
            
        print(f"⚡ Emulating BNS call to CWP.PricingService (PCTv2)...")
        results = calculate_mock_costs(payload)
        
        # Create parent dir if needed
        parent = os.path.dirname(args.output_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
            
        # Save JSON
        with open(args.output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
            
        # Save CSV for GSHEETS CLI import
        csv_path = args.output_path.replace(".json", ".csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("Resource Name,Resource Type,SKU ID,SKU Description,Status,Current Configuration,Location,Monthly Cost\n")
            for item in results["line_items"]:
                f.write(f"{item['Resource Name']},{item['Resource Type']},{item['SKU ID']},{item['SKU Description']},{item['Status']},{item['Current Configuration']},{item['Location']},{item['Monthly Cost']}\n")
            f.write(f"\nTotal Monthly Cost,,,,,,,{results['total_monthly_cost']}\n")
            
        print(f"🚀 Success! Dynamic pre-sales pricing estimated saved.")
        print(f"  - JSON Artifact: {args.output_path}")
        print(f"  - CSV Artifact: {csv_path}")
        
    except Exception as e:
        print(f"❌ Local execution failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
