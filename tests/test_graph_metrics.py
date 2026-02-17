# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for graph metrics service."""
from __future__ import annotations

from uuid import uuid4

import pytest

from data_catalog.db.models import Asset, ColumnVector, Relationship
from data_catalog.services.graph_metrics import GraphMetricsService


class TestGraphMetricsService:
    """Tests for GraphMetricsService."""

    def _seed_graph(self, db):
        """Create a small graph for testing."""
        assets = []
        for name in ["Customers", "Orders", "Products", "OrderItems"]:
            a = Asset(
                id=str(uuid4()),
                qualified_name=f"[dbo].[{name}]",
                table_schema="dbo",
                table_name=name,
                asset_type="table",
                source_system="test",
            )
            db.add(a)
            assets.append(a)
        db.commit()

        # Orders -> Customers
        db.add(Relationship(
            id=str(uuid4()),
            parent_asset_id=assets[1].id,
            referenced_asset_id=assets[0].id,
            relationship_type="foreign_key",
            column_mappings=[{"parent": "CustomerID", "referenced": "CustomerID"}],
            is_validated=True,
        ))
        # OrderItems -> Orders
        db.add(Relationship(
            id=str(uuid4()),
            parent_asset_id=assets[3].id,
            referenced_asset_id=assets[1].id,
            relationship_type="foreign_key",
            column_mappings=[{"parent": "OrderID", "referenced": "OrderID"}],
            is_validated=True,
        ))
        # OrderItems -> Products
        db.add(Relationship(
            id=str(uuid4()),
            parent_asset_id=assets[3].id,
            referenced_asset_id=assets[2].id,
            relationship_type="foreign_key",
            column_mappings=[{"parent": "ProductID", "referenced": "ProductID"}],
            is_validated=True,
        ))
        db.commit()
        return assets

    def test_build_graph(self, db):
        assets = self._seed_graph(db)
        service = GraphMetricsService(db)
        graph = service.build_graph()

        assert graph.number_of_nodes() == 4
        assert graph.number_of_edges() == 3

    def test_compute_pagerank(self, db):
        self._seed_graph(db)
        service = GraphMetricsService(db)
        graph = service.build_graph()
        pagerank = service.compute_pagerank(graph)

        assert len(pagerank) == 4
        # All values sum to ~1.0
        assert abs(sum(pagerank.values()) - 1.0) < 0.01

    def test_detect_communities(self, db):
        self._seed_graph(db)
        service = GraphMetricsService(db)
        graph = service.build_graph()
        communities = service.detect_communities(graph)

        # Should detect at least 1 community
        assert len(communities) >= 1

    def test_analyze(self, db):
        self._seed_graph(db)
        service = GraphMetricsService(db)
        results = service.analyze()

        assert results["nodes"] == 4
        assert results["edges"] == 3
        assert "communities" in results
        assert "top_pagerank" in results

    def test_empty_graph(self, db):
        service = GraphMetricsService(db)
        results = service.analyze()

        assert results["nodes"] == 0
        assert results["edges"] == 0
