# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Pipeline stage 04b: Entity consolidation / deduplication.

Merges duplicate entity nodes into canonical nodes with has_alias edges.
Uses fuzzy string matching + same community_id for clustering.
"""

import logging
import re
from difflib import SequenceMatcher

from .core_db import CoreDB

logger = logging.getLogger(__name__)

MIN_FUZZY_LENGTH = 3
FUZZY_THRESHOLD = 0.65
MIN_CLUSTER_SIZE = 2
MAX_GROUP_SIZE = 500  # Use O(n^2) pairwise for groups up to this size
MAX_TOKEN_BLOCK = 200  # Skip individual token blocks larger than this
_TOKENIZE_RE = re.compile(r"[\s_\-/()>:,\.]+")  # Split on whitespace and punctuation


class _UnionFind:
    """Simple union-find (disjoint set) data structure."""

    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, i: int) -> int:
        while self.parent[i] != i:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i

    def union(self, i: int, j: int) -> None:
        ri, rj = self.find(i), self.find(j)
        if ri != rj:
            self.parent[ri] = rj


def fuzzy_name_match(name_a: str, name_b: str) -> bool:
    """Check if two entity names refer to the same concept."""
    a = name_a.strip().lower()
    b = name_b.strip().lower()

    if not a or not b:
        return False

    if a == b:
        return True

    if len(a) < MIN_FUZZY_LENGTH or len(b) < MIN_FUZZY_LENGTH:
        return False

    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    if shorter in longer:
        return True

    ratio = SequenceMatcher(None, a, b).ratio()
    return ratio >= FUZZY_THRESHOLD


def _tokenize_name(name: str) -> set[str]:
    """Split entity name into normalized tokens for blocking."""
    tokens = _TOKENIZE_RE.split(name.strip().lower())
    return {t for t in tokens if len(t) >= MIN_FUZZY_LENGTH}


def _cluster_with_blocking(group: list[dict]) -> list[list[dict]]:
    """Cluster a large group using token-based blocking.

    Instead of O(n^2) pairwise comparison, builds an inverted index of
    name tokens and only compares entities sharing at least one token.
    """
    token_index: dict[str, list[int]] = {}
    for i, ent in enumerate(group):
        for tok in _tokenize_name(ent["name"]):
            token_index.setdefault(tok, []).append(i)

    uf = _UnionFind(len(group))
    seen_pairs: set[tuple[int, int]] = set()

    for indices in token_index.values():
        if len(indices) < MIN_CLUSTER_SIZE or len(indices) > MAX_TOKEN_BLOCK:
            continue
        for ii in range(len(indices)):
            for jj in range(ii + 1, len(indices)):
                pair = (indices[ii], indices[jj])
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                if fuzzy_name_match(group[pair[0]]["name"], group[pair[1]]["name"]):
                    uf.union(pair[0], pair[1])

    cluster_map: dict[int, list[dict]] = {}
    for i in range(len(group)):
        root = uf.find(i)
        cluster_map.setdefault(root, []).append(group[i])

    return [c for c in cluster_map.values() if len(c) >= MIN_CLUSTER_SIZE]


def find_consolidation_clusters(entities: list[dict]) -> list[list[dict]]:
    """Group entities into clusters of duplicates.

    Clusters entities that share same node_type, same community_id,
    and have fuzzy-matching names.
    """
    groups = {}
    for ent in entities:
        key = (ent.get("node_type", "Topic"), ent.get("community_id"))
        if key[1] is None or key[1] == -1:
            continue
        groups.setdefault(key, []).append(ent)

    clusters = []
    for _key, group in groups.items():
        if len(group) < MIN_CLUSTER_SIZE:
            continue

        if len(group) > MAX_GROUP_SIZE:
            logger.info(
                "Token-blocking large group (type=%s, community=%s, size=%d)",
                _key[0], _key[1], len(group),
            )
            clusters.extend(_cluster_with_blocking(group))
            continue

        uf = _UnionFind(len(group))

        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                if fuzzy_name_match(group[i]["name"], group[j]["name"]):
                    uf.union(i, j)

        cluster_map = {}
        for i in range(len(group)):
            root = uf.find(i)
            cluster_map.setdefault(root, []).append(group[i])

        for cluster in cluster_map.values():
            if len(cluster) >= MIN_CLUSTER_SIZE:
                clusters.append(cluster)

    return clusters


def pick_canonical_name(cluster: list[dict]) -> dict:
    """Pick the canonical entity from a cluster.

    Highest pagerank wins. On tie, shortest name wins.
    """
    return max(cluster, key=lambda e: (e.get("pagerank", 0), -len(e.get("name", ""))))


def run(db: CoreDB = None):
    """Run entity consolidation on all non-Email, non-Person, non-Alias nodes."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - pipe_04b - %(levelname)s - %(message)s",
    )

    own_db = db is None
    if own_db:
        db = CoreDB()

    rows = db.query(f"""
        SELECT node_id, node_type, name, pagerank, community_id
        FROM {db.table("graph_nodes")}
        WHERE node_type IN ('Topic', 'Project', 'Organization')
          AND community_id IS NOT NULL AND community_id != -1
        ORDER BY pagerank DESC NULLS LAST
    """)

    entities = [
        {
            "node_id": r[0],
            "node_type": r[1],
            "name": r[2],
            "pagerank": r[3] or 0,
            "community_id": r[4],
        }
        for r in rows
    ]

    logger.info("Loaded %d entities for consolidation.", len(entities))

    clusters = find_consolidation_clusters(entities)
    logger.info("Found %d consolidation clusters.", len(clusters))

    alias_edges = []
    mention_redirects = []

    for cluster in clusters:
        canonical = pick_canonical_name(cluster)
        canonical_id = canonical["node_id"]

        for ent in cluster:
            if ent["node_id"] == canonical_id:
                continue
            alias_edges.append((canonical_id, ent["node_id"], "has_alias", 1.0))
            mention_redirects.append((ent["node_id"], canonical_id))

    if alias_edges:
        db.conn.executemany(
            f"INSERT OR IGNORE INTO {db.table('semantic_edges')} (source_id, target_id, edge_type, weight) VALUES (?, ?, ?, ?)",
            alias_edges,
        )
        logger.info("Created %d has_alias edges.", len(alias_edges))

    redirected = 0
    dropped_dupes = 0
    for old_target, new_target in mention_redirects:
        # Delete alias mention edges where canonical already has a mention from same source
        result = db.conn.execute(
            f"""DELETE FROM {db.table('semantic_edges')}
                WHERE target_id = ? AND edge_type = 'mention'
                AND source_id IN (
                    SELECT source_id FROM {db.table('semantic_edges')}
                    WHERE target_id = ? AND edge_type = 'mention'
                )""",
            (old_target, new_target),
        )
        dropped_dupes += result.rowcount
        # Redirect remaining alias mentions to canonical
        result = db.conn.execute(
            f"UPDATE {db.table('semantic_edges')} SET target_id = ? WHERE target_id = ? AND edge_type = 'mention'",
            (new_target, old_target),
        )
        redirected += result.rowcount

    if redirected or dropped_dupes:
        logger.info(
            "Redirected %d mention edges to canonical nodes (%d duplicate edges dropped).",
            redirected, dropped_dupes,
        )

    logger.info(
        "Consolidation complete. %d clusters, %d alias edges, %d redirects, %d dupes dropped.",
        len(clusters),
        len(alias_edges),
        redirected,
        dropped_dupes,
    )

    if own_db:
        db.close()

    return {
        "clusters": len(clusters),
        "alias_edges": len(alias_edges),
        "redirected": redirected,
    }
