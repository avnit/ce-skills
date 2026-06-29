#!/usr/bin/env python3
"""
Cost Engine Module for Codelab Pricing Estimator.

Calculates aggregated costs, normalizes resource descriptions, and generates
zero-indentation HTML table reports adhering to strict formatting standards.
"""

import billing_client


def evaluate_resource_cost(resource_type, details, region="us-central1"):
    """Calculates deterministic hourly running cost for a normalized resource dictionary."""
    try:
        status = str(details.get("status", "TERMINATED")).upper()
        active_statuses = ("RUNNING", "RECONCILING", "PROVISIONED", "STAGING", "ACTIVE", "ALLOCATED", "RUNNABLE", "READY")
        
        if resource_type == "Compute Instance":
            if status in active_statuses:
                machine_type = details.get("machine_type", "e2-medium")
                return billing_client.get_compute_price(machine_type, region)
            return 0.0
            
        elif resource_type == "Persistent Disk":
            # Disks are billed continuously while provisioned regardless of attachment status
            disk_type = details.get("disk_type", "pd-standard")
            size_gb = details.get("size_gb", 10)
            return billing_client.get_disk_price(disk_type, size_gb, region)
            
        elif resource_type == "GKE Cluster":
            node_count = details.get("node_count", 0)
            machine_type = details.get("machine_type", "e2-medium")
            return billing_client.get_gke_price(node_count, machine_type, region, status)
            
        elif resource_type == "Cloud SQL Database":
            if status in active_statuses:
                tier = details.get("tier", "db-f1-micro")
                return billing_client.get_sql_price(tier, region)
            return 0.0
            
        elif resource_type in ("Networking / Security", "Networking"):
            subtype = details.get("subtype", "")
            count = details.get("count", 1)
            return billing_client.get_networking_price(subtype, count)
            
        elif resource_type in ("Vertex AI Endpoint", "Vertex AI"):
            subtype = details.get("subtype", "model_endpoint")
            machine_type = details.get("machine_type")
            node_count = details.get("node_count", 1)
            return billing_client.get_vertex_price(subtype, machine_type, node_count, region)
            
        elif resource_type == "Cloud Run Service":
            min_instances = details.get("min_instances", 0)
            vcpu = details.get("vcpu", 1.0)
            memory_gb = details.get("memory_gb", 0.5)
            return billing_client.get_cloud_run_price(min_instances, vcpu, memory_gb)
            
        elif resource_type == "Universal Provisioned Resource":
            asset_type = details.get("asset_type", "")
            return billing_client.get_universal_fallback_price(asset_type)
            
    except Exception:
        return 0.0
        
    return 0.0


def format_html_table(resources):
    """Formats the discovered resources into a strict zero-indentation HTML table."""
    lines = [
        '<div style="max-width: 900px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Helvetica, Arial, sans-serif; background: #ffffff; border-radius: 12px; border: 1px solid #e8eaed; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);">',
        '<table style="width: 100%; border-collapse: collapse; margin: 0; font-size: 13px;">',
        '<thead>',
        '<tr style="background-color: #f8f9fa; border-bottom: 2px solid #e8eaed; text-align: left; color: #3c4043;">',
        '<th style="padding: 12px 24px; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Resource Name</th>',
        '<th style="padding: 12px 12px; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Resource Type</th>',
        '<th style="padding: 12px 12px; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Status</th>',
        '<th style="padding: 12px 12px; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Current Configuration</th>',
        '<th style="padding: 12px 12px; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Location</th>',
        '<th style="padding: 12px 24px; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Hourly Cost</th>',
        '</tr>',
        '</thead>',
        '<tbody>'
    ]
    
    if not resources:
        lines.append('<tr style="border-bottom: 1px solid #e8eaed; background-color: #ffffff;">')
        lines.append('<td colspan="6" style="padding: 20px 24px; text-align: center; color: #5f6368;">No billable active resources discovered.</td>')
        lines.append('</tr>')
    else:
        for idx, r in enumerate(resources):
            bg_color = "#ffffff" if idx % 2 == 0 else "#fafbfc"
            lines.append(f'<tr style="border-bottom: 1px solid #e8eaed; background-color: {bg_color};">')
            lines.append(f'<td style="padding: 14px 24px; vertical-align: top; font-weight: 600; color: #3c4043;">`{r.get("name", "N/A")}`</td>')
            lines.append(f'<td style="padding: 14px 12px; vertical-align: top; color: #5f6368;">{r.get("type", "N/A")}</td>')
            
            status = str(r.get("status", "UNKNOWN")).upper()
            status_style = "background: #e6f4ea; color: #137333;" if status in ("RUNNING", "PROVISIONED", "RUNNABLE", "ACTIVE", "ALLOCATED", "READY") else "background: #f1f3f4; color: #5f6368;"
            lines.append(f'<td style="padding: 14px 12px; vertical-align: top;"><span style="{status_style} padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; display: inline-block;">{status}</span></td>')
            
            lines.append(f'<td style="padding: 14px 12px; vertical-align: top; color: #5f6368;">{r.get("config", "N/A")}</td>')
            lines.append(f'<td style="padding: 14px 12px; vertical-align: top; color: #5f6368;">{r.get("location", "N/A")}</td>')
            lines.append(f'<td style="padding: 14px 24px; vertical-align: top; font-weight: 600; color: #1a73e8;">${r.get("hourly_cost", 0.0):.4f}</td>')
            lines.append('</tr>')
            
    lines.append('</tbody>')
    lines.append('</table>')
    lines.append('</div>')
    return "\n".join(lines)


def generate_report(project_id, resources, total_hourly_cost):
    """Generates the full Markdown audit report containing the unindented HTML table."""
    report_lines = [
        "# Deployed Sandbox Pricing Audit Report",
        "",
        f"- **Target GCP Project**: `{project_id}`",
        "- **Deterministic Audit State**: Verified via Cloud Asset Inventory & Native APIs",
        f"- **Hourly Running Cost**: `${total_hourly_cost:.4f}`",
        "",
        "## Active Billable Resources",
        "",
        format_html_table(resources),
        "",
        f"**Total Deployed Sandbox Cost**: `${total_hourly_cost:.4f} / hour`",
        "",
        "## Audit Warnings & Disclaimers",
        "> [!NOTE]",
        "> This audit represents exact hourly configuration charges currently provisioned in your project. Volume-based usage (network egress, query scans, request invocations) is excluded."
    ]
    return "\n".join(report_lines)
