# One-Pager: Acme Corp + GCP Executive Architecture Sync

**Meeting**: Acme Corp + GCP Architecture & Capacity Bi-Weekly  
**Date & Time**: Tuesday, July 14, 2026 | 2:00 PM – 2:50 PM PDT  
**Meeting Deck**: [Acme Corp BiWeekly Sync Deck (go/acme-sync-deck)](https://docs.google.com/presentation/d/1234567890abcdefghijklmnopqrstuvwxyz/edit) `[Internal Only]`  
**Account Friction Temperature**: `High 🟠`  
**Primary Participants**:

- **Customer Team**: Jane Doe (`jane.doe@acme.example.com`), John Smith (`john.smith@acme.example.com`)
- **Google Team**: Lead CE (`ce-lead@google.com`), TAM Lead (`tam-lead@google.com`), Capacity Eng (`capacity-eng@google.com`)

---

## Grounded Account Friction & Sentiment Analysis

| Metric                           | Rating                   | Grounded Evidence & Reference Link                                                                                                                                                      |
| :------------------------------- | :----------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Account Friction Temperature** | `High 🟠`                | M4 Ramp assessment is blocked due to missing VM shapes ([b/123456789](https://buganizer.corp.google.com/issues/123456789)). Capacity Eng cannot proceed until shape specs are provided. |
| **Customer Technical Sentiment** | `Frustrated / Impatient` | Customer expressed urgency regarding reserved external IP block removal without clear discovery tools ([Google Doc Sample](https://docs.google.com/document/d/abcdef123456789/edit)).   |
| **Launch Timeline Risk**         | `At Risk`                | August 2026 M4 ramp plan (~16.3k cores) requires immediate shape confirmation to meet lead time constraints ([Horizon RDR99999999](https://horizon.corp.google.com/list/RDR99999999)).  |

---

## Executive Briefing & Context (Last 14 Days)

Over the past two weeks (July 1 – July 14, 2026), discussions between Google and Acme Corp focused on **capacity scaling**, **M4 instance family ramp planning**, **C4D quota grants for high-scale testing**, **Load Balancing/WAF migrations**, and **External IP CIDR Block Draining / Internal VPC Migration**.

> [!IMPORTANT]
> **Primary Meeting Goals Today**:
>
> 1. Resolve the blocking information gap on the **M4 Ramp Plan (Bug 123456789)** so GCP Capacity Engineering can complete the formal capacity risk assessment before August 2026.
> 2. Provide guidance on **External IP CIDR Block Deprecation & Draining** for Acme Corp's transition to private internal VPC IPs.

---

## Open Issues & Architectural Blockers

### 1. [BLOCKED] M4 Ramp Plan Capacity Risk Assessment (`acme-scylla-s0027`)

- **Buganizer Ticket**: [b/123456789](https://buganizer.corp.google.com/issues/123456789) | **Horizon Demand ID**: `RDR99999999` | **Classification**: `[Internal Only]`
- **Project**: `project-acme-prod-123` (`us-west1-c`)
- **Ramp Schedule**:
  - **Aug 2026**: 15,725 vCPUs | 204.02 TiB RAM
  - **Sep 2026**: 15,859 vCPUs | 205.76 TiB RAM
  - **Oct 2026**: 15,859 vCPUs | 205.76 TiB RAM
  - **Nov 2026**: 16,397 vCPUs | 213.00 TiB RAM
- **Root Cause of Blocker**:
  On July 13, GCP Capacity Engineering (`capacity-eng@google.com`) flagged that the risk assessment cannot proceed because Acme Corp has not specified the **exact machine shapes** required.
- **Missing Inputs Needed from Customer**:
  1. Specific VM machine shapes (e.g., `m4-hypermem-16`, `m1-ultramem-160`, or custom instance configurations).
  2. Total VM instance count vs. total vCPU multiplier for the Central Capacity Assessment (CCA).

---

### 2. [OPEN DESIGN] Reserved External IP CIDR Block Draining & Internal VPC Migration

- **Document Reference**: [Acme Corp External IP Draining Guide](https://docs.google.com/document/d/abcdef123456789/edit) | **Classification**: `[Internal Only]`
- **Problem Statement**:
  Acme Corp is modifying its architecture to migrate VMs to private internal VPC IPs and wants to remove/release unused reserved external IP CIDR blocks. However, active VMs remain assigned to IPs inside these blocks, and Acme Corp lacks an automated discovery mechanism to identify in-use IPs and safely drain them without disrupting active services.
- **Validated Solution Workflow**:
  1. Automated discovery of external IP attachments using `gcloud compute addresses list --filter="addressType=EXTERNAL"`.
  2. Python `ipaddress` script filtering to correlate active VM bindings against target CIDR blocks scheduled for release.

---

### 3. [RESOLVED] High-Scale Testing C4D Quota Increase (`acme-scylla-s0028`)

- **Buganizer Ticket**: [b/987654321](https://buganizer.corp.google.com/issues/987654321) | **Classification**: `[Internal Only]`
- **Status**: **Fixed / Granted** (July 13, 2026)
- **Approved Details**:
  - C4D core quota bumped to **2,304 vCPUs**.
  - Key Deployment Requirement: Acme Corp must deploy strictly in **`us-west1-a` (Zone A)**.
- **Operational Risk / Warning**:
  > [!WARNING]
  > This quota allocation was performed in an **on-demand capacity pool**. If customer requires strict guarantees against host starvation or preemption during large test runs, capacity reservations (KDA) must be executed.

---

## Expected Q&A & Validated Solutions

| #      | Question / Topic                                                                                      | Validated Answer & Position                                                                                                                                                                             | Source & Classification                                                                                             | Key Contacts              |
| :----- | :---------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :------------------------------------------------------------------------------------------------------------------ | :------------------------ |
| **Q1** | _What is holding up the M4 Ramp risk assessment for Aug–Nov 2026?_                                    | GCP Capacity Engineering needs customer to confirm exact VM shapes (e.g., `m4-hypermem-16`). Once shape list is provided, capacity eng can complete the risk assessment immediately.                    | [b/123456789](https://buganizer.corp.google.com/issues/123456789) `[Internal Only]`                                 | `capacity-eng@google.com` |
| **Q2** | _How can customer safely identify and drain active external IPs in CIDR blocks targeted for removal?_ | We have authored an automated Python filtering script and `gcloud` workflow in [Google Doc Sample](https://docs.google.com/document/d/abcdef123456789/edit) to audit active IP bindings per CIDR block. | [Doc Link](https://docs.google.com/document/d/abcdef123456789/edit) `[Internal Only]`                               | `ce-lead@google.com`      |
| **Q3** | _What machine shapes and memory configurations are supported in the M4 instance family?_              | M4 machine family supports high-memory configurations up to 16 vCPUs to 160 vCPUs with up to 1.5 TB memory, optimized for memory-intensive enterprise workloads.                                        | [Compute Engine M4 Docs](https://cloud.google.com/compute/docs/general-purpose-machines#m4_series) `[Public]`       | `ce-lead@google.com`      |
| **Q4** | _What is the status of the C4D quota request for load testing?_                                       | The quota has been approved and granted up to **2,304 C4D vCPUs**. Customer must target **`us-west1-a`** for deployment.                                                                                | [b/987654321](https://buganizer.corp.google.com/issues/987654321) `[Internal Only]`                                 | `capacity-eng@google.com` |
| **Q5** | _Are C4D test instances guaranteed to spin up on demand?_                                             | On-demand quota is allocated, but guarantees require formal capacity reservations (KDA). If strict SLA guarantees are needed for load test dates, place a reservation.                                  | [Compute Engine Reservations](https://cloud.google.com/compute/docs/instances/reserving-zonal-resources) `[Public]` | `tam-lead@google.com`     |

---

## Action Item Checklist for Meeting

- [ ] **Unblock M4 Ramp**: Prompt customer team to specify exact M4 machine shapes for `acme-scylla-s0027`.
- [ ] **Discuss IP CIDR Draining**: Review the external IP discovery script ([Doc Link](https://docs.google.com/document/d/abcdef123456789/edit)) for draining legacy external CIDRs as customer moves to internal VPC IPs.
- [ ] **Confirm Zone Target for C4D**: Remind customer team that C4D capacity for load testing is provisioned in `us-west1-a`.
- [ ] **Review Bi-Weekly Deck**: Sync on updated 2026-12 demand forecasts in [go/acme-sync-deck](https://docs.google.com/presentation/d/1234567890abcdefghijklmnopqrstuvwxyz/edit).

---

## Key References & Document Directory

### 📄 Google Docs & Specifications

- [Acme Corp External IP Draining Guide](https://docs.google.com/document/d/abcdef123456789/edit) `[Internal Only]` — _Guide & Python script for identifying and draining active external IPs in reserved CIDR blocks._
- [Acme Corp LB/WAF Migration Doc](https://docs.google.com/document/d/123456789abcdef/edit) `[Internal Only]` — _Design doc for regional L7 Load Balancing and Cloud Armor migration._

### 🎨 Slides & Presentations

- [Acme Corp BiWeekly Deck (go/acme-sync-deck)](https://docs.google.com/presentation/d/1234567890abcdefghijklmnopqrstuvwxyz/edit) `[Internal Only]` — _Bi-weekly sync presentation deck and demand roadmap._

### 🐛 Buganizer & Horizon Capacity Tickets

- [b/123456789: M4 Ramp - Acme Corp](https://buganizer.corp.google.com/issues/123456789) `[Internal Only]` — _Horizon capacity request RDR99999999 for M4 ramp plan (Aug–Nov 2026)._
- [b/987654321: Load Testing C4D - Acme Corp](https://buganizer.corp.google.com/issues/987654321) `[Internal Only]` — _Capacity request for load testing (C4D quota granted: 2,304 vCPUs in us-west1-a)._

### 💬 Workspace Communication Threads

- [Calendar Invite: Acme Corp + GCP Sync](https://mail.google.com/mail/) `[Internal Only]` — _Meeting invite & attendee list._

### 🌐 Official Public Documentation

- [Compute Engine M4 Series Machine Types](https://cloud.google.com/compute/docs/general-purpose-machines#m4_series) `[Public]` — _Public documentation on M4 machine specs, vCPU counts, and memory limits._
- [Reserving Zonal Resources](https://cloud.google.com/compute/docs/instances/reserving-zonal-resources) `[Public]` — _Public guide on zonal capacity reservations (KDAs)._
