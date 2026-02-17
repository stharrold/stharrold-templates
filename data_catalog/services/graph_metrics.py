# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Graph analysis service for business entity discovery.

Builds a NetworkX graph from FK relationships and runs:
- Community detection (Louvain)
- PageRank centrality
- HDBSCAN clustering on semantic_description vectors
- Name consolidation (fuzzy matching of entity names)
- Co-occurrence analysis (entities sharing FK targets)
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any

import networkx as nx
import numpy as np
from sqlalchemy.orm import Session

from data_catalog.db.models import Asset, ColumnVector, Relationship

logger = logging.getLogger(__name__)


class GraphMetricsService:
    """Builds and analyzes the asset relationship graph.

    Args:
        db: SQLAlchemy session for the catalog metadata store.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def build_graph(self) -> nx.DiGraph:
        """Build a directed graph from validated FK relationships."""
        G = nx.DiGraph()

        assets = self.db.query(Asset).all()
        for asset in assets:
            meta = asset.schema_metadata or {}
            if meta.get("inactive"):
                continue
            G.add_node(
                asset.qualified_name,
                asset_type=asset.asset_type,
                grain_status=meta.get("grain_status", "unknown"),
            )

        relationships = (
            self.db.query(Relationship)
            .filter(Relationship.is_validated.is_(True))
            .all()
        )
        for rel in relationships:
            G.add_edge(
                rel.parent_asset.qualified_name,
                rel.referenced_asset.qualified_name,
                relationship_type=rel.relationship_type,
                cardinality=rel.cardinality,
                constraint_name=rel.constraint_name,
            )

        logger.info(
            f"Built graph: {G.number_of_nodes()} nodes, "
            f"{G.number_of_edges()} edges"
        )
        return G

    def compute_pagerank(self, G: nx.DiGraph) -> dict[str, float]:
        """Compute PageRank centrality for all nodes."""
        if G.number_of_nodes() == 0:
            return {}
        return nx.pagerank(G)

    def detect_communities(self, G: nx.DiGraph) -> dict[str, int]:
        """Detect communities using Louvain algorithm on undirected
        projection.
        """
        if G.number_of_nodes() == 0:
            return {}
        try:
            from networkx.algorithms.community import louvain_communities

            undirected = G.to_undirected()
            communities = louvain_communities(undirected)
            membership: dict[str, int] = {}
            for i, community in enumerate(communities):
                for node in community:
                    membership[node] = i
            return membership
        except Exception as e:
            logger.warning(f"Community detection failed: {e}")
            return {}

    def cluster_by_description(
        self, min_cluster_size: int = 3
    ) -> dict[str, int]:
        """Cluster assets using HDBSCAN on semantic_description vectors.

        Returns:
            Map of qualified_name -> cluster_id (-1 = noise).
        """
        try:
            from sklearn.cluster import HDBSCAN
        except ImportError:
            logger.warning(
                "scikit-learn not available for HDBSCAN"
            )
            return {}

        # Load description vectors
        vectors = (
            self.db.query(ColumnVector)
            .filter(
                ColumnVector.vector_type == "semantic_description"
            )
            .all()
        )
        if len(vectors) < min_cluster_size:
            return {}

        # Build matrix
        names = []
        matrix = []
        for v in vectors:
            if v.value_vector:
                names.append(
                    f"[{v.table_schema}].[{v.table_name}]"
                    f".{v.column_name}"
                )
                matrix.append(v.value_vector)

        if not matrix:
            return {}

        X = np.array(matrix)
        clusterer = HDBSCAN(
            min_cluster_size=min_cluster_size, metric="cosine"
        )
        labels = clusterer.fit_predict(X)

        return dict(zip(names, [int(l) for l in labels]))

    def analyze(self) -> dict[str, Any]:
        """Run full graph analysis and return summary metrics."""
        G = self.build_graph()
        pagerank = self.compute_pagerank(G)
        communities = self.detect_communities(G)

        # Summary
        n_communities = (
            len(set(communities.values())) if communities else 0
        )
        top_pagerank = sorted(
            pagerank.items(), key=lambda x: x[1], reverse=True
        )[:10]

        return {
            "nodes": G.number_of_nodes(),
            "edges": G.number_of_edges(),
            "communities": n_communities,
            "top_pagerank": [
                {"asset": name, "score": round(score, 4)}
                for name, score in top_pagerank
            ],
            "density": (
                nx.density(G) if G.number_of_nodes() > 1 else 0.0
            ),
        }
