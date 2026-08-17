#!/usr/bin/env python3
"""
Tag Scrubber & Scaffolding Utilities for Closed-Loop Learning

Provides:
1. Boilerplate Stripping (Iterative cleaning across string fields).
2. Command Scaffolding (Concise rules paired with exact command syntax samples).
3. Service-Specific Knowledge Topics / Tags filtering with fallback domain mapping.
"""

import re
from typing import Any, List

BANNED_PROCESS_TAGS = {
    "validation", "remediation", "closedloop", "bug", "error",
    "test", "fix", "lesson", "generalized", "specific", "result", "status"
}

BOILERPLATE_PATTERNS = [
    r"^verified\s+architectural\s+resolution:\s*",
    r"^verified\s+remediation:\s*",
    r"^lesson\s+learned:\s*",
    r"^generalized\s+lesson:\s*",
    r"^specific\s+lesson:\s*",
    r"^error\s+in\s+command\s+'[^']+'\s*:\s*",
    r"^error\s+executing\s+command\s+'[^']+'\s*:\s*",
]

FALLBACK_DOMAIN_MAPPING = {
    "gcs": ["GCS", "CloudStorage"],
    "storage": ["GCS", "CloudStorage"],
    "gsutil": ["GCS", "CloudStorage"],
    "gke": ["GKE", "Kubernetes"],
    "kubectl": ["GKE", "Kubernetes"],
    "iam": ["IAM", "Security"],
    "serviceaccount": ["IAM", "Security"],
    "role": ["IAM", "Security"],
    "vpc": ["VPC", "Networking"],
    "subnet": ["VPC", "Networking"],
    "network": ["VPC", "Networking"],
    "firewall": ["VPC", "Networking"],
    "compute": ["ComputeEngine"],
    "instance": ["ComputeEngine"],
    "run": ["CloudRun", "Serverless"],
    "bigquery": ["BigQuery", "Data"],
    "bq": ["BigQuery", "Data"],
    "pubsub": ["PubSub", "Messaging"],
    "functions": ["CloudFunctions", "Serverless"],
    "sql": ["CloudSQL", "Database"],
    "cloudsql": ["CloudSQL", "Database"],
    "secret": ["SecretManager", "Security"],
    "secretmanager": ["SecretManager", "Security"],
    "artifact": ["ArtifactRegistry"],
    "gcloud": ["gcloud"]
}


def strip_boilerplate(text_val: Any) -> str:
    """Case-insensitive iterative regex cleaning to remove boilerplate prefixes."""
    if not text_val:
        return ""
    cleaned = str(text_val).strip()
    changed = True
    while changed:
        changed = False
        for pattern in BOILERPLATE_PATTERNS:
            new_text = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
            if new_text != cleaned:
                cleaned = new_text
                changed = True
    return cleaned


def enforce_command_scaffolding(generalized_rule: str, failed_cmd: str = "") -> str:
    """Enforces rule formatting paired with command syntax samples."""
    rule_clean = strip_boilerplate(generalized_rule)

    if re.search(r"Command sample:\s*\n?`[^`]+`", rule_clean, flags=re.IGNORECASE):
        return rule_clean

    clean_cmd = failed_cmd.strip()
    if clean_cmd.startswith("`") and clean_cmd.endswith("`"):
        clean_cmd = clean_cmd[1:-1].strip()

    if clean_cmd:
        return f"{rule_clean}\n\nCommand sample:\n`{clean_cmd}`"
    return rule_clean


def clean_topics(raw_topics: List[Any], context_text: str = "") -> List[str]:
    """Scrubs process tags and applies word boundary fallback domain tags if empty."""
    valid_tags = []
    seen = set()
    if isinstance(raw_topics, list):
        for tag in raw_topics:
            if not isinstance(tag, str):
                continue
            clean_tag = tag.strip()
            if clean_tag and clean_tag.lower() not in BANNED_PROCESS_TAGS and clean_tag.lower() not in seen:
                valid_tags.append(clean_tag)
                seen.add(clean_tag.lower())

    if not valid_tags:
        context_lower = context_text.lower()
        for keyword, mapped_tags in FALLBACK_DOMAIN_MAPPING.items():
            if re.search(rf"\b{re.escape(keyword)}\b", context_lower):
                for m_tag in mapped_tags:
                    if m_tag.lower() not in seen and m_tag.lower() not in BANNED_PROCESS_TAGS:
                        valid_tags.append(m_tag)
                        seen.add(m_tag.lower())

    if not valid_tags:
        valid_tags = ["GCP", "gcloud"]

    return valid_tags
