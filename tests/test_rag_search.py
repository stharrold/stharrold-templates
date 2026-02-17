# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for RAG search service."""
from __future__ import annotations

from uuid import uuid4

import numpy as np
import pytest

from data_catalog.db.models import (
    Asset,
    ColumnVector,
    Relationship,
    SearchIndexColumn,
)
from data_catalog.services.rag_search import RAGSearchService


class _MockEmbedder:
    """Mock embedding service that returns normalized random vectors."""

    def embed_query(self, text: str) -> np.ndarray:
        rng = np.random.default_rng(hash(text) % (2**31))
        vec = rng.standard_normal(384).astype(np.float32)
        return vec / np.linalg.norm(vec)


class TestRAGSearchService:
    """Tests for RAGSearchService."""

    def _seed_searchable(self, db):
        """Seed assets with vectors for search testing."""
        asset = Asset(
            id=str(uuid4()),
            qualified_name="[dbo].[Customers]",
            table_schema="dbo",
            table_name="Customers",
            asset_type="table",
            source_system="test",
            schema_metadata={
                "columns": [
                    {"name": "CustomerID", "data_type": "int"},
                    {"name": "CustomerName", "data_type": "varchar"},
                ],
            },
        )
        db.add(asset)
        db.commit()

        for col_name, desc in [
            ("CustomerID", "Unique identifier for the customer"),
            ("CustomerName", "Full name of the customer"),
        ]:
            entry = SearchIndexColumn(
                id=str(uuid4()),
                asset_id=asset.id,
                table_schema="dbo",
                table_name="Customers",
                column_name=col_name,
                data_type="varchar",
                ordinal_position=1,
                description=desc,
            )
            db.add(entry)

            vec = np.random.randn(384).astype(np.float32)
            vec = vec / np.linalg.norm(vec)

            cv = ColumnVector(
                id=str(uuid4()),
                asset_id=asset.id,
                table_schema="dbo",
                table_name="Customers",
                column_name=col_name,
                vector_type="semantic_description",
                value_vector=vec.tolist(),
                vector_bits="".join("1" if v > 0 else "0" for v in vec),
            )
            db.add(cv)

        db.commit()
        return asset

    def test_search_returns_results(self, db):
        self._seed_searchable(db)
        service = RAGSearchService(db, embedding_service=_MockEmbedder())
        results = service.search("customer name", top_k=5)

        assert len(results) > 0
        assert "qualified_name" in results[0]

    def test_search_empty_catalog(self, db):
        service = RAGSearchService(db, embedding_service=_MockEmbedder())
        results = service.search("anything", top_k=5)

        assert len(results) == 0

    def test_search_respects_top_k(self, db):
        self._seed_searchable(db)
        service = RAGSearchService(db, embedding_service=_MockEmbedder())
        results = service.search("customer", top_k=1)

        assert len(results) <= 1
