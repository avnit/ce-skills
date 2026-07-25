#!/usr/bin/env python3
"""Unit test suite for CloudBlockerQueryBuilder.
Verifies proper GoogleSQL WHERE clause compilation and strict PST product scoping.
"""

import sys
import unittest
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).resolve().parents[1] / "scripts"
sys.path.append(str(scripts_dir))

from query_builder import CloudBlockerQueryBuilder  # noqa: E402


class DummyArgs:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestCloudBlockerQueryBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = CloudBlockerQueryBuilder(limit=50)

    def test_pst_area_strict_scoping(self):
        """Verify --pst-area scopes strictly to PST hierarchy fields and does NOT match cr_title/cb_title."""
        args = DummyArgs(pst_area="Networking")
        where_clause = self.builder.build_where_clause(args)

        self.assertIn("pst_owning_product_group", where_clause)
        self.assertIn("pst_display_name", where_clause)
        self.assertIn("owning_super_product_area", where_clause)
        self.assertIn("pst_owning_execution_area", where_clause)
        # Ensure title matching is excluded from pst_area
        self.assertNotIn("cr_title", where_clause)
        self.assertNotIn("cb_title", where_clause)

    def test_title_keyword_scoping(self):
        """Verify --title-keyword scopes strictly to issue titles."""
        args = DummyArgs(title_keyword="Networking")
        where_clause = self.builder.build_where_clause(args)

        self.assertIn("cr_title", where_clause)
        self.assertIn("cb_title", where_clause)
        self.assertNotIn("pst_owning_product_group", where_clause)

    def test_pst_group_exact_filter(self):
        """Verify --pst-group matches exact PST Product Group."""
        args = DummyArgs(pst_group="Cloud Networking")
        where_clause = self.builder.build_where_clause(args)

        self.assertIn("pst_owning_product_group", where_clause)
        self.assertIn("cloud networking", where_clause)

    def test_account_and_pst_area_combination(self):
        """Verify combination of account and strict pst-area."""
        args = DummyArgs(account="PayPal", pst_area="Networking")
        where_clause = self.builder.build_where_clause(args)

        self.assertIn("account_name", where_clause)
        self.assertIn("pst_owning_product_group", where_clause)
        self.assertIn("AND", where_clause)

    def test_numeric_validation_cr_id(self):
        """Verify invalid non-numeric CR ID raises ValueError."""
        args = DummyArgs(cr_id="abc_invalid")
        with self.assertRaises(ValueError):
            self.builder.build_where_clause(args)


if __name__ == "__main__":
    unittest.main()
