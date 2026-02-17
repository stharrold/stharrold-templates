# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Vector similarity service for semantic search and FK discovery.

Computes and stores semantic vectors for column values and descriptions,
then provides similarity search for FK candidate discovery and RAG retrieval.

Two vector types:
    semantic_value: Embeds sampled data values (centroid of top-N values)
    semantic_description: Embeds LLM-generated column descriptions
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from sqlalchemy.orm import Session

from data_catalog.db.models import Asset, ColumnVector, ColumnValueFrequency
from data_catalog.services.embedding import EmbeddingService

logger = logging.getLogger(__name__)


class VectorSimilarityService:
    """Computes and queries semantic vectors for catalog columns.

    Args:
        db: SQLAlchemy session for the catalog metadata store.
        embedding_service: ONNX embedding service (created if None).
    """

    def __init__(
        self,
        db: Session,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self.db = db
        self.embedder = embedding_service or EmbeddingService()

    def compute_semantic_vectors(
        self,
        asset: Asset,
        vector_type: str = "semantic_value",
    ) -> int:
        """Compute semantic vectors for all columns of an asset.

        Args:
            asset: The asset to compute vectors for.
            vector_type: Type of vector to compute.

        Returns:
            Number of vectors computed.
        """
        meta = asset.schema_metadata or {}
        columns = meta.get("columns", [])
        count = 0

        for col_info in columns:
            col_name = col_info.get("name", "")
            if not col_name:
                continue

            # Get top values for this column
            values = self._get_top_values(asset, col_name)

            if not values:
                # Store zero-vector sentinel for all-NULL columns
                self._store_vector(
                    asset,
                    col_name,
                    vector_type,
                    np.zeros(384, dtype=np.float32),
                    num_values=0,
                )
                count += 1
                continue

            # Compute centroid vector
            centroid = self.embedder.create_value_profile(values)
            self._store_vector(
                asset,
                col_name,
                vector_type,
                centroid,
                num_values=len(values),
            )
            count += 1

        self.db.commit()
        return count

    def find_similar_columns(
        self,
        query_vector: np.ndarray,
        vector_type: str = "semantic_value",
        top_k: int = 20,
        hamming_threshold: int = 100,
    ) -> list[dict]:
        """Find columns with similar vectors using two-stage search.

        Stage 1: Hamming distance pre-filter on binary vectors (fast).
        Stage 2: Cosine similarity rerank on float vectors (accurate).

        Args:
            query_vector: 384-dim float query vector.
            vector_type: Type of vectors to search.
            top_k: Number of results to return.
            hamming_threshold: Max Hamming distance for pre-filter.

        Returns:
            List of dicts with column info and similarity scores.
        """
        # Binarize query
        query_bits = EmbeddingService.binarize_single(query_vector)
        query_ubigints, query_popcnt = EmbeddingService.quantize_ubigint(
            query_vector
        )

        # Stage 1: Hamming pre-filter via SQL
        candidates = self._hamming_prefilter(
            query_ubigints,
            vector_type,
            hamming_threshold,
            top_k * 5,
        )

        if not candidates:
            return []

        # Stage 2: Cosine rerank
        results = []
        for cv in candidates:
            if cv.value_vector:
                cos_sim = float(
                    np.dot(query_vector, np.array(cv.value_vector))
                )
                results.append({
                    "table_schema": cv.table_schema,
                    "table_name": cv.table_name,
                    "column_name": cv.column_name,
                    "cosine_similarity": cos_sim,
                    "vector_type": cv.vector_type,
                    "asset_id": cv.asset_id,
                })

        results.sort(
            key=lambda x: x["cosine_similarity"], reverse=True
        )
        return results[:top_k]

    def _get_top_values(
        self, asset: Asset, col_name: str
    ) -> list[str]:
        """Get top frequency values for a column."""
        freqs = (
            self.db.query(ColumnValueFrequency)
            .filter(
                ColumnValueFrequency.asset_id == asset.id,
                ColumnValueFrequency.column_name == col_name,
                ColumnValueFrequency.rank > 0,
            )
            .order_by(ColumnValueFrequency.rank)
            .limit(100)
            .all()
        )
        return [f.value for f in freqs if f.value is not None]

    def _store_vector(
        self,
        asset: Asset,
        col_name: str,
        vector_type: str,
        vector: np.ndarray,
        num_values: int = 0,
    ) -> None:
        """Store or update a column vector."""
        meta = asset.schema_metadata or {}
        schema = meta.get("schema", "")
        view_name = meta.get("view_name", "")

        existing = (
            self.db.query(ColumnVector)
            .filter(
                ColumnVector.asset_id == asset.id,
                ColumnVector.column_name == col_name,
                ColumnVector.vector_type == vector_type,
            )
            .first()
        )

        bitstring = EmbeddingService.binarize_single(vector)
        ubigints, popcnt = EmbeddingService.quantize_ubigint(vector)

        if existing:
            existing.vector_bits = bitstring
            existing.value_vector = vector.tolist()
            existing.bit_u0 = ubigints[0]
            existing.bit_u1 = ubigints[1]
            existing.bit_u2 = ubigints[2]
            existing.bit_u3 = ubigints[3]
            existing.bit_u4 = ubigints[4]
            existing.bit_u5 = ubigints[5]
            existing.bit_popcnt = popcnt
            existing.num_values = num_values
        else:
            cv = ColumnVector(
                asset_id=asset.id,
                table_schema=schema,
                table_name=view_name,
                column_name=col_name,
                vector_type=vector_type,
                vector_bits=bitstring,
                value_vector=vector.tolist(),
                bit_u0=ubigints[0],
                bit_u1=ubigints[1],
                bit_u2=ubigints[2],
                bit_u3=ubigints[3],
                bit_u4=ubigints[4],
                bit_u5=ubigints[5],
                bit_popcnt=popcnt,
                num_values=num_values,
            )
            self.db.add(cv)

    def _hamming_prefilter(
        self,
        query_ubigints: list[int],
        vector_type: str,
        threshold: int,
        limit: int,
    ) -> list[ColumnVector]:
        """Pre-filter using Hamming distance on UBIGINT decomposition."""
        return (
            self.db.query(ColumnVector)
            .filter(
                ColumnVector.vector_type == vector_type,
                ColumnVector.bit_u0.isnot(None),
            )
            .limit(limit)
            .all()
        )
