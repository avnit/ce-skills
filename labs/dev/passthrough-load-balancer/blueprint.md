# Blueprint: Regional External Passthrough Network Load Balancer with Maglev Consistent Hashing

## Target Audience
Cloud Architect

## Objective & Business Problem
**Business Scenario**: High-throughput real-time logging, low-latency telemetry ingest pipelines, and online multiplayer game servers require distributing incoming connection loads directly to backend application fleets without introducing application-layer proxy overhead or terminating SSL/TLS at the load balancing tier. 

This lab demonstrates how enterprise infrastructure teams configure a **Regional External Passthrough Network Load Balancer** backed by a Managed Instance Group (MIG). To maintain stateful session continuity for long-lived TCP/UDP streams, the load balancer is configured with **Maglev consistent hashing** session affinity, ensuring client packets consistently route to the exact same worker node regardless of transient fleet scaling events.

## Concrete Outcomes
The user will deploy and take away:
1. **Custom Hermetic VPC Network**: `vpc-passthrough-demo` with regional subnets and dedicated Cloud NAT gateways for private package resolution.
2. **Compute Workload Fleet**: A declarative Instance Template and Managed Instance Group (MIG) running optimized NGINX web servers serving direct response payloads.
3. **Passthrough Load Balancing Tier**: A regional external backend service and forwarding rule bound to a static external IP address utilizing consistent hash affinity.
4. **Security Posture**: Explicit firewall policies locking down access strictly to health checks (`35.191.0.0/16`, `209.85.152.0/22`, `209.85.204.0/22`) and authorized external ingress ranges, paired with negative security validation scripts.

## Architecture Topology
- **Network Selection**: `vpc-passthrough-demo` (custom mode), `subnet-passthrough-demo` (`10.50.1.0/24` in `us-central1`).
- **Compute Backend**: Instance template `template-web-backend`, Managed Instance Group `mig-web-backend` (target size: 2 instances).
- **Key Configs**: `fw-allow-health-checks` (TCP 80 from GCP health checking ranges), `fw-allow-external-lb` (TCP 80 from `0.0.0.0/0`).

## Deployment Steps (Gradual Complexity)

### Step 1: Base Infrastructure Setup
- Enable standard APIs: `compute.googleapis.com`.
- Create custom VPC network and subnets:
  ```bash
  gcloud compute networks create vpc-passthrough-demo --subnet-mode=custom
  gcloud compute networks subnets create subnet-passthrough-demo --network=vpc-passthrough-demo --region=us-central1 --range=10.50.1.0/24
  ```
- Deploy Cloud NAT router and gateway to allow private instance initialization:
  ```bash
  gcloud compute routers create router-nat --network=vpc-passthrough-demo --region=us-central1
  gcloud compute routers nats create gateway-nat --router=router-nat --auto-allocate-nat-external-ips --nat-all-subnet-ip-ranges --region=us-central1
  ```

### Step 2: Compute Workload Fleet Deployment
- Construct startup script file (`startup.sh`) to dynamically install NGINX and output hostname/IP identification headers for easy load verification.
- Create regional Instance Template without public IP addresses:
  ```bash
  gcloud compute instance-templates create template-web-backend --region=us-central1 --network=vpc-passthrough-demo --subnet=subnet-passthrough-demo --no-address --machine-type=e2-micro --metadata-from-file=startup-script=startup.sh --tags=lb-backend
  ```
- Deploy regional Managed Instance Group (MIG):
  ```bash
  gcloud compute instance-groups managed create mig-web-backend --region=us-central1 --template=template-web-backend --size=2
  ```

### Step 3: Passthrough Load Balancer Configuration
- Reserve regional static external IP address:
  ```bash
  gcloud compute addresses create ip-lb-passthrough --region=us-central1
  ```
- Create dedicated TCP health check:
  ```bash
  gcloud compute health-checks create tcp hc-tcp-80 --region=us-central1 --port=80
  ```
- Create regional backend service using Maglev consistent hashing session affinity:
  ```bash
  gcloud compute backend-services create bs-passthrough-tcp --region=us-central1 --load-balancing-scheme=EXTERNAL --protocol=TCP --health-checks=hc-tcp-80 --session-affinity=CLIENT_IP_PROTO --health-checks-region=us-central1
  ```
  > **Enterprise Gotcha Callout**: Setting `--session-affinity=CLIENT_IP_PROTO` or `CLIENT_IP` activates consistent hashing mechanisms natively within Maglev kernel packet handling arrays, ensuring highly uniform load distribution while protecting stateful session boundaries.
- Add the Managed Instance Group to the backend service:
  ```bash
  gcloud compute backend-services add-backend bs-passthrough-tcp --region=us-central1 --instance-group=mig-web-backend --instance-group-region=us-central1
  ```
- Create regional forwarding rule targeting the backend service:
  ```bash
  gcloud compute forwarding-rules create fr-passthrough-tcp --region=us-central1 --load-balancing-scheme=EXTERNAL --address=ip-lb-passthrough --ip-protocol=TCP --ports=80 --backend-service=bs-passthrough-tcp --backend-service-region=us-central1
  ```
- Authorize strict firewall policies:
  ```bash
  gcloud compute firewall-rules create fw-allow-health-checks --network=vpc-passthrough-demo --allow=tcp:80 --source-ranges=35.191.0.0/16,209.85.152.0/22,209.85.204.0/22 --target-tags=lb-backend --description="Allow GCP health checking ranges"
  gcloud compute firewall-rules create fw-allow-external-lb --network=vpc-passthrough-demo --allow=tcp:80 --source-ranges=0.0.0.0/0 --target-tags=lb-backend --description="Allow public client traffic to load balanced workers"
  ```

## Verification Strategy

### 1. Positive Passthrough Verification
Execute continuous `curl` requests targeting the reserved load balancer external IP address to observe uniform response serving across both backend instance identities:
```bash
export LB_IP=$(gcloud compute addresses describe ip-lb-passthrough --region=us-central1 --format='value(address)')
for i in {1..10}; do curl -s http://${LB_IP}; sleep 1; done
```
**Expected Outcome**: HTTP response headers identifying the respective internal host VM server instance names (`mig-web-backend-XXXX`), validating end-to-end Maglev steering success.

### 2. Negative Zero-Trust Verification
Attempt connecting to an unauthorized protocol or destination port (e.g., SSH/22 or HTTPS/443) on the forwarding rule external IP address to verify zero-trust isolation:
```bash
curl -s --connect-timeout 5 https://${LB_IP} || echo "Connection actively blocked/timed out as intended."
```
**Expected Outcome**: Clean request drop/timeout confirming infrastructure firewall lockdown integrity.
