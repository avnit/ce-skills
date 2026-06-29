#!/usr/bin/env python3
"""
Local JSON TTL Caching Module for Google Cloud Billing Catalog API.
Ensures sub-5ms pricing lookups without repetitive network requests.
"""

import json
import os
import sys
import time
from typing import Dict, Any, Optional

CACHE_TTL_SECONDS = 86400  # 24 hours


class CatalogCache:
    """Manages local JSON TTL cache for pricing catalog data."""

    def __init__(self, cache_dir: Optional[str] = None):
        if not cache_dir:
            env_dir = os.environ.get("ANTIGRAVITY_EXECUTABLE_DATA_DIR")
            if env_dir and os.path.exists(env_dir):
                cache_dir = os.path.join(env_dir, "sku_cache")
            else:
                default_sidecar = "/usr/local/google/home/shacharb/.gemini/jetski/sidecar_data/sku_cache"
                if os.path.exists("/usr/local/google/home/shacharb/.gemini/jetski/sidecar_data"):
                    cache_dir = default_sidecar
                else:
                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    cache_dir = os.path.join(base_dir, "cache")
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(self.cache_dir, "gcp_catalog.json")
        self.cache_status = "MISS"
        self.lookup_time_ms = 0.0

    def load(self, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Loads cached catalog if valid (<24h TTL). Returns dict if successful."""
        start_time = time.perf_counter()
        if not force_refresh and os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                timestamp = data.get("timestamp", 0)
                if time.time() - timestamp < CACHE_TTL_SECONDS:
                    self.cache_status = "HIT"
                    self.lookup_time_ms = (time.perf_counter() - start_time) * 1000.0
                    return data.get("catalog")
            except Exception as e:
                sys.stderr.write(f"⚠️ Warning: Failed reading cache file {self.cache_file}: {e}\n")
        self.cache_status = "MISS"
        self.lookup_time_ms = (time.perf_counter() - start_time) * 1000.0
        return None

    def save(self, catalog_data: Dict[str, Any]) -> None:
        """Persists catalog data to local JSON cache file."""
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            payload = {
                "timestamp": time.time(),
                "catalog": catalog_data,
            }
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception as e:
            sys.stderr.write(f"⚠️ Warning: Failed saving cache to {self.cache_file}: {e}\n")
