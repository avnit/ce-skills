#!/usr/bin/env python3
"""
Unit Test Suite for Codelab Pricing Estimator Redesign.
Verifies local JSON TTL caching, deterministic composite cost engine calculations, and zero indentation compliance.
"""

import os
import shutil
import tempfile
import unittest
import sys

# Add scripts directory to import path
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"
    ),
)

from cache import CatalogCache
import cost_engine
from report_generator import HTMLReportGenerator


class TestCatalogCache(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.cache = CatalogCache(cache_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_cache_miss_initially(self):
        data = self.cache.load()
        self.assertIsNone(data)
        self.assertEqual(self.cache.cache_status, "MISS")

    def test_cache_hit_after_save(self):
        sample = {"test": 123}
        self.cache.save(sample)
        data = self.cache.load()
        self.assertEqual(data, sample)
        self.assertEqual(self.cache.cache_status, "HIT")

    def test_force_refresh(self):
        sample = {"test": 123}
        self.cache.save(sample)
        data = self.cache.load(force_refresh=True)
        self.assertIsNone(data)
        self.assertEqual(self.cache.cache_status, "MISS")


class TestCostEngine(unittest.TestCase):
    def test_custom_vm_ratio(self):
        details = {"status": "RUNNING", "machine_type": "custom-4-16384"}
        cost = cost_engine.evaluate_resource_cost(
            "Compute Instance", details, "us-central1"
        )
        # 4 * 0.0316 + 16 * 0.0042 = 0.1264 + 0.0672 = 0.1936
        self.assertAlmostEqual(cost, 0.1936, places=4)

    def test_spot_discount(self):
        details_normal = {"status": "RUNNING", "machine_type": "e2-medium"}
        cost_normal = cost_engine.evaluate_resource_cost(
            "Compute Instance", details_normal, "us-central1"
        )

        details_spot = {
            "status": "RUNNING",
            "machine_type": "e2-medium",
            "scheduling": {"provisioningModel": "SPOT"},
        }
        cost_spot = cost_engine.evaluate_resource_cost(
            "Compute Instance", details_spot, "us-central1"
        )
        self.assertAlmostEqual(cost_spot, cost_normal * 0.30, places=4)

    def test_gpu_attachment(self):
        gpus = [
            {
                "acceleratorType": "projects/p/zones/z/acceleratorTypes/nvidia-tesla-t4",
                "acceleratorCount": 2,
            }
        ]
        details = {"status": "RUNNING", "machine_type": "e2-medium", "gpus": gpus}
        cost = cost_engine.evaluate_resource_cost(
            "Compute Instance", details, "us-central1"
        )
        self.assertAlmostEqual(cost, 0.0335 + (2 * 0.350), places=4)

    def test_disk_pricing(self):
        details = {"disk_type": "hyperdisk-extreme", "size_gb": 100}
        cost = cost_engine.evaluate_resource_cost(
            "Persistent Disk", details, "us-central1"
        )
        expected = 100 * (0.500 / 730.0)
        self.assertAlmostEqual(cost, expected, places=4)

    def test_sql_ha_doubling(self):
        details_zonal = {
            "status": "RUNNING",
            "tier": "db-custom-2-7680",
            "availability_type": "ZONAL",
        }
        cost_zonal = cost_engine.evaluate_resource_cost(
            "Cloud SQL Database", details_zonal, "us-central1"
        )

        details_ha = {
            "status": "RUNNING",
            "tier": "db-custom-2-7680",
            "availability_type": "REGIONAL",
        }
        cost_ha = cost_engine.evaluate_resource_cost(
            "Cloud SQL Database", details_ha, "us-central1"
        )
        self.assertAlmostEqual(cost_ha, cost_zonal * 2.0, places=4)


class TestHTMLReportGenerator(unittest.TestCase):
    def test_zero_indentation(self):
        resources = [
            {
                "name": "vm-1",
                "type": "Compute Instance",
                "status": "RUNNING",
                "config": "Machine: e2-medium",
                "location": "us-central1-a",
                "hourly_cost": 0.0335,
            }
        ]
        report = HTMLReportGenerator.generate(
            "test-proj", resources, 0.0335, "HIT", 1.25, "static_fallback"
        )
        for i, line in enumerate(report.split("\n")):
            if "<" in line and ">" in line:
                self.assertFalse(
                    line.startswith(" "),
                    f"Line {i + 1} has leading spaces: {repr(line)}",
                )
                self.assertFalse(
                    line.startswith("\t"),
                    f"Line {i + 1} has leading tabs: {repr(line)}",
                )


if __name__ == "__main__":
    unittest.main()
