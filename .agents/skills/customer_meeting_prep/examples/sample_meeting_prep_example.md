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

Over the past two weeks, Acme Corp and Google Cloud engineering teams have focused on two critical operational tracks: preparing the infrastructure for Acme Corp's August 2026 M4 workload ramp (~16.3k vCPUs) and resolving external IP CIDR block release constraints.

While technical collaboration remains active, account friction has increased due to unresolved VM machine shape specifications required by the GCP Capacity Engineering team to approve the M4 reservation. Additionally, Acme Corp infrastructure leads have requested automated tools to identify and drain active VM instances from external IP blocks targeted for release.

> [!IMPORTANT]
> **Primary Meeting Goals Today**:
>
> 1. Secure Acme Corp's confirmation on exact VM machine shapes (e.g. `m4-hypermem-16`) to unblock the M4 capacity assessment.
> 2. Present the validated 2-step automated discovery script for reserved external IP CIDR block draining.

---

## Technical Edge-Case Audit & Solution Breakdown

### 1. [BLOCKED] M4 Ramp Machine Shape Specification (`acme-m4-ramp`)

- **Buganizer Ticket**: [b/123456789](https://buganizer.corp.google.com/issues/123456789) | **Classification**: `[Internal Only]`
- **Problem Statement**:
  Acme Corp requested a high-priority capacity reservation for ~16.3k cores of M4 instances in `us-central1` for an August 2026 go-live. However, the request lacks specific machine shape breakdowns (e.g. `m4-hypermem-16` vs custom shapes). Capacity Engineering (`capacity-eng@google.com`) cannot evaluate slot availability or approve the reservation until exact shapes are confirmed.
- **Validated Solution Workflow**:
  1. Confirm specific VM machine shapes (e.g., `m4-hypermem-16`, `m1-ultramem-160`, or custom instance configurations).
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

---

## Executive Q&A & Talking Points Roadmap

| #      | Anticipated Customer Question                                                        | Recommended Google Strategy / Answer                                                                                                                | Supporting Evidence / Link                                                                                        | Google Owner              |
| :----- | :----------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------- | :------------------------ |
| **Q1** | _When will our M4 capacity reservation for August 2026 be approved?_                 | Approval requires exact machine shapes. Once Acme Corp confirms the shape breakdown today, Capacity Eng can finalize slot matching within 48 hours. | [Compute Engine M4 Docs](https://cloud.google.com/compute/docs/general-purpose-machines#m4_series) `[Public]`     | `capacity-eng@google.com` |
| **Q2** | _How can we safely release our reserved external IP blocks without causing outages?_ | Google has validated a 2-step gcloud + Python discovery script to identify all active VM bindings in target blocks before release.                  | [Acme Corp External IP Draining Guide](https://docs.google.com/document/d/abcdef123456789/edit) `[Internal Only]` | `ce-lead@google.com`      |
| **Q3** | _Is our C4D quota sufficient for upcoming performance testing?_                      | Yes, the quota bump to 2,304 vCPUs was approved on July 13 and is active in `us-central1`.                                                          | [b/987654321](https://buganizer.corp.google.com/issues/987654321) `[Internal Only]`                               | `tam-lead@google.com`     |

---

## Recommended Immediate Next Steps

1. [ ] **Machine Shape Confirmation**: Obtain finalized M4 VM shape list from Acme Corp infrastructure lead (`john.smith@acme.example.com`).
2. [ ] **IP Draining Script Handoff**: Deliver the validated gcloud external IP discovery script to Acme Corp network team.
3. [ ] **Follow-Up Sync**: Schedule a 30-minute technical check-in for Friday, July 17, 2026.

---

## Key References & Document Directory

> [!NOTE]
> All document links, chat threads, support cases, and public documentation referenced in this briefing are audited for authenticity.

- **Decks & Slides**: [Acme Corp BiWeekly Sync Deck (go/acme-sync-deck)](https://docs.google.com/presentation/d/1234567890abcdefghijklmnopqrstuvwxyz/edit) `[Internal Only]`
- **Google Docs & Architecture Guides**: [Acme Corp External IP Draining Guide](https://docs.google.com/document/d/abcdef123456789/edit) `[Internal Only]`, [Acme Corp LB/WAF Migration Doc](https://docs.google.com/document/d/123456789abcdef/edit) `[Internal Only]`
- **Buganizer Issues**: [b/123456789: M4 Ramp - Acme Corp](https://buganizer.corp.google.com/issues/123456789) `[Internal Only]`, [b/987654321: Load Testing C4D - Acme Corp](https://buganizer.corp.google.com/issues/987654321) `[Internal Only]`
- **Workspace Email Threads**: [Calendar Invite: Acme Corp + GCP Sync](https://mail.google.com/mail/) `[Internal Only]`
- **Public GCP Documentation**: [Compute Engine M4 Series Machine Types](https://cloud.google.com/compute/docs/general-purpose-machines#m4_series) `[Public]`, [Reserving Zonal Resources](https://cloud.google.com/compute/docs/instances/reserving-zonal-resources) `[Public]`
