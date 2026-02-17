# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for repository pattern implementations."""
from __future__ import annotations

from uuid import uuid4

import pytest

from data_catalog.db.models import Asset, Relationship
from data_catalog.db.repositories import (
    AssetRepository,
    RelationshipRepository,
)


class TestAssetRepository:
    """Tests for AssetRepository."""

    def _make_asset(self, schema="dbo", name="Test", **kwargs):
        return Asset(
            id=str(uuid4()),
            qualified_name=f"[{schema}].[{name}]",
            table_schema=schema,
            table_name=name,
            asset_type=kwargs.get("asset_type", "table"),
            source_system="test",
            schema_metadata=kwargs.get("schema_metadata"),
            statistics=kwargs.get("statistics"),
        )

    def test_find_by_qualified_name(self, db):
        repo = AssetRepository(db)
        asset = self._make_asset()
        db.add(asset)
        db.commit()

        found = repo.find_by_qualified_name("[dbo].[Test]")
        assert found is not None
        assert found.qualified_name == "[dbo].[Test]"

    def test_find_by_qualified_name_not_found(self, db):
        repo = AssetRepository(db)
        assert repo.find_by_qualified_name("[dbo].[Missing]") is None

    def test_find_by_schema_pattern(self, db):
        repo = AssetRepository(db)
        db.add_all([
            self._make_asset("dbo", "A"),
            self._make_asset("dbo", "B"),
            self._make_asset("staging", "C"),
        ])
        db.commit()

        results = repo.find_by_schema_pattern("dbo")
        assert len(results) == 2

    def test_find_all(self, db):
        repo = AssetRepository(db)
        db.add_all([
            self._make_asset("dbo", "X"),
            self._make_asset("dbo", "Y"),
        ])
        db.commit()

        results = repo.find_all()
        assert len(results) == 2

    def test_find_all_with_limit(self, db):
        repo = AssetRepository(db)
        for i in range(5):
            db.add(self._make_asset("dbo", f"T{i}"))
        db.commit()

        results = repo.find_all(limit=3)
        assert len(results) == 3

    def test_find_by_id(self, db):
        repo = AssetRepository(db)
        asset = self._make_asset()
        db.add(asset)
        db.commit()

        found = repo.find_by_id(asset.id)
        assert found is not None
        assert found.id == asset.id


class TestRelationshipRepository:
    """Tests for RelationshipRepository."""

    def test_find_by_asset(self, db):
        repo = RelationshipRepository(db)

        a1 = Asset(
            id=str(uuid4()), qualified_name="[dbo].[A]",
            table_schema="dbo", table_name="A",
            asset_type="table", source_system="test",
        )
        a2 = Asset(
            id=str(uuid4()), qualified_name="[dbo].[B]",
            table_schema="dbo", table_name="B",
            asset_type="table", source_system="test",
        )
        db.add_all([a1, a2])
        db.commit()

        rel = Relationship(
            id=str(uuid4()),
            parent_asset_id=a1.id,
            referenced_asset_id=a2.id,
            relationship_type="foreign_key",
            column_mappings=[{"parent": "BID", "referenced": "ID"}],
        )
        db.add(rel)
        db.commit()

        # Find from parent side
        results = repo.find_by_asset(a1.id)
        assert len(results) == 1
        assert results[0].parent_asset_id == a1.id

        # Find from child side
        results = repo.find_by_asset(a2.id)
        assert len(results) == 1
