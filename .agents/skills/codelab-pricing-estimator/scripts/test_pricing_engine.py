#!/usr/bin/env python3
"""
Unit Test Suite for Universal Codelab Pricing Estimator.

Verifies mathematical calculations across Compute, Storage, SQL, GKE, Networking,
Vertex AI, Cloud Run, and Universal assets, while strictly asserting zero indentation
across all lines of generated HTML table reports.
"""

import os
import sys

# Dynamically resolve current script path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import billing_client
import cost_engine


def test_compute_pricing():
    rate = billing_client.get_compute_price("e2-medium", "us-central1")
    assert rate > 0.0, f"Expected positive rate for e2-medium, got {rate}"
    print("✅ Compute instance pricing tests passed.")


def test_disk_pricing():
    cost = billing_client.get_disk_price("pd-ssd", 100, "us-central1")
    assert cost > 0.0, f"Expected positive disk cost, got {cost}"
    print("✅ Persistent disk pricing tests passed.")


def test_sql_pricing():
    rate = billing_client.get_sql_price("db-f1-micro", "us-central1")
    assert rate > 0.0, f"Expected positive SQL cost, got {rate}"
    print("✅ Cloud SQL pricing tests passed.")


def test_gke_pricing():
    cost = billing_client.get_gke_price(3, "e2-medium", "us-central1", "RUNNING")
    assert cost > 0.10, f"Expected cost greater than cluster fee, got {cost}"
    print("✅ GKE cluster pricing tests passed.")


def test_networking_pricing():
    swp = billing_client.get_networking_price("swp_gateway", 2)
    assert swp == 0.1600, f"Expected 0.1600, got {swp}"

    fw = billing_client.get_networking_price("firewall_endpoint", 1)
    assert fw == 1.2500, f"Expected 1.2500, got {fw}"

    vpn = billing_client.get_networking_price("vpn_gateway", 2)
    assert vpn == 0.1000, f"Expected 0.1000, got {vpn}"

    fwd = billing_client.get_networking_price("forwarding_rule", 6)
    expected_fwd = (5 * 0.0250) + (1 * 0.0100)
    assert abs(fwd - expected_fwd) < 1e-6, f"Expected {expected_fwd}, got {fwd}"
    print("✅ Networking & Security pricing tests passed.")


def test_vertex_pricing():
    idx = billing_client.get_vertex_price("index_endpoint", node_count=2)
    assert idx == 0.1680, f"Expected 0.1680, got {idx}"

    mdl = billing_client.get_vertex_price(
        "model_endpoint", machine_type="n1-standard-4", node_count=2
    )
    assert mdl > 0.0, f"Expected positive model endpoint cost, got {mdl}"
    print("✅ Vertex AI pricing tests passed.")


def test_cloudrun_pricing():
    idle = billing_client.get_cloud_run_price(min_instances=0)
    assert idle == 0.0, f"Expected 0.0 for 0 min instances, got {idle}"

    active = billing_client.get_cloud_run_price(
        min_instances=2, vcpu=1.0, memory_gb=0.5
    )
    expected = 2 * (1.0 * 0.0864 + 0.5 * 0.0090)
    assert abs(active - expected) < 1e-6, f"Expected {expected}, got {active}"
    print("✅ Cloud Run continuous pricing tests passed.")


def test_universal_pricing():
    redis = billing_client.get_universal_fallback_price("redis.googleapis.com/Instance")
    assert redis == 0.0490, f"Expected 0.0490, got {redis}"
    spanner = billing_client.get_universal_fallback_price(
        "spanner.googleapis.com/Instance"
    )
    assert spanner == 0.9000, f"Expected 0.9000, got {spanner}"
    print("✅ Universal catch-all pricing tests passed.")


def test_html_table_formatting():
    mock_resources = [
        {
            "name": "swp-prod",
            "type": "Networking / Security",
            "status": "ACTIVE",
            "config": "Secure Web Proxy Gateway",
            "location": "us-central1",
            "hourly_cost": 0.0800,
        },
        {
            "name": "api-run",
            "type": "Cloud Run Service",
            "status": "ALLOCATED",
            "config": "Min Instances: 2 (1.0 vCPU, 0.50 GB)",
            "location": "us-central1",
            "hourly_cost": 0.1818,
        },
    ]
    html = cost_engine.format_html_table(mock_resources)
    assert "<div style=" in html, "Table must be wrapped in outer container"
    assert "<table" in html, "Table tag missing"

    for line in html.split("\n"):
        assert not line.startswith(" "), f"Leading space indentation found: {line!r}"
        assert not line.startswith("\t"), f"Leading tab indentation found: {line!r}"
    print("✅ Strict zero-indentation HTML formatting test passed.")


def main():
    print("🧪 Running Universal Codelab Pricing Estimator Test Suite...\n")
    test_compute_pricing()
    test_disk_pricing()
    test_sql_pricing()
    test_gke_pricing()
    test_networking_pricing()
    test_vertex_pricing()
    test_cloudrun_pricing()
    test_universal_pricing()
    test_html_table_formatting()
    print("\n🎉 ALL DEEP VERIFICATION TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
