---
name: codelab-audit-logging
description: >-
  Extracts and formats GCP audit logs to provide evidence of actions performed
  during codelab testing and validation. Use when you need to verify that
  specific resources were created, deleted, or configured, and generate a
  table of evidence in the lab directory.
---

# Codelab Audit Logging Skill

This skill helps you extract evidence from GCP Audit Logs during codelab testing and validation.

## How to use

1.  **Identify the target resources**: Know what resources you want to find evidence for (e.g., GKE cluster, forwarding rules, subnets).
2.  **Run `gcloud logging read`**: Use a query to find relevant audit logs.
3.  **Format as a table**: Create a table in the lab directory with columns: `Timestamp`, `Action`, `Resource`, `Principal`.

### Example Query

```bash
gcloud logging read 'logName="projects/{project_id}/logs/cloudaudit.googleapis.com%2Factivity" AND resource.type="gce_network"' --limit=10 --format="table(timestamp, protoPayload.methodName, protoPayload.resourceName, protoPayload.authenticationInfo.principalEmail)"
```

### Automated Evidence Gathering

You can use the provided script to gather evidence automatically:

```bash
./.agents/skills/codelab_audit_logging/scripts/gather_evidence.py {project_id} {output_file}
```

Example:

```bash
./.agents/skills/codelab_audit_logging/scripts/gather_evidence.py gke-service-ext-1775761721 ./evidence.md
```

This will create an `evidence.md` file with a table of the last 5000 audit log entries.

---

## Gotchas & Pitfalls

- **Log Latency**: Google Cloud Audit Logs can take up to 1-2 minutes to appear. If a resource was just created, wait or retry the script after 60 seconds.
- **IAM Permissions**: Reading activity logs requires `roles/logging.viewer` or `roles/viewer` on the target project. Ensure the active admin credentials possess this role.
- **Filter Truncation**: The script limits retrieval to the last 5000 logs (defined by `DEFAULT_LOG_LIMIT`). For long-running complex setups, refine your resource filters to prevent relevant creation events from being rotated out.
