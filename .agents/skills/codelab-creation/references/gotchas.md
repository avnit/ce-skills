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

---

## 5. Non-Interactive kubectl Authentication & gke-gcloud-auth-plugin

### The Gotcha

Modern `kubectl` (≥1.26) has no in-tree GCP authentication providers. Without `gke-gcloud-auth-plugin` installed, `kubectl` falls back to a metadata-server-based ADC path that fails in headless subshells (`no auth` / metadata 404 errors).

### The Fix

Ensure `gke-gcloud-auth-plugin` is installed and `USE_GKE_GCLOUD_AUTH_PLUGIN=True` is set in the environment, then run `gcloud container clusters get-credentials` before any `kubectl` call. Do **not** inject raw tokens into the codelab — the plugin handles headless auth via the active gcloud identity.

---

## 6. Org-Policy Blocks (vmExternalIpAccess, requireShieldedVm)

### The Gotcha

Target test sandboxes often enforce strict organizational policies (such as `constraints/compute.vmExternalIpAccess` or `constraints/compute.requireShieldedVm`). Adding policy-bypass flags (e.g. `--no-address` or `--shielded-secure-boot`) directly into tutorial command blocks pollutes the published narrative and breaks execution for readers in different organizations.

### The Fix

Remediate the SANDBOX by running `disable_org_policies.sh` (which executes automatically during project provisioning via `create_project.py`). If a specific test environment requires command overrides during validation, place them exclusively in the lab's `overlay.json`. **Never** bake policy-bypass flags into published tutorial narratives.

---

## 7. Zonal Stockouts (ZONE_RESOURCE_POOL_EXHAUSTED)

### The Gotcha

Omitting an explicit `--machine-type` parameter during VM or cluster creation causes Google Cloud to default to standard machine families (such as `n1-standard-1`), which frequently encounter zonal capacity stockouts (`ZONE_RESOURCE_POOL_EXHAUSTED`) in busy sandbox regions.

### The Fix

Always specify an explicit, lightweight machine type (e.g. `--machine-type=e2-micro` or `--machine-type=e2-medium` for general workloads and demo clusters). This complements Gotcha #2's explicit image flags and minimizes resource contention across test zones.

---

## 8. Mermaid Diagram Rendering Errors

### The Gotcha

Complex Mermaid diagrams using nested subgraphs with quoted titles or unescaped HTML characters fail to render in GitHub Flavored Markdown (GFM) and DevSite previewers, displaying broken code blocks instead of visual architecture diagrams.

### The Fix

Use single-tier `flowchart TD` or `flowchart LR` structures. Use `<br/>` tags for multi-line node labels, avoid nested subgraphs with quoted titles, and quote node labels containing parentheses or special characters.

---

## 9. Avoid Unnecessary --fresh Purges During Step Debugging

### The Gotcha

Passing `--fresh` to `tester.py` after a minor step failure (e.g. fixing a syntax error or flag in Step 5) purges local `.tester_state/` progress files while previously deployed GCP resources (VPCs, GKE clusters, subnets) remain active in the sandbox project.
When `tester.py --fresh` restarts execution from Step 1, preceding resource creation commands collide with pre-existing infrastructure (e.g. `ERROR: The resource 'projects/.../networks/demo-vpc' already exists`), failing validation and wasting massive re-provisioning time.

### The Fix

Always default to **stateful resumption** during step debugging. On a step failure, edit the broken command in `.lab.md` and re-run `tester.py` **without** `--fresh` against the same `--project-id`. `tester.py` preserves completed `DONE` steps (such as 15-minute GKE cluster builds), re-reads the edited commands, and re-executes only the failed step. Reserve `--fresh` strictly for catastrophic state corruption (unparseable `.tester_state` JSON or unrecoverable state/infra divergence).

