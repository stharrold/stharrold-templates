# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for grain discovery service (pattern-based, no source DB)."""
from __future__ import annotations

from uuid import uuid4

import pytest

from data_catalog.db.models import Asset
from data_catalog.models.data_model import GrainResult


class TestGrainResult:
    """Tests for the GrainResult dataclass."""

    def test_grain_result_with_pk(self):
        result = GrainResult(
            qualified_name="[dbo].[Orders]",
            status="confirmed",
            primary_key=["OrderID"],
            method="pattern",
        )
        assert result.primary_key == ["OrderID"]
        assert result.method == "pattern"
        assert result.pk_minimal is None

    def test_grain_result_no_pk(self):
        result = GrainResult(
            qualified_name="[dbo].[Logs]",
            status="no_natural_pk",
            primary_key=None,
            method="no-pk",
        )
        assert result.primary_key is None
        assert result.method == "no-pk"

    def test_grain_result_with_fd_minimal(self):
        result = GrainResult(
            qualified_name="[dbo].[Orders]",
            status="confirmed",
            primary_key=["PostPeriod", "ExtractDTS", "OrderID"],
            method="iterative-accumulation",
            pk_minimal=["PostPeriod", "OrderID"],
            fd_removed=["ExtractDTS"],
        )
        assert result.pk_minimal == ["PostPeriod", "OrderID"]
        assert result.fd_removed == ["ExtractDTS"]

    def test_grain_result_composite(self):
        result = GrainResult(
            qualified_name="[dbo].[OrderItems]",
            status="confirmed",
            primary_key=["OrderID", "ProductID"],
            method="progressive-scan",
        )
        assert len(result.primary_key) == 2


class TestGrainDiscoveryPatterns:
    """Tests for grain discovery pattern matching (offline only)."""

    def test_asset_with_existing_pk(self, db):
        """Assets with PK in schema_metadata should be returned directly."""
        asset = Asset(
            id=str(uuid4()),
            qualified_name="[dbo].[Customers]",
            table_schema="dbo",
            table_name="Customers",
            asset_type="table",
            source_system="test",
            schema_metadata={
                "primary_key": ["CustomerID"],
                "grain_status": "confirmed",
                "columns": [
                    {"name": "CustomerID", "data_type": "int"},
                    {"name": "Name", "data_type": "varchar"},
                ],
            },
        )
        db.add(asset)
        db.commit()

        loaded = db.query(Asset).first()
        pk = loaded.schema_metadata.get("primary_key")
        assert pk == ["CustomerID"]

    def test_asset_no_natural_pk(self, db):
        """Assets marked as no_natural_pk should be queryable."""
        asset = Asset(
            id=str(uuid4()),
            qualified_name="[dbo].[AuditLog]",
            table_schema="dbo",
            table_name="AuditLog",
            asset_type="table",
            source_system="test",
            schema_metadata={
                "grain_status": "no_natural_pk",
                "columns": [
                    {"name": "LogID", "data_type": "int"},
                    {"name": "Action", "data_type": "varchar"},
                    {"name": "Timestamp", "data_type": "datetime"},
                ],
            },
        )
        db.add(asset)
        db.commit()

        loaded = db.query(Asset).first()
        assert loaded.schema_metadata["grain_status"] == "no_natural_pk"
