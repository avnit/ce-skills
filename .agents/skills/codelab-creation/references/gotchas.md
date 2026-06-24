# Google Cloud Codelab Development - Gotchas & Best Practices

This document maintains a list of critical gotchas, execution edge cases, and recommended fixes discovered during Google Cloud Codelab design, deployment, and automated validation.

---

## 1. Self-Contained Startup Scripts in Private Subnets

### The Gotcha

Workloads deployed in secure private subnetworks (with no public external IP mapping and no external Cloud NAT gateway) will experience boot hangs and SSH validation timeouts (exit status `255` / `Failed to lookup instance`) if their startup-script payloads attempt network-dependent installations.
Common offenders include:

- `apt-get update && apt-get install -y ...`
- `pip install -r requirements.txt`
- `curl` or `wget` calls to external servers.

### The Fix

1.  **Zero-Dependency Code**: Keep GCE VM startup scripts 100% self-contained. Rely exclusively on core standard libraries pre-installed in the target OS image. For example, rather than installing Node.js or Flask, deploy a basic mock server utilizing Python's built-in `http.server` class.
2.  **Private Google Access**: Ensure Private Google Access is explicitly enabled on the backend subnet (see section 3) so private instances can communicate securely with Google-hosted services (like Cloud Storage or Logging) if bootstrap assets are required.

---

## 2. Explicit Image Mapping for Non-Interactive CLI Pipelines

### The Gotcha

Omitting explicit OS image arguments (e.g., calling `gcloud compute instance-templates create` or `gcloud compute instances create` without image parameters) triggers non-deterministic behavior.
In interactive environments, the CLI prompts the developer to choose from a list of images. In automated non-interactive validation subshells (like `tester.py`), these prompts block execution indefinitely, causing the pipeline to timeout and fail.

### The Fix

Always explicitly define the OS image family and image project on GCE VM and template creation commands:

```bash
--image-family=debian-12 \
--image-project=debian-cloud
```

This guarantees consistent, repeatable, and completely headless execution across all sandboxed environments.

---

## 3. Private Google Access Enablement on Private VPC Subnets

### The Gotcha

Backend workload instances housed in private subnets (without external public IPs) cannot securely reach Google Cloud service endpoints (e.g. BigQuery, Cloud Storage, Cloud Logging, or Cloud Trace) by default. This violates security best practices and breaks telemetry monitoring in production-grade HA architectures.

### The Fix

Always explicitly append the `--enable-private-ip-google-access` flag during the creation of VPC subnetworks hosting private backend instances:

```bash
gcloud compute networks subnets create backend-subnet \
    --network=session-lb-vpc \
    --range=10.0.1.0/24 \
    --region=us-central1 \
    --enable-private-ip-google-access
```

This satisfies Google Cloud Well-Architected security pillars and allows secure, private, internal routing directly to Google APIs.

---

## 4. GKE Autopilot Security Constraints (Warden Policies) & Node Boot Latencies

### The Gotcha

1. GKE Autopilot clusters restrict container capabilities (e.g. adding `NET_ADMIN` will trigger GKE Warden admission webhook violations).
2. Autopilot provisions physical nodes dynamically. System pods (including `konnectivity-agent` and `kube-dns`) have a startup latency of 1-2 minutes. Executing commands (`kubectl exec`) before this delay will fail with `No agent available` or `pod does not have a host assigned`.

### The Fix

1. Omit root privileges and custom capabilities from GKE Autopilot manifests.
2. In automated scripts, always wait for pod readiness explicitly using:
   `kubectl wait --for=condition=Ready pod/<pod-name> --timeout=300s`
   and avoid passing TTY flags (`-it`) in non-interactive terminal runs.
