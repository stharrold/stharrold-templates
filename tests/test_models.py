# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for SQLAlchemy ORM models."""
from __future__ import annotations

from uuid import uuid4

import pytest

from data_catalog.db.models import (
    Asset,
    AuditLog,
    ColumnCardinalityHistory,
    ColumnValueFrequency,
    ColumnVector,
    GlossaryTerm,
    Relationship,
    SearchIndexColumn,
)


class TestAssetModel:
    """Tests for the Asset model."""

    def test_create_asset(self, db):
        asset = Asset(
            id=str(uuid4()),
            qualified_name="[dbo].[Customers]",
            table_schema="dbo",
            table_name="Customers",
            asset_type="table",
            source_system="test",
        )
        db.add(asset)
        db.commit()

        loaded = db.query(Asset).filter(
            Asset.qualified_name == "[dbo].[Customers]"
        ).first()
        assert loaded is not None
        assert loaded.table_schema == "dbo"
        assert loaded.table_name == "Customers"
        assert loaded.asset_type == "table"

    def test_asset_schema_metadata(self, db):
        asset = Asset(
            id=str(uuid4()),
            qualified_name="[dbo].[Orders]",
            table_schema="dbo",
            table_name="Orders",
            asset_type="table",
            source_system="test",
            schema_metadata={
                "columns": [
                    {"name": "OrderID", "data_type": "int"},
                    {"name": "CustomerID", "data_type": "int"},
                ],
                "primary_key": ["OrderID"],
                "grain_status": "confirmed",
            },
        )
        db.add(asset)
        db.commit()

        loaded = db.query(Asset).first()
        assert loaded.schema_metadata["primary_key"] == ["OrderID"]
        assert loaded.schema_metadata["grain_status"] == "confirmed"
        assert len(loaded.schema_metadata["columns"]) == 2

    def test_asset_statistics(self, db):
        asset = Asset(
            id=str(uuid4()),
            qualified_name="[dbo].[Products]",
            table_schema="dbo",
            table_name="Products",
            asset_type="table",
            source_system="test",
            statistics={"row_count": 1000000},
        )
        db.add(asset)
        db.commit()

        loaded = db.query(Asset).first()
        assert loaded.statistics["row_count"] == 1000000


class TestRelationshipModel:
    """Tests for the Relationship model."""

    def test_create_relationship(self, db):
        parent = Asset(
            id=str(uuid4()),
            qualified_name="[dbo].[Orders]",
            table_schema="dbo",
            table_name="Orders",
            asset_type="table",
            source_system="test",
        )
        child = Asset(
            id=str(uuid4()),
            qualified_name="[dbo].[Customers]",
            table_schema="dbo",
            table_name="Customers",
            asset_type="table",
            source_system="test",
        )
        db.add_all([parent, child])
        db.commit()

        rel = Relationship(
            id=str(uuid4()),
            parent_asset_id=parent.id,
            referenced_asset_id=child.id,
            relationship_type="foreign_key",
            column_mappings=[
                {"parent": "CustomerID", "referenced": "CustomerID"}
            ],
            is_validated=True,
        )
        db.add(rel)
        db.commit()

        loaded = db.query(Relationship).first()
        assert loaded.parent_asset_id == parent.id
        assert loaded.referenced_asset_id == child.id
        assert loaded.is_validated is True
        assert len(loaded.column_mappings) == 1


class TestColumnModels:
    """Tests for column-related models."""

    def test_column_cardinality(self, db):
        asset = Asset(
            id=str(uuid4()),
            qualified_name="[dbo].[Orders]",
            table_schema="dbo",
            table_name="Orders",
            asset_type="table",
            source_system="test",
        )
        db.add(asset)
        db.commit()

        record = ColumnCardinalityHistory(
            cardinality_id=str(uuid4()),
            asset_id=asset.id,
            table_schema="dbo",
            table_name="Orders",
            column_name="CustomerID",
            ordinal_position=2,
            discovery_method="test",
            cardinality_at_1pct=500,
            selectivity_at_1pct=50.0,
        )
        db.add(record)
        db.commit()

        loaded = db.query(ColumnCardinalityHistory).first()
        assert loaded.column_name == "CustomerID"
        assert loaded.cardinality_at_1pct == 500

    def test_column_frequency(self, db):
        asset = Asset(
            id=str(uuid4()),
            qualified_name="[dbo].[Orders]",
            table_schema="dbo",
            table_name="Orders",
            asset_type="table",
            source_system="test",
        )
        db.add(asset)
        db.commit()

        freq = ColumnValueFrequency(
            id=str(uuid4()),
            asset_id=asset.id,
            table_schema="dbo",
            table_name="Orders",
            column_name="Status",
            rank=1,
            value="Active",
            frequency=5000,
            sample_pct=10.0,
        )
        db.add(freq)
        db.commit()

        loaded = db.query(ColumnValueFrequency).first()
        assert loaded.value == "Active"
        assert loaded.frequency == 5000

    def test_column_vector(self, db):
        asset = Asset(
            id=str(uuid4()),
            qualified_name="[dbo].[Orders]",
            table_schema="dbo",
            table_name="Orders",
            asset_type="table",
            source_system="test",
        )
        db.add(asset)
        db.commit()

        vector = ColumnVector(
            id=str(uuid4()),
            asset_id=asset.id,
            table_schema="dbo",
            table_name="Orders",
            column_name="CustomerID",
            vector_type="semantic_value",
            value_vector=[0.1] * 384,
            vector_bits="0" * 384,
        )
        db.add(vector)
        db.commit()

        loaded = db.query(ColumnVector).first()
        assert loaded.vector_type == "semantic_value"
        assert len(loaded.value_vector) == 384

    def test_search_index_column(self, db):
        asset = Asset(
            id=str(uuid4()),
            qualified_name="[dbo].[Orders]",
            table_schema="dbo",
            table_name="Orders",
            asset_type="table",
            source_system="test",
        )
        db.add(asset)
        db.commit()

        entry = SearchIndexColumn(
            id=str(uuid4()),
            asset_id=asset.id,
            table_schema="dbo",
            table_name="Orders",
            column_name="CustomerID",
            data_type="int",
            ordinal_position=2,
            description="FK to Customers table",
        )
        db.add(entry)
        db.commit()

        loaded = db.query(SearchIndexColumn).first()
        assert loaded.description == "FK to Customers table"
