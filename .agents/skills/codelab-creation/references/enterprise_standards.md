# Enterprise Codelab Standards

This reference guide outlines the standards for elevating codelabs to an enterprise-ready level, based on lessons learned from advanced load balancing codelabs.

## 1. Lead with the Business Problem

- **Pattern**: Do not just describe a feature. Frame the codelab around a concrete enterprise scenario.
- **Examples**:
  - _Instead of_: "How to configure SNI routing."
  - _Use_: "How a SaaS provider can route hundreds of customer vanity domains through a single load balancer without managing their SSL certificates."
- **Goal**: Give the user a compelling reason to care and understand the real-world value.

## 2. Include Stateful Reliability

- **Pattern**: For TCP/UDP traffic, always consider session stability.
- **Do this**: Implement **Maglev consistent hashing** (or similar session persistence mechanisms) when configuring load balancer backend services for stateful workloads.
- **Goal**: Teach users how to build production-ready, resilient architectures, not just toy examples.

## 3. Implement "Negative Testing" for Zero-Trust

- **Pattern**: Security validation must prove what _cannot_ happen as much as what _can_.
- **Do this**: Include verification steps for **unregistered domains** or unauthorized access attempts to prove that traffic is actively dropped or blocked.
- **Goal**: Validate the security posture of the infrastructure.

## 4. Operational Guardrails

- **Pattern**: Anticipate common engineering mistakes and provide explicit warnings.
- **Do this**: Include callouts (Negative Notes) for known gotchas, such as mutual exclusivity of configurations in Envoy (e.g., Target TCP Proxy cannot have both a default backend and a `TLSRoute` for SNI steering).
- **Goal**: Save users hours of debugging time by pointing out non-obvious constraints.

## 5. Modern Infrastructure Patterns

- **Pattern**: Avoid legacy anti-patterns.
- **Do this**: Use **Instance Templates** and **Managed Instance Groups (MIGs)** instead of raw VM creation commands and unmanaged instance groups.
- **Goal**: Teach modern infrastructure-as-code habits.
