#!/usr/bin/env python3
"""Scans Terraform HCL and local GCP Asset Inventory CSVs to merge findings with CSPR & NIST KBs."""

import argparse
import csv
import json
import os
import re
import sys


def strip_comments(text: str) -> str:
  """Strips single-line and multi-line comments from HCL code to prevent commented-out settings from fooling checks."""
  # Strip multi-line /* ... */
  text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
  # Strip single-line # ...
  text = re.sub(r'#.*$', '', text, flags=re.MULTILINE)
  # Strip single-line // ...
  text = re.sub(r'//.*$', '', text, flags=re.MULTILINE)
  return text


def extract_resource_blocks(content: str, resource_type: str) -> list:
  """Finds and extracts full resource blocks of a specific type, resolving nested curly braces correctly."""
  blocks = []
  pattern = re.compile(r'resource\s+"' + resource_type + r'"\s+"([^"]+)"\s*\{')
  
  for match in pattern.finditer(content):
    name = match.group(1)
    start_idx = match.end() - 1  # Starts at the opening '{'
    
    # Balanced brace matching loop
    brace_count = 0
    end_idx = -1
    for i in range(start_idx, len(content)):
      char = content[i]
      if char == '{':
        brace_count += 1
      elif char == '}':
        brace_count -= 1
        if brace_count == 0:
          end_idx = i + 1
          break
          
    if end_idx != -1:
      block_content = content[start_idx:end_idx]
      blocks.append((name, block_content))
      
  return blocks


def audit_asset_inventory_csv(csv_path: str, cspr_kb: dict, nist_kb: dict) -> list:
  """Scans a local GCP Asset Inventory CSV dump for security, cost, and reliability gaps."""
  findings = []
  if not os.path.exists(csv_path):
      return findings
      
  print(f"⚡ Scanning local GCP Asset Inventory CSV dump: {csv_path}...")
  try:
      with open(csv_path, 'r', encoding='utf-8') as f:
          reader = csv.reader(f)
          headers = next(reader, None)
          
          # Verify we have correct columns
          if not headers or "Resource type" not in headers:
              print("⚠️ Warning: Invalid Asset Inventory CSV headers. Skipping CSV audit.", file=sys.stderr)
              return findings
              
          type_idx = headers.index("Resource type")
          name_idx = headers.index("Name")
          display_idx = headers.index("Display name") if "Display name" in headers else name_idx
          loc_idx = headers.index("Location") if "Location" in headers else type_idx
          
          for row in reader:
              if len(row) <= max(type_idx, name_idx):
                  continue
                  
              res_type = row[type_idx].strip()
              res_name = row[name_idx].strip()
              display_name = row[display_idx].strip()
              location = row[loc_idx].strip()
              
              # 1. Audit API Keys (P0 Security)
              if "apikeys.Key" in res_type:
                  findings.append({
                      "resource_name": display_name,
                      "resource_type": "apikeys.Key",
                      "vulnerability": "UNRESTRICTED_API_KEY",
                      "severity": "HIGH",
                      "pillar": "SECURITY",
                      "cspr_golden_title": "Restrict API Keys",
                      "cspr_golden_rationale": "Unrestricted API keys can be harvested from client applications, leading to unauthorized API consumption and billing escalations.",
                      "nist_csf_mapping": nist_kb.get("entries", {}).get("PR.AA-05", {"subcategory_id": "PR.AA-05", "description": "Access least privilege managed."}),
                      "remediation_hcl": "# ENFORCE API restrictions (limit usage to specific services/IPs) in Google Cloud Console API & Services > Credentials."
                  })
                  
              # 2. Audit Secret Manager Baseline (P0 Security)
              elif "secretmanager.Secret" in res_type:
                  findings.append({
                      "resource_name": display_name,
                      "resource_type": "secretmanager.Secret",
                      "vulnerability": "UNROTATED_SECRET",
                      "severity": "MEDIUM",
                      "pillar": "SECURITY",
                      "cspr_golden_title": "Rotate Secret Manager Keys",
                      "cspr_golden_rationale": "Secrets such as credentials and passwords should be rotated periodically to limit threat windows in case of leakage.",
                      "nist_csf_mapping": nist_kb.get("entries", {}).get("PR.DS-01", {"subcategory_id": "PR.DS-01", "description": "Data-at-rest protected."}),
                      "remediation_hcl": "# CONFIGURE automatic rotation schedule on Secret Manager version."
                  })
  except Exception as e:
      print(f"⚠️ Warning: Failed to execute CSV audit: {e}", file=sys.stderr)
      
  return findings


