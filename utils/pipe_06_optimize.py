# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
import logging
import time

import numpy as np
from sklearn.cluster import MiniBatchKMeans

from .core_db import CoreDB

DEFAULT_ITERATIONS = 20
DAMPING = 0.85
EPSILON = 1e-6
HITS_ITERATIONS = 20
HITS_EPSILON = 1e-4
COMMUNITY_ROUNDS = 5
EMBEDDING_CLUSTERS_K = 50

# Geometric milestone pattern: 10, 30, 100, 300, 1000, 3000, 10000...
# Uses 1-3-10 pattern within each decade (matches library check_optimizer.py)

logger = logging.getLogger(__name__)


def run_pagerank(db, iterations=DEFAULT_ITERATIONS):
    """Compute PageRank scores for all graph nodes via iterative SQL."""
    logger.info(
        "Running PageRank (%d iterations, damping=%s, epsilon=%s)...",
        iterations,
        DAMPING,
        EPSILON,
    )

    db.conn.execute("DROP TABLE IF EXISTS _tmp_out_degree")
    db.conn.execute(f"CREATE TEMP TABLE _tmp_out_degree AS SELECT source_id, count(*) as degree FROM {db.table('semantic_edges')} GROUP BY source_id")

    for i in range(1, iterations + 1):
        db.conn.execute("DROP TABLE IF EXISTS _tmp_prev_ranks")
        db.conn.execute(f"CREATE TEMP TABLE _tmp_prev_ranks AS SELECT node_id, pagerank FROM {db.table('graph_nodes')}")

        db.conn.execute(f"""
            UPDATE {db.table("graph_nodes")}
            SET pagerank = {1 - DAMPING} + {DAMPING} * (
                SELECT COALESCE(SUM(src.pagerank / deg.degree), 0)
                FROM {db.table("semantic_edges")} e
                JOIN {db.table("graph_nodes")} src ON e.source_id = src.node_id
                JOIN _tmp_out_degree deg ON src.node_id = deg.source_id
                WHERE e.target_id = {db.table("graph_nodes")}.node_id
            )
        """)

        result = db.query(f"""
            SELECT MAX(ABS(g.pagerank - p.pagerank))
            FROM {db.table("graph_nodes")} g
            JOIN _tmp_prev_ranks p ON g.node_id = p.node_id
        """)
        max_delta = result[0][0] if result and result[0][0] is not None else 0.0

        if i % 5 == 0 or i == 1:
            logger.info("  PageRank iteration %d/%d: max_delta=%.8f", i, iterations, max_delta)

        if max_delta < EPSILON:
            logger.info(
                "  PageRank converged at iteration %d (max_delta=%.8f < epsilon=%s)",
                i,
                max_delta,
                EPSILON,
            )
            break

    db.conn.execute("DROP TABLE IF EXISTS _tmp_out_degree")
    db.conn.execute("DROP TABLE IF EXISTS _tmp_prev_ranks")
    logger.info("PageRank complete.")


