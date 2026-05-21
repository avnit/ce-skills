#!/usr/bin/env python3
"""Script to gather audit log evidence and format as a markdown table."""

import json
import os
import subprocess
import sys

DEFAULT_LOG_LIMIT = 5000



def main():
    if len(sys.argv) < 3:
        print("Usage: gather_evidence.py <project_id> <output_file>")
        sys.exit(1)

    project_id = sys.argv[1]
    output_file = sys.argv[2]

    query = f'logName="projects/{project_id}/logs/cloudaudit.googleapis.com%2Factivity" AND NOT protoPayload.methodName="io.k8s.coordination.v1.leases.update" AND NOT protoPayload.authenticationInfo.principalEmail="system:cluster-autoscaler" AND NOT protoPayload.resourceName="core/v1/namespaces/kube-system/configmaps/gke-common-webhook-heartbeat"'




    print(f"Querying audit logs for project {project_id}...")
    cmd = [
        "gcloud",
        "logging",
        "read",
        query,
        f"--project={project_id}",
        f"--limit={DEFAULT_LOG_LIMIT}",
        "--order=asc",
        "--format=json",
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True
        )
        logs = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running gcloud: {e.stderr}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        sys.exit(1)

    print(f"Found {len(logs)} log entries. Generating table...")

    output_dir = os.path.dirname(output_file)
    map_file = os.path.join(output_dir, "section_map.json")
    section_map = {}

    if os.path.exists(map_file):
        print(f"Loading section map from {map_file}...")
        try:
            with open(map_file, "r") as f:
                section_map = json.load(f)
        except Exception as e:
            print(f"Error loading section map: {e}")
    else:
        print(f"No section map found at {map_file}. Classifying all logs under Common/Unclassified.")
        section_map = {}

    def correlate_to_section(action, resource):
        for section, keywords in section_map.items():
            for kw in keywords:
                if kw in action or kw in resource:
                    return section
        return "Unknown/Common"


    # Header
    table = "| Timestamp | Action | Resource | Principal | Section |\n"
    table += "|---|---|---|---|---|\n"

    for entry in logs:
        proto_payload = entry.get("protoPayload", {})
        timestamp = entry.get("timestamp", "")
        action = proto_payload.get("methodName", "")
        resource = proto_payload.get("resourceName", "")
        auth_info = proto_payload.get("authenticationInfo", {})
        principal = auth_info.get("principalEmail", "")

        # Clean up resource name if it's too long
        if "projects/" in resource:
             resource = resource.split("/")[-1]

        section = correlate_to_section(action, resource)

        table += f"| {timestamp} | {action} | {resource} | {principal} | {section} |\n"


    with open(output_file, "w") as f:
        f.write(table)

    print(f"Evidence written to {output_file}")


if __name__ == "__main__":
    main()
