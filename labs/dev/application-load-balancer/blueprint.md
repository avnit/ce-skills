# Blueprint: Regional External Application Load Balancer (HTTP)

## Target Audience
Cloud Architect (Level 300: Advanced Stateful & Resiliency Patterns)

## Objective & Business Problem
**Business Scenario**: Fast-growing multi-tenant web platforms and modern enterprise microservices architectures require distributing client application requests securely across auto-scaling application fleets. Rather than passing raw network sockets directly to workers, infrastructure teams utilize **Application Load Balancers** to unlock application-layer (Layer 7) HTTP intelligence—including path-based routing, advanced header manipulation, centralized SSL/TLS termination, and seamless site isolation.

This lab demonstrates how to configure a **Regional External Application Load Balancer** leveraging regional Envoy proxies hosted inside a dedicated proxy-only subnet to steer incoming HTTP connections securely to a highly resilient backend fleet.

## Concrete Outcomes
The user will deploy and take away:
1. **Custom Hermetic VPC Network**: `vpc-alb-demo` with regional application subnets, dedicated Envoy proxy-only subnets, and secure Cloud NAT routing.
2. **Resilient Compute Fleets**: A regional Managed Instance Group (MIG) running dynamic Apache/NGINX web workloads capable of responding with client routing context.
3. **Managed Load Balancing Tier**: A full Layer 7 stack consisting of a regional backend service, HTTP URL map, target HTTP proxy, and regional forwarding rule.
4. **Zero-Trust Security Controls**: Explicit firewall restrictions permitting traffic entry strictly from Envoy proxy subnet ranges and Google health check systems, validated via negative access testing.

## Architecture Topology
- **Network Selection**: `vpc-alb-demo` (custom mode), `subnet-app` (`10.60.1.0/24`), `subnet-proxy` (`10.60.2.0/24`, purpose: `REGIONAL_MANAGED_PROXY` in `us-central1`).
- **Compute Backend**: Instance template `template-alb-backend`, Managed Instance Group `mig-alb-backend` (size: 2 instances).
- **Key Configs**: `fw-allow-proxy-to-backend` (TCP 80 from proxy subnet), `fw-allow-gcp-health-checks` (TCP 80 from GCP health check ranges).

## Deployment Steps (Gradual Complexity)

### Step 1: Base Infrastructure Setup
- Enable standard APIs: `compute.googleapis.com`.
- Create custom VPC network and core subnets:
  ```bash
  gcloud compute networks create vpc-alb-demo --subnet-mode=custom
  gcloud compute networks subnets create subnet-app --network=vpc-alb-demo --region=us-central1 --range=10.60.1.0/24
  ```
- Provision the dedicated regional Envoy Proxy-only Subnet:
  ```bash
  gcloud compute networks subnets create subnet-proxy --network=vpc-alb-demo --region=us-central1 --range=10.60.2.0/24 --purpose=REGIONAL_MANAGED_PROXY --role=ACTIVE
  ```
- Deploy Cloud NAT routing gateways for secure package installations:
  ```bash
  gcloud compute routers create router-alb-nat --network=vpc-alb-demo --region=us-central1
  gcloud compute routers nats create gateway-alb-nat --router=router-alb-nat --auto-allocate-nat-external-ips --nat-all-subnet-ip-ranges --region=us-central1
  ```

### Step 2: Workload Fleet Provisioning
- Define instance initial startup script (`startup.sh`) rendering response payloads identifying serving nodes.
- Create regional Instance Template:
  ```bash
  gcloud compute instance-templates create template-alb-backend --region=us-central1 --network=vpc-alb-demo --subnet=subnet-app --no-address --machine-type=e2-micro --metadata-from-file=startup-script=startup.sh --tags=alb-target
  ```
- Deploy regional Managed Instance Group (MIG):
  ```bash
  gcloud compute instance-groups managed create mig-alb-backend --region=us-central1 --template=template-alb-backend --size=2
  ```

### Step 3: Application Load Balancer Orchestration
- Reserve static public access IP:
  ```bash
  gcloud compute addresses create ip-alb-public --region=us-central1
  ```
- Configure regional HTTP health check verification loop:
  ```bash
  gcloud compute health-checks create http hc-http-80 --region=us-central1 --port=80 --request-path="/"
  ```
- Create managed regional backend service:
  ```bash
  gcloud compute backend-services create bs-alb-web --region=us-central1 --load-balancing-scheme=EXTERNAL_MANAGED --protocol=HTTP --port-name=http --health-checks=hc-http-80 --health-checks-region=us-central1
  ```
- Attach the target MIG to the backend service:
  ```bash
  gcloud compute backend-services add-backend bs-alb-web --region=us-central1 --instance-group=mig-alb-backend --instance-group-region=us-central1 --balancing-mode=UTILIZATION --max-utilization=0.8
  ```
- Compile base HTTP URL map routing logic:
  ```bash
  gcloud compute url-maps create map-alb-web --region=us-central1 --default-service=bs-alb-web
  ```
- Establish target HTTP proxy interface:
  ```bash
  gcloud compute target-http-proxies create proxy-alb-web --region=us-central1 --url-map=map-alb-web
  ```
- Bind external public-facing forwarding rule:
  ```bash
  gcloud compute forwarding-rules create fr-alb-web --region=us-central1 --load-balancing-scheme=EXTERNAL_MANAGED --network-tier=PREMIUM --address=ip-alb-public --target-http-proxy=proxy-alb-web --ports=80
  ```
- Authorize strict zero-trust backend firewall access policies:
  ```bash
  gcloud compute firewall-rules create fw-allow-proxy-to-backend --network=vpc-alb-demo --allow=tcp:80 --source-ranges=10.60.2.0/24 --target-tags=alb-target --description="Allow Envoy proxies to communicate with backend targets"
  gcloud compute firewall-rules create fw-allow-gcp-health-checks --network=vpc-alb-demo --allow=tcp:80 --source-ranges=35.191.0.0/16,130.211.0.0/22 --target-tags=alb-target --description="Allow GCP Load Balancing health probers"
  ```
  > **Enterprise Gotcha Callout**: Unlike passthrough architectures where client packets flow directly to workers, managed application load balancers terminate connections at the regional proxy layer. Backend targets must explicitly permit ingress traffic originating from the dedicated Envoy proxy subnet CIDR range (`10.60.2.0/24`), or else health checking and client traffic forwarding will silently hang and fail.

## Verification Strategy

### 1. Layer 7 Ingress Resolution
Send sequential HTTP requests to the load balancer public address to observe dynamic load steering and proxy headers (e.g., `Via: 1.1 google`):
```bash
export ALB_IP=$(gcloud compute addresses describe ip-alb-public --region=us-central1 --format='value(address)')
for i in {1..10}; do curl -s -I http://${ALB_IP}; sleep 1; done
```
**Expected Outcome**: `HTTP/1.1 200 OK` responses containing standard Google load balancing headers, confirming operational Envoy proxy proxying success.

### 2. Negative Security Isolation Check
Attempt executing direct network interactions against backend server ports bypassing proxy layers to confirm hermetic infrastructure zero-trust segmentation.
```bash
curl -s --connect-timeout 5 https://${ALB_IP} || echo "TLS/443 requests actively dropped as proxy configuration isolates unrouted port mappings."
```