def run_hits(db, iterations=HITS_ITERATIONS):
    """Compute HITS authority and hub scores for all graph nodes.

    Authority: sum of hub scores of nodes pointing to this node.
    Hub: sum of authority scores of nodes this node points to.
    Both are L2-normalized after each iteration.
    """
    logger.info("Running HITS (%d iterations, epsilon=%s)...", iterations, HITS_EPSILON)

    # Initialize scores to 1.0
    db.conn.execute(f"UPDATE {db.table('graph_nodes')} SET authority_score = 1.0, hub_score = 1.0")

    for i in range(1, iterations + 1):
        # Save previous scores
        db.conn.execute("DROP TABLE IF EXISTS _tmp_prev_hits")
        db.conn.execute(f"CREATE TEMP TABLE _tmp_prev_hits AS SELECT node_id, authority_score, hub_score FROM {db.table('graph_nodes')}")

        # Authority update: authority(v) = SUM(hub(u)) for all u -> v
        db.conn.execute(f"""
            UPDATE {db.table("graph_nodes")}
            SET authority_score = (
                SELECT COALESCE(SUM(src.hub_score * e.weight), 0)
                FROM {db.table("semantic_edges")} e
                JOIN {db.table("graph_nodes")} src ON e.source_id = src.node_id
                WHERE e.target_id = {db.table("graph_nodes")}.node_id
            )
        """)

        # L2 normalize authority
        db.conn.execute(f"""
            UPDATE {db.table("graph_nodes")}
            SET authority_score = authority_score / NULLIF(
                (SELECT SQRT(SUM(authority_score * authority_score)) FROM {db.table("graph_nodes")}), 0
            )
        """)

        # Hub update: hub(u) = SUM(authority(v)) for all u -> v
        db.conn.execute(f"""
            UPDATE {db.table("graph_nodes")}
            SET hub_score = (
                SELECT COALESCE(SUM(tgt.authority_score * e.weight), 0)
                FROM {db.table("semantic_edges")} e
                JOIN {db.table("graph_nodes")} tgt ON e.target_id = tgt.node_id
                WHERE e.source_id = {db.table("graph_nodes")}.node_id
            )
        """)

        # L2 normalize hub
        db.conn.execute(f"""
            UPDATE {db.table("graph_nodes")}
            SET hub_score = hub_score / NULLIF(
                (SELECT SQRT(SUM(hub_score * hub_score)) FROM {db.table("graph_nodes")}), 0
            )
        """)

        # Convergence check
        result = db.query(f"""
            SELECT SUM(ABS(g.authority_score - p.authority_score)
                     + ABS(g.hub_score - p.hub_score))
            FROM {db.table("graph_nodes")} g
            JOIN _tmp_prev_hits p ON g.node_id = p.node_id
        """)
        delta = result[0][0] if result and result[0][0] is not None else 0.0

        if i % 5 == 0 or i == 1:
            logger.info("  HITS iteration %d/%d: delta=%.8f", i, iterations, delta)

        if delta < HITS_EPSILON:
            logger.info(
                "  HITS converged at iteration %d (delta=%.8f < epsilon=%s)",
                i,
                delta,
                HITS_EPSILON,
            )
            break

    db.conn.execute("DROP TABLE IF EXISTS _tmp_prev_hits")
    logger.info("HITS complete.")


def run_community_detection(db, rounds=COMMUNITY_ROUNDS):
    """Label propagation community detection via SQL mode() smoothing.

    Each node adopts the most common community_id among its neighbors.
    Repeated rounds allow labels to propagate through the graph.
    """
    logger.info("Running community detection (%d rounds)...", rounds)

    # Initialize: each node is its own community (use ROWID-like assignment)
    db.conn.execute(f"""
        UPDATE {db.table("graph_nodes")}
        SET community_id = CASE
            WHEN community_id IS NULL OR community_id = -1
            THEN abs(hash(node_id)) % 1000000
            ELSE community_id
        END
    """)

    for i in range(1, rounds + 1):
        # Each node adopts the mode (most common) community_id of its neighbors
        db.conn.execute("DROP TABLE IF EXISTS _tmp_comm_updates")
        db.conn.execute(f"""
            CREATE TEMP TABLE _tmp_comm_updates AS
            SELECT
                e_src AS node_id,
                mode(neighbor_comm) AS new_comm
            FROM (
                SELECT e.source_id AS e_src, tgt.community_id AS neighbor_comm
                FROM {db.table("semantic_edges")} e
                JOIN {db.table("graph_nodes")} tgt ON e.target_id = tgt.node_id
                WHERE tgt.community_id IS NOT NULL AND tgt.community_id != -1
                UNION ALL
                SELECT e.target_id AS e_src, src.community_id AS neighbor_comm
                FROM {db.table("semantic_edges")} e
                JOIN {db.table("graph_nodes")} src ON e.source_id = src.node_id
                WHERE src.community_id IS NOT NULL AND src.community_id != -1
            ) neighbors
            GROUP BY e_src
        """)

        db.conn.execute(f"""
            UPDATE {db.table("graph_nodes")} g
            SET community_id = u.new_comm
            FROM _tmp_comm_updates u
            WHERE g.node_id = u.node_id
              AND g.community_id != u.new_comm
        """)

        db.conn.execute("DROP TABLE IF EXISTS _tmp_comm_updates")
        logger.info("  Community round %d/%d complete.", i, rounds)

    # Count communities
    result = db.query(f"SELECT count(DISTINCT community_id) FROM {db.table('graph_nodes')} WHERE community_id != -1")
    num_communities = result[0][0] if result and result[0][0] is not None else 0
    logger.info("Community detection complete. %d communities found.", num_communities)


