# 📜 Architecture Decision Record (ADR)

**Document Version:** 1.0  
**Date Generated:** {{ timestamp }}  
**Status:** {% if ciso_approved %}🟢 APPROVED BY SEC AGENT{% else %}⚠️ PENDING HUMAN ESCALATION{% endif %}

---

## 🏢 Customer Profile & Scoping

| Field                    | Value                         |
| :----------------------- | :---------------------------- |
| **Customer Name**        | {{ customer_name }}           |
| **Industry Vertical**    | {{ industry_vertical }}       |
| **Area of Technology**   | `{{ area_of_tech }}`          |
| **Deployment Size**      | `{{ deployment_size }}`       |
| **Primary Priority**     | **{{ customer_priority }}**   |
| **Governing Compliance** | `{{ compliance_frameworks }}` |

---

## 🎯 Business Requirements & Scope

- **Business Requirements:**
  > [!NOTE]
  > {{ business_requirements }}
- **Overall Architecture Goal:**  
  _{{ overall_goal }}_

---

## 🎯 Executive Summary

{{ executive_summary }}

---

## 🏗️ System Architecture & Design

Below is the visualized target-state design topology showing the selected components and flow:

```mermaid
{{ architecture_diagram_mermaid }}
```

---

## 🔧 Architectural Decisions

{% for group in decisions %}

### Decision Group: {{ group.group_name }}

**Core Discovery Question:**  
_{{ group.discovery_question }}_

**Chosen Option:**  
`{{ group.selected_option_id }}`: **{{ group.selected_option_text }}**

- **Governing Rules & Benchmarks:**
  {{ group.rules_formatted }}
- **Architectural Trade-offs (Cons):**  
  _{{ group.cons }}_
- **Business Justification / Technical Rationale:**
  > [!NOTE]
  > **Human CE Input:** {{ group.justification }}

{% if group.is_override %}

> [!WARNING]
> **Heuristic Override Warning:** This selection overrides the standard WAF-recommended option for a `{{ deployment_size }}` deployment prioritizing `{{ customer_priority }}`.
> {% endif %}

{% if group.warning_triggered %}

> [!IMPORTANT]
> **Priority Alignment Alert:**  
> _{{ group.warning_text }}_
> {% endif %}

---

{% endfor %}

## 🛡️ Security Agent Evaluation & Risk Governance

### Critique Status: {% if ciso_approved %}🟢 PASS{% else %}🔴 FAIL (PENDING HUMAN ESCALATION){% endif %}

{% if ciso_approved %}

> [!TIP]
> **Security Agent Seal of Approval:** This design has passed all Heuristic Override Audits, Risk Compensation Analysis, and Priority Warning Enforcement. The documented justifications are deemed sufficient and compliant with governing standards.
> {% else %}
> [!CAUTION]
> **⚠️ SECURITY EXCEPTION WARNING:**  
> The design contains active heuristic overrides or risk factors that require security review or manual customer sign-off.
>
> **Security Evaluation Report:**
> {{ ciso_report }}
> {% endif %}

---

_Document authored by Gemini 3.1 Pro Solutions Architect Plane and validated by Principal Security Agent._
