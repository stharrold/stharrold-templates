# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""6-stage RAG retrieval pipeline for semantic catalog search.

Pipeline stages:
    1. Embed query text
    2. Hamming pre-filter (binary vectors, fast)
    3. Cosine rerank (float vectors, accurate)
    4. Merge and deduplicate results
    5. Enrich with asset metadata
    6. Graph expand (BFS on FK relationships)

Searches both semantic_description and semantic_value vectors.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from sqlalchemy.orm import Session

from data_catalog.db.models import Asset, ColumnVector, Relationship
from data_catalog.services.embedding import EmbeddingService

logger = logging.getLogger(__name__)


class RAGSearchService:
    """Semantic search over the data catalog.

    Args:
        db: SQLAlchemy session.
        embedding_service: ONNX embedding service.
    """

    def __init__(
        self,
        db: Session,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self.db = db
        self.embedder = embedding_service or EmbeddingService()

    def search(
        self,
        query: str,
        top_k: int = 10,
        expand_hops: int = 1,
        vector_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute full RAG retrieval pipeline.

        Args:
            query: Natural language search query.
            top_k: Number of results to return.
            expand_hops: BFS hops for graph expansion (0 = no expansion).
            vector_types: Vector types to search (default: both).

        Returns:
            List of enriched result dicts.
        """
        if vector_types is None:
            vector_types = ["semantic_description", "semantic_value"]

        # Stage 1: Embed query
        query_vector = self.embedder.embed_query(query)

        # Stage 2-3: Search each vector type
        all_results: list[dict] = []
        for vtype in vector_types:
            results = self._search_vectors(
                query_vector, vtype, top_k * 3
            )
            all_results.extend(results)

        # Stage 4: Merge and deduplicate
        merged = self._merge_results(all_results)

        # Stage 5: Enrich with metadata
        enriched = self._enrich_results(merged[: top_k * 2])

        # Stage 6: Graph expand
        if expand_hops > 0:
            enriched = self._graph_expand(enriched, expand_hops)

        return enriched[:top_k]

    def _search_vectors(
        self,
        query_vector: np.ndarray,
        vector_type: str,
        limit: int,
    ) -> list[dict]:
        """Search vectors of a specific type."""
        vectors = (
            self.db.query(ColumnVector)
            .filter(
                ColumnVector.vector_type == vector_type,
                ColumnVector.value_vector.isnot(None),
            )
            .all()
        )

        results = []
        for cv in vectors:
            if not cv.value_vector:
                continue
            cos_sim = float(
                np.dot(query_vector, np.array(cv.value_vector))
            )
            results.append({
                "asset_id": cv.asset_id,
                "table_schema": cv.table_schema,
                "table_name": cv.table_name,
                "column_name": cv.column_name,
                "vector_type": cv.vector_type,
                "cosine_similarity": cos_sim,
            })

        results.sort(
            key=lambda x: x["cosine_similarity"], reverse=True
        )
        return results[:limit]

    def _merge_results(self, results: list[dict]) -> list[dict]:
        """Merge and deduplicate results from multiple vector types."""
        seen: dict[str, dict] = {}
        for r in results:
            key = f"{r['asset_id']}:{r['column_name']}"
            if (
                key not in seen
                or r["cosine_similarity"]
                > seen[key]["cosine_similarity"]
            ):
                seen[key] = r
        merged = sorted(
            seen.values(),
            key=lambda x: x["cosine_similarity"],
            reverse=True,
        )
        return merged

    def _enrich_results(self, results: list[dict]) -> list[dict]:
        """Enrich results with asset metadata."""
        asset_ids = {r["asset_id"] for r in results}
        assets = (
            self.db.query(Asset)
            .filter(Asset.id.in_(asset_ids))
            .all()
        )
        asset_map = {a.id: a for a in assets}

        for r in results:
            asset = asset_map.get(r["asset_id"])
            if asset:
                r["qualified_name"] = asset.qualified_name
                r["display_name"] = asset.display_name
                r["description"] = asset.description
                meta = asset.schema_metadata or {}
                r["grain_status"] = meta.get(
                    "grain_status", "unknown"
                )

        return results

    def _graph_expand(
        self, results: list[dict], hops: int
    ) -> list[dict]:
        """Expand results via BFS on FK relationships."""
        if not results:
            return results

        asset_ids = {r["asset_id"] for r in results}
        expanded_ids: set[str] = set(asset_ids)

        for _ in range(hops):
            new_ids: set[str] = set()
            rels = (
                self.db.query(Relationship)
                .filter(
                    Relationship.is_validated.is_(True),
                    (
                        Relationship.parent_asset_id.in_(expanded_ids)
                        | Relationship.referenced_asset_id.in_(
                            expanded_ids
                        )
                    ),
                )
                .all()
            )
            for rel in rels:
                new_ids.add(rel.parent_asset_id)
                new_ids.add(rel.referenced_asset_id)
            expanded_ids.update(new_ids)

        # Add expanded assets as context
        new_asset_ids = expanded_ids - asset_ids
        if new_asset_ids:
            new_assets = (
                self.db.query(Asset)
                .filter(Asset.id.in_(new_asset_ids))
                .all()
            )
            for asset in new_assets:
                results.append({
                    "asset_id": asset.id,
                    "qualified_name": asset.qualified_name,
                    "display_name": asset.display_name,
                    "description": asset.description,
                    "cosine_similarity": 0.0,
                    "source": "graph_expansion",
                })

        return results