def run_embedding_clusters(db, k=EMBEDDING_CLUSTERS_K):
    """K-means clustering on node embeddings for semantic community detection.

    Converts 1-bit embeddings to +/-1 float vectors, runs MiniBatchKMeans,
    and stores cluster assignments in embedding_cluster_id.
    """
    logger.info("Running embedding clustering (k=%d)...", k)

    # Fetch all Email nodes with UBIGINT embeddings
    rows = db.query(f"""
        SELECT node_id, bit_u0, bit_u1, bit_u2, bit_u3, bit_u4, bit_u5
        FROM {db.table("graph_nodes")}
        WHERE bit_u0 IS NOT NULL AND node_type = 'Email'
    """)

    if not rows:
        logger.info("No email nodes with embeddings found. Skipping clustering.")
        return

    logger.info("  Loading %d email embeddings...", len(rows))
    node_ids = [r[0] for r in rows]

    # Convert 6 UBIGINTs to +/-1 float vectors for meaningful Euclidean distance
    vectors = np.zeros((len(rows), 384), dtype=np.float32)
    for i, (_, *ubigints) in enumerate(rows):
        for u_idx, val in enumerate(ubigints):
            if val is None:
                continue
            for bit_pos in range(64):
                j = u_idx * 64 + bit_pos
                # Extract bit: MSB first (bit 63 is position 0 within each UBIGINT)
                if (val >> (63 - bit_pos)) & 1:
                    vectors[i, j] = 1.0
                else:
                    vectors[i, j] = -1.0

    # Adjust k if fewer samples than clusters
    actual_k = min(k, len(node_ids))
    if actual_k < k:
        logger.info("  Adjusted k from %d to %d (fewer samples).", k, actual_k)

    logger.info("  Running MiniBatchKMeans (k=%d, n=%d)...", actual_k, len(node_ids))
    kmeans = MiniBatchKMeans(n_clusters=actual_k, batch_size=4096, n_init=1, random_state=42)
    labels = kmeans.fit_predict(vectors)

    # Batch update cluster assignments
    batch_size = 5000
    for start in range(0, len(node_ids), batch_size):
        end = min(start + batch_size, len(node_ids))
        updates = [(int(labels[i]), node_ids[i]) for i in range(start, end)]
        db.conn.executemany(f"UPDATE {db.table('graph_nodes')} SET embedding_cluster_id = ? WHERE node_id = ?", updates)

    num_clusters = len(set(labels))
    logger.info("Embedding clustering complete. %d clusters assigned to %d nodes.", num_clusters, len(node_ids))