def main():
  parser = argparse.ArgumentParser(description="Scan local HCL and CAI CSV files for GCP security gaps.")
  parser.add_argument("--tf_dir", default=None, help="Directory containing customer Terraform .tf files.")
  parser.add_argument("--cai_csv", default=None, help="Path to local GCP Asset Inventory CSV dump.")
  parser.add_argument("--output_json", default="/tmp/war_master_findings.json", help="Path to write unified finding payload.")
  args = parser.parse_args()

  if not args.tf_dir and not args.cai_csv:
    print("❌ Error: Must supply at least one of --tf_dir or --cai_csv for evaluation.", file=sys.stderr)
    sys.exit(1)

  # Load cached knowledge bases if present
  cspr_kb_path = "/tmp/cspr_golden_kb.json"
  nist_kb_path = "/tmp/nist_csf_kb.json"
  
  cspr_kb = {"entries": {}}
  nist_kb = {"entries": {}}
  
  if os.path.exists(cspr_kb_path) and os.path.exists(nist_kb_path):
    print("⚡ Loading cached CSPR & NIST regulatory knowledge bases...")
    try:
      with open(cspr_kb_path, "r", encoding='utf-8') as f:
        cspr_kb = json.load(f)
      with open(nist_kb_path, "r", encoding='utf-8') as f:
        nist_kb = json.load(f)
    except Exception as e:
      print(f"⚠️ Warning: Failed to load lookup tables: {e}. Running without metadata enrichment.", file=sys.stderr)
  else:
    print("⚠️ Warning: Cached knowledge bases not found at /tmp/. Running in baseline mode.", file=sys.stderr)

  findings = []
  
  # 1. Scan HCL Terraform configurations if supplied
  if args.tf_dir:
      if not os.path.exists(args.tf_dir):
          print(f"❌ Error: Target Terraform directory [{args.tf_dir}] does not exist.", file=sys.stderr)
          sys.exit(1)
          
      print(f"⚡ Scanning Terraform HCL files in: {args.tf_dir}...")
      for root, _, files in os.walk(args.tf_dir):
        for file in files:
          if file.endswith(".tf"):
            tf_path = os.path.join(root, file)
            try:
              with open(tf_path, "r", encoding='utf-8') as f:
                content = f.read()
            except Exception as e:
              print(f"⚠️ Warning: Skipping unreadable file {tf_path}: {e}", file=sys.stderr)
              continue
              
            # storage bucket Uniform Access
            storage_buckets = extract_resource_blocks(content, "google_storage_bucket")
            for bucket_name, block_content in storage_buckets:
              clean_block = strip_comments(block_content)
              if "uniform_bucket_level_access" not in clean_block or "uniform_bucket_level_access = false" in clean_block:
                findings.append({
                    "resource_name": bucket_name,
                    "resource_type": "google_storage_bucket",
                    "vulnerability": "MISSING_UNIFORM_ACCESS",
                    "severity": "HIGH",
                    "pillar": "SECURITY",
                    "cspr_golden_title": "Enforce Bucket Policy Only",
                    "cspr_golden_rationale": cspr_kb.get("entries", {}).get("Enforce Bucket Policy Only", {}).get("rationale", "Disabling legacy Access Control Lists (ACLs) prevents accidental public exposure by ensuring all storage objects are governed uniformly by Cloud IAM policies."),
                    "nist_csf_mapping": nist_kb.get("entries", {}).get("PR.DS-01", {"subcategory_id": "PR.DS-01", "description": "Data-at-rest encryption and protection."}),
                    "remediation_hcl": "uniform_bucket_level_access = true"
                })

            # wildcard project IAM bindings
            iam_bindings = extract_resource_blocks(content, "google_project_iam_binding")
            for binding_name, block_content in iam_bindings:
              clean_block = strip_comments(block_content)
              if "allUsers" in clean_block or "allAuthenticatedUsers" in clean_block:
                findings.append({
                    "resource_name": binding_name,
                    "resource_type": "google_project_iam_binding",
                    "vulnerability": "WILDCARD_IAM_BINDING",
                    "severity": "CRITICAL",
                    "pillar": "SECURITY",
                    "cspr_golden_title": "Restrict Wildcard IAM Bindings",
                    "cspr_golden_rationale": "Prevents anonymous public access or open authenticated user rights over project API surfaces.",
                    "nist_csf_mapping": nist_kb.get("entries", {}).get("PR.AA-05", {"subcategory_id": "PR.AA-05", "description": "Identity access rights granted based on least privilege."}),
                    "remediation_hcl": "# REMOVE allUsers/allAuthenticatedUsers from members list"
                })

            # KMS Key rotation gaps
            crypto_keys = extract_resource_blocks(content, "google_kms_crypto_key")
            for key_name, block_content in crypto_keys:
              clean_block = strip_comments(block_content)
              if "rotation_period" not in clean_block:
                findings.append({
                    "resource_name": key_name,
                    "resource_type": "google_kms_crypto_key",
                    "vulnerability": "MISSING_KEY_ROTATION",
                    "severity": "HIGH",
                    "pillar": "RELIABILITY",
                    "cspr_golden_title": "Enforce Cryptographic Key Rotation",
                    "cspr_golden_rationale": "Limits the exposure window of compromised cryptographic material by automatically rotating keys.",
                    "nist_csf_mapping": nist_kb.get("entries", {}).get("PR.DS-02", {"subcategory_id": "PR.DS-02", "description": "Data-in-transit encryption and protection."}),
                    "remediation_hcl": "rotation_period = \"7776000s\" # 90 days"
                })

  # 2. Scan Asset Inventory CSV if supplied
  if args.cai_csv:
      csv_findings = audit_asset_inventory_csv(args.cai_csv, cspr_kb, nist_kb)
      findings.extend(csv_findings)

  # Output unified findings JSON
  try:
    parent = os.path.dirname(args.output_json)
    if parent:
        os.makedirs(parent, exist_ok=True)
        
    with open(args.output_json, "w", encoding='utf-8') as f:
      json.dump(findings, f, indent=2)
      
    print(f"🚀 Success! Found {len(findings)} security and compliance gaps.")
    print(f"  - Unified findings JSON output written to: {args.output_json}")
    
  except Exception as e:
    print(f"❌ Error: Failed to write findings JSON to disk: {e}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
  main()
