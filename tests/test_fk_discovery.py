# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for FK discovery service and patterns."""
from __future__ import annotations

from uuid import uuid4

import pytest

from data_catalog.db.models import Asset
from data_catalog.services.fk_discovery import FKCandidate, FKDiscoveryService
from data_catalog.services.fk_patterns import (
    CompositePattern,
    EntityNamePattern,
    FKPatternRegistry,
    PrefixPattern,
    SameNamePattern,
    SuffixPattern,
)


class TestFKPatterns:
    """Tests for FK pattern matching."""

    def test_same_name_pattern(self):
        pattern = SameNamePattern()
        candidates = pattern.match(
            col_name="CustomerID",
            target_name="[dbo].[Customers]",
            pk_cols=["CustomerID"],
            source_name="[dbo].[Orders]",
        )

        assert len(candidates) == 1
        assert candidates[0].parent_columns == ["CustomerID"]
        assert candidates[0].referenced_columns == ["CustomerID"]
        assert candidates[0].pattern_name == "same_name"

    def test_entity_name_pattern(self):
        pattern = EntityNamePattern()
        candidates = pattern.match(
            col_name="CustomerID",
            target_name="[dbo].[Customer]",
            pk_cols=["ID"],
            source_name="[dbo].[Orders]",
        )

        assert len(candidates) >= 1

    def test_pattern_registry(self):
        registry = FKPatternRegistry()
        registry.register_defaults()

        patterns = registry.get_patterns()
        assert len(patterns) >= 5  # At least 5 built-in patterns

    def test_composite_pattern(self):
        pattern = CompositePattern()
        candidates = pattern.match_composite(
            source_columns=["ReviewID", "OrderID", "ProductID", "Rating"],
            target_name="[dbo].[OrderItems]",
            pk_cols=["OrderID", "ProductID"],
            source_name="[dbo].[ItemReviews]",
        )

        assert len(candidates) == 1
        assert candidates[0].evidence.get("composite_match") is True


class TestFKDiscoveryService:
    """Tests for the FK discovery service."""

    def test_discover_candidates(self, db):
        pk_asset = Asset(
            id=str(uuid4()),
            qualified_name="[dbo].[Customers]",
            table_schema="dbo",
            table_name="Customers",
            asset_type="table",
            source_system="test",
            schema_metadata={
                "primary_key": ["CustomerID"],
                "grain_status": "confirmed",
                "columns": [{"name": "CustomerID"}, {"name": "Name"}],
            },
        )
        fk_asset = Asset(
            id=str(uuid4()),
            qualified_name="[dbo].[Orders]",
            table_schema="dbo",
            table_name="Orders",
            asset_type="table",
            source_system="test",
            schema_metadata={
                "columns": [
                    {"name": "OrderID"},
                    {"name": "CustomerID"},
                    {"name": "Amount"},
                ],
            },
        )
        db.add_all([pk_asset, fk_asset])
        db.commit()

        service = FKDiscoveryService(db)
        candidates = service.discover_candidates(fk_asset)

        assert len(candidates) >= 1
        match = [c for c in candidates if "CustomerID" in c.parent_columns]
        assert len(match) >= 1