def run_incremental(db, node_ids):
    """Lightweight single-pass update for newly added nodes only.

    Sets approximate PageRank, authority, hub, and community_id by averaging
    neighbors' existing scores. Much faster than full iterative optimization.
    """
    if not node_ids:
        return

    t0 = time.perf_counter()

    # Create temp table with target node IDs
    db.conn.execute("DROP TABLE IF EXISTS _inc_targets")
    db.conn.execute("CREATE TEMP TABLE _inc_targets (node_id VARCHAR PRIMARY KEY)")
    db.conn.executemany("INSERT OR IGNORE INTO _inc_targets VALUES (?)", [(nid,) for nid in node_ids])

    # Approximate PageRank: average of neighbors' pagerank, default 0.15
    db.conn.execute(f"""
        UPDATE {db.table("graph_nodes")}
        SET pagerank = COALESCE(
            (SELECT AVG(neighbor.pagerank)
             FROM {db.table("semantic_edges")} e
             JOIN {db.table("graph_nodes")} neighbor ON e.target_id = neighbor.node_id
             WHERE e.source_id = {db.table("graph_nodes")}.node_id
               AND neighbor.pagerank > 0),
            {1 - DAMPING}
        )
        WHERE node_id IN (SELECT node_id FROM _inc_targets)
    """)

    # Approximate authority: average of in-neighbors' authority
    db.conn.execute(f"""
        UPDATE {db.table("graph_nodes")}
        SET authority_score = COALESCE(
            (SELECT AVG(neighbor.authority_score)
             FROM {db.table("semantic_edges")} e
             JOIN {db.table("graph_nodes")} neighbor ON e.source_id = neighbor.node_id
             WHERE e.target_id = {db.table("graph_nodes")}.node_id
               AND neighbor.authority_score > 0),
            0.0
        )
        WHERE node_id IN (SELECT node_id FROM _inc_targets)
    """)

    # Approximate hub: average of out-neighbors' hub
    db.conn.execute(f"""
        UPDATE {db.table("graph_nodes")}
        SET hub_score = COALESCE(
            (SELECT AVG(neighbor.hub_score)
             FROM {db.table("semantic_edges")} e
             JOIN {db.table("graph_nodes")} neighbor ON e.target_id = neighbor.node_id
             WHERE e.source_id = {db.table("graph_nodes")}.node_id
               AND neighbor.hub_score > 0),
            0.0
        )
        WHERE node_id IN (SELECT node_id FROM _inc_targets)
    """)

    # Community: adopt mode of neighbors, or hash-based fallback
    db.conn.execute(f"""
        UPDATE {db.table("graph_nodes")}
        SET community_id = COALESCE(
            (SELECT mode(neighbor.community_id)
             FROM (
                 SELECT tgt.community_id
                 FROM {db.table("semantic_edges")} e
                 JOIN {db.table("graph_nodes")} tgt ON e.target_id = tgt.node_id
                 WHERE e.source_id = {db.table("graph_nodes")}.node_id
                   AND tgt.community_id IS NOT NULL AND tgt.community_id != -1
                 UNION ALL
                 SELECT src.community_id
                 FROM {db.table("semantic_edges")} e
                 JOIN {db.table("graph_nodes")} src ON e.source_id = src.node_id
                 WHERE e.target_id = {db.table("graph_nodes")}.node_id
                   AND src.community_id IS NOT NULL AND src.community_id != -1
             ) neighbor),
            abs(hash({db.table("graph_nodes")}.node_id)) % 1000000
        )
        WHERE node_id IN (SELECT node_id FROM _inc_targets)
    """)

    db.conn.execute("DROP TABLE IF EXISTS _inc_targets")
    elapsed = time.perf_counter() - t0
    logger.debug("Incremental optimization for %d nodes in %.3fs", len(node_ids), elapsed)


