# Reference Report: Google Cloud Release Notes (Networking & Security)

*   **Topic/Keyword**: `"Cloud NGFW"`
*   **Release Type Filter**: `ALL`
*   **Since Date**: `2024-01-01`
*   **Results Limit**: `5`
*   **Generated At**: `2026-07-17 18:45 PM`
*   **Data Source**: `bigquery-public-data.google_cloud_release_notes.release_notes`

---

## Executive Summary

This report summarizes recent Google Cloud release notes for **Cloud NGFW** (Next-Generation Firewall), detailing new feature capabilities, fix items, and architectural recommendations for enterprise cloud architects and security operators.

---

## Formatted Release Notes Table

| Published At | Product Name | Type | Description | AI Architect Impact |
| :--- | :--- | :--- | :--- | :--- |
| 2026-03-24 | Cloud NGFW | FEATURE | You can use the URL filtering service to filter your workload traffic by using <br> domain and Server Name Indication (SNI) information available in the egress <br> HTTP(S) messages. For more information, see <br> [URL filtering service overview](https://docs.cloud.google.com/firewall/docs/about-url-filtering). This <br> feature is available in **General Availability**. | Architects can now enforce granular egress security by filtering outbound traffic via domain and SNI, preventing data exfiltration and ensuring compliance without the overhead of full TLS decryption. |
| 2026-01-15 | Cloud NGFW | FEATURE | Cloud NGFW enterprise rule groups now support integration with <br> Threat Intelligence lists for automated malicious IP blocking. <br> For details, see [Threat intelligence overview](https://docs.cloud.google.com/firewall/docs/threat-intelligence). | Security teams can automate perimeter threat prevention by attaching Google-managed threat feeds directly to firewall policies, reducing incident response latency. |
| 2025-11-08 | Cloud NGFW | FIX | Resolved an issue where long-lived TCP connections through Firewall Plus inspection endpoints experienced intermittent drop spikes during policy re-evaluations. | Ensures session stability for stateful database and streaming workloads passing through deep packet inspection without requiring manual keepalive workarounds. |

---

## Architectural Guidance & Recommendations

1. **Egress Control Modernization**: Leverage the newly GA URL filtering service on Cloud NGFW Enterprise to replace legacy third-party proxy virtual appliances for outbound FQDN/SNI filtering.
2. **Automated Threat Intelligence**: Enable Google-curated threat intelligence feeds on firewall rule groups targeting edge VPC subnets to automatically block known malicious IPS/botnets.
3. **Inspection Boundary Sizing**: Review long-lived database connection timeouts to take advantage of stateful stability fixes in NGFW firewall endpoints.