def run_scoped_optimization(db, seed_node_ids, iterations=10):
    """Run iterative PageRank/HITS/community on a subgraph (seed nodes + 1-hop neighbors).

    This is more accurate than single-pass averaging but faster than full graph optimization.
    Used at milestones to recalculate the m recently-ingested nodes + their ~10*m connections.
    """
    if not seed_node_ids:
        return 0

    t0 = time.perf_counter()

    # 1. Create temp table with seed nodes
    db.conn.execute("DROP TABLE IF EXISTS _scope_seeds")
    db.conn.execute("CREATE TEMP TABLE _scope_seeds (node_id VARCHAR PRIMARY KEY)")
    db.conn.executemany("INSERT OR IGNORE INTO _scope_seeds VALUES (?)", [(nid,) for nid in seed_node_ids])

    # 2. Expand to 1-hop neighbors (seed nodes + their connections)
    db.conn.execute("DROP TABLE IF EXISTS _scope_targets")
    db.conn.execute(f"""
        CREATE TEMP TABLE _scope_targets AS
        SELECT DISTINCT node_id FROM (
            -- Seed nodes
            SELECT node_id FROM _scope_seeds
            UNION
            -- Outgoing neighbors
            SELECT e.target_id AS node_id
            FROM {db.table("semantic_edges")} e
            WHERE e.source_id IN (SELECT node_id FROM _scope_seeds)
            UNION
            -- Incoming neighbors
            SELECT e.source_id AS node_id
            FROM {db.table("semantic_edges")} e
            WHERE e.target_id IN (SELECT node_id FROM _scope_seeds)
        )
    """)

    result = db.query("SELECT COUNT(*) FROM _scope_targets")
    scope_size = result[0][0] if result else 0
    logger.info("Scoped optimization: %d seed nodes expanded to %d total nodes", len(seed_node_ids), scope_size)

    if scope_size == 0:
        db.conn.execute("DROP TABLE IF EXISTS _scope_seeds")
        db.conn.execute("DROP TABLE IF EXISTS _scope_targets")
        return 0

    # 3. Build subgraph edges temp table (only edges within scope)
    db.conn.execute("DROP TABLE IF EXISTS _scope_edges")
    db.conn.execute(f"""
        CREATE TEMP TABLE _scope_edges AS
        SELECT e.source_id, e.target_id, e.weight
        FROM {db.table("semantic_edges")} e
        WHERE e.source_id IN (SELECT node_id FROM _scope_targets)
          AND e.target_id IN (SELECT node_id FROM _scope_targets)
    """)

    # 4. Out-degree within subgraph
    db.conn.execute("DROP TABLE IF EXISTS _scope_out_degree")
    db.conn.execute("""
        CREATE TEMP TABLE _scope_out_degree AS
        SELECT source_id, COUNT(*) as degree
        FROM _scope_edges
        GROUP BY source_id
    """)

    # 5. Iterative PageRank on subgraph only
    for i in range(1, iterations + 1):
        db.conn.execute("DROP TABLE IF EXISTS _scope_prev_pr")
        db.conn.execute(f"""
            CREATE TEMP TABLE _scope_prev_pr AS
            SELECT node_id, pagerank FROM {db.table("graph_nodes")}
            WHERE node_id IN (SELECT node_id FROM _scope_targets)
        """)

        db.conn.execute(f"""
            UPDATE {db.table("graph_nodes")}
            SET pagerank = {1 - DAMPING} + {DAMPING} * (
                SELECT COALESCE(SUM(src.pagerank / deg.degree), 0)
                FROM _scope_edges e
                JOIN {db.table("graph_nodes")} src ON e.source_id = src.node_id
                JOIN _scope_out_degree deg ON src.node_id = deg.source_id
                WHERE e.target_id = {db.table("graph_nodes")}.node_id
            )
            WHERE node_id IN (SELECT node_id FROM _scope_targets)
        """)

        # Convergence check
        result = db.query(f"""
            SELECT MAX(ABS(g.pagerank - p.pagerank))
            FROM {db.table("graph_nodes")} g
            JOIN _scope_prev_pr p ON g.node_id = p.node_id
        """)
        max_delta = result[0][0] if result and result[0][0] is not None else 0.0
        if max_delta < EPSILON:
            logger.debug("Scoped PageRank converged at iteration %d", i)
            break

    # 6. Iterative HITS on subgraph (fewer iterations for speed)
    hits_iters = min(iterations, HITS_ITERATIONS // 2)
    for _ in range(hits_iters):
        # Authority update
        db.conn.execute(f"""
            UPDATE {db.table("graph_nodes")}
            SET authority_score = (
                SELECT COALESCE(SUM(src.hub_score * e.weight), 0)
                FROM _scope_edges e
                JOIN {db.table("graph_nodes")} src ON e.source_id = src.node_id
                WHERE e.target_id = {db.table("graph_nodes")}.node_id
            )
            WHERE node_id IN (SELECT node_id FROM _scope_targets)
        """)

        # L2 normalize authority within scope
        db.conn.execute(f"""
            UPDATE {db.table("graph_nodes")}
            SET authority_score = authority_score / NULLIF(
                (SELECT SQRT(SUM(authority_score * authority_score))
                 FROM {db.table("graph_nodes")} WHERE node_id IN (SELECT node_id FROM _scope_targets)), 0
            )
            WHERE node_id IN (SELECT node_id FROM _scope_targets)
        """)

        # Hub update
        db.conn.execute(f"""
            UPDATE {db.table("graph_nodes")}
            SET hub_score = (
                SELECT COALESCE(SUM(tgt.authority_score * e.weight), 0)
                FROM _scope_edges e
                JOIN {db.table("graph_nodes")} tgt ON e.target_id = tgt.node_id
                WHERE e.source_id = {db.table("graph_nodes")}.node_id
            )
            WHERE node_id IN (SELECT node_id FROM _scope_targets)
        """)

        # L2 normalize hub within scope
        db.conn.execute(f"""
            UPDATE {db.table("graph_nodes")}
            SET hub_score = hub_score / NULLIF(
                (SELECT SQRT(SUM(hub_score * hub_score))
                 FROM {db.table("graph_nodes")} WHERE node_id IN (SELECT node_id FROM _scope_targets)), 0
            )
            WHERE node_id IN (SELECT node_id FROM _scope_targets)
        """)

    # 7. Community detection within scope (label propagation, 3 rounds)
    for _ in range(3):
        db.conn.execute("DROP TABLE IF EXISTS _scope_comm_updates")
        db.conn.execute(f"""
            CREATE TEMP TABLE _scope_comm_updates AS
            SELECT
                e_src AS node_id,
                mode(neighbor_comm) AS new_comm
            FROM (
                SELECT e.source_id AS e_src, tgt.community_id AS neighbor_comm
                FROM _scope_edges e
                JOIN {db.table("graph_nodes")} tgt ON e.target_id = tgt.node_id
                WHERE tgt.community_id IS NOT NULL AND tgt.community_id != -1
                UNION ALL
                SELECT e.target_id AS e_src, src.community_id AS neighbor_comm
                FROM _scope_edges e
                JOIN {db.table("graph_nodes")} src ON e.source_id = src.node_id
                WHERE src.community_id IS NOT NULL AND src.community_id != -1
            ) neighbors
            WHERE e_src IN (SELECT node_id FROM _scope_targets)
            GROUP BY e_src
        """)

        db.conn.execute(f"""
            UPDATE {db.table("graph_nodes")} g
            SET community_id = u.new_comm
            FROM _scope_comm_updates u
            WHERE g.node_id = u.node_id
              AND g.community_id != u.new_comm
        """)
        db.conn.execute("DROP TABLE IF EXISTS _scope_comm_updates")

    # Cleanup temp tables
    db.conn.execute("DROP TABLE IF EXISTS _scope_seeds")
    db.conn.execute("DROP TABLE IF EXISTS _scope_targets")
    db.conn.execute("DROP TABLE IF EXISTS _scope_edges")
    db.conn.execute("DROP TABLE IF EXISTS _scope_out_degree")
    db.conn.execute("DROP TABLE IF EXISTS _scope_prev_pr")

    elapsed = time.perf_counter() - t0
    logger.info("Scoped optimization complete: %d nodes in %.2fs", scope_size, elapsed)
    return scope_size


def get_pattern_value(n):
    """Return tier value only at exact geometric milestones: 10, 30, 100, 300, 1000...

    Uses 1-3-10 pattern within each decade.
    Returns None for non-milestone values.
    """
    if n < 10:
        return None

    # Remove trailing zeros and count them
    k = 0
    temp_n = n
    while temp_n % 10 == 0:
        k += 1
        temp_n //= 10

    # Check if remaining value is exactly 1 or 3 (not just ends in 1 or 3)
    # This yields: 10, 30, 100, 300, 1000, 3000, 10000, 30000...
    if temp_n == 3:
        return 3 * (10**k)
    elif temp_n == 1 and k > 0:
        return 10**k
    return None


def check_milestone_trigger(db):
    """Check if graph_nodes count has crossed a new milestone since last recorded one.

    Scans the range from last processed count to current count to catch any
    milestones that may have been passed (handles batch ingestion jumps).
    Returns the highest milestone tier crossed, or None.
    """
    result = db.query(f"SELECT COUNT(*) FROM {db.table('graph_nodes')}")
    current_count = result[0][0] if result and result[0][0] else 0

    if current_count < 10:
        return None

    # Check last recorded milestone in pipeline_logs
    last = db.query(f"""
        SELECT details FROM {db.table("pipeline_logs")}
        WHERE task = 'optimize_milestone'
        ORDER BY created_at DESC
        LIMIT 1
    """)

    last_processed_count = 0
    if last and last[0][0]:
        try:
            import json

            info = json.loads(last[0][0])
            last_processed_count = info.get("nodes_processed", 0)
        except (json.JSONDecodeError, TypeError):
            pass

    # Scan the range for missed milestones (like library check_optimizer.py)
    if current_count <= last_processed_count:
        return None

    max_tier = 0
    for n in range(last_processed_count + 1, current_count + 1):
        tier = get_pattern_value(n)
        if tier and tier > max_tier:
            max_tier = tier

    return max_tier if max_tier > 0 else None


def run_milestone_if_needed(db):
    """If a milestone was crossed, run scoped optimization on recent nodes + connections.

    Instead of full graph optimization, we only recalculate graph measures for:
    - The m nodes added since the last milestone (seed nodes)
    - Their 1-hop connected neighbors (~10*m nodes total)

    This is much faster than full graph recompute while maintaining accuracy.
    Embedding clustering only runs at larger milestones (1000+).
    """
    import json

    # Get current count before checking trigger (needed for logging)
    result = db.query(f"SELECT COUNT(*) FROM {db.table('graph_nodes')}")
    current_count = result[0][0] if result and result[0][0] else 0

    tier = check_milestone_trigger(db)
    if tier is None:
        return False

    # Get last processed count to find seed nodes
    last = db.query(f"""
        SELECT details FROM {db.table("pipeline_logs")}
        WHERE task = 'optimize_milestone'
        ORDER BY created_at DESC
        LIMIT 1
    """)

    last_processed_count = 0
    has_baseline = False
    if last and last[0][0]:
        try:
            info = json.loads(last[0][0])
            last_processed_count = info.get("nodes_processed", 0)
            has_baseline = True
        except (json.JSONDecodeError, TypeError):
            pass

    # Skip if no baseline - first milestone should be set manually or via full optimization
    if not has_baseline:
        logger.info("No milestone baseline found. Recording current count as baseline (skipping optimization).")
        db.conn.execute(
            f"INSERT INTO {db.table('pipeline_logs')} (document_id, task, status, details) VALUES (?, ?, ?, ?)",
            (
                "_milestone_",
                "optimize_milestone",
                "baseline",
                json.dumps({"tier": tier, "nodes_processed": current_count, "elapsed": 0}),
            ),
        )
        return False

    # Find seed nodes: nodes added since last milestone
    # We use ROWID ordering as a proxy for insertion order
    num_new_nodes = current_count - last_processed_count

    # Safety limit: don't try to optimize more than 10K nodes at once
    if num_new_nodes > 10000:
        logger.warning("Too many new nodes (%d). Capping at 10000 for scoped optimization.", num_new_nodes)
        num_new_nodes = 10000
    seed_rows = db.query(f"""
        SELECT node_id FROM {db.table("graph_nodes")}
        ORDER BY ROWID DESC
        LIMIT {num_new_nodes}
    """)
    seed_node_ids = [r[0] for r in seed_rows] if seed_rows else []

    logger.info("Milestone reached: tier %d (at %d nodes, %d new since last). Running scoped optimization...", tier, current_count, len(seed_node_ids))
    t0 = time.perf_counter()

    # Scoped optimization: seed nodes + their 1-hop neighbors
    scope_size = run_scoped_optimization(db, seed_node_ids, iterations=10)

    # Embedding clustering only at larger milestones (expensive, global)
    if tier >= 1000:
        logger.info("Large milestone (%d) - also running embedding clustering...", tier)
        run_embedding_clusters(db)

    elapsed = time.perf_counter() - t0

    # Log milestone with nodes_processed for range scanning
    # UPDATE existing row (avoids duplicate key on _milestone_)
    milestone_details = json.dumps(
        {
            "tier": tier,
            "nodes_processed": current_count,
            "seed_nodes": len(seed_node_ids),
            "scope_size": scope_size,
            "elapsed": round(elapsed, 2),
        }
    )
    updated = db.conn.execute(
        f"UPDATE {db.table('pipeline_logs')} SET status = 'completed', details = ? WHERE document_id = '_milestone_' AND task = 'optimize_milestone'",
        (milestone_details,),
    ).rowcount
    if not updated:
        db.conn.execute(
            f"INSERT INTO {db.table('pipeline_logs')} (document_id, task, status, details) VALUES (?, ?, ?, ?)",
            ("_milestone_", "optimize_milestone", "completed", milestone_details),
        )

    logger.info("Milestone optimization complete in %.1fs (tier=%d, seeds=%d, scope=%d)", elapsed, tier, len(seed_node_ids), scope_size)
    return True


def run(iterations=DEFAULT_ITERATIONS, db=None):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - pipe_06 - %(levelname)s - %(message)s",
    )
    own_db = db is None
    if own_db:
        db = CoreDB()

    run_pagerank(db, iterations=iterations)
    run_hits(db, iterations=HITS_ITERATIONS)
    run_community_detection(db, rounds=COMMUNITY_ROUNDS)
    run_embedding_clusters(db, k=EMBEDDING_CLUSTERS_K)

    logger.info("All graph optimizations complete.")
    if own_db:
        db.close()


if __name__ == "__main__":
    run()
