# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
import json
import logging
import time

import duckdb

DB_PATH = "documents.duckdb"

# Module-level singleton
_db_instance = None

logger = logging.getLogger(__name__)


def get_db(db_path=DB_PATH):
    """Get or create the singleton CoreDB instance."""
    global _db_instance
    if _db_instance is None or _db_instance.conn is None:
        _db_instance = CoreDB(db_path)
    return _db_instance


class CoreDB:
    MAX_RETRIES = 5

    def __init__(self, db_path=DB_PATH, table_prefix=""):
        self.db_path = db_path
        self.table_prefix = table_prefix
        self.conn = self._connect_with_retry()
        self._setup()

    def _connect_with_retry(self):
        """Connect to DuckDB with exponential backoff on IOException."""
        for attempt in range(self.MAX_RETRIES):
            try:
                return duckdb.connect(self.db_path)
            except duckdb.IOException:
                if attempt == self.MAX_RETRIES - 1:
                    raise
                wait = 2**attempt  # 1, 2, 4, 8, 16
                logger.warning(
                    "DuckDB locked (attempt %d/%d), retrying in %ds...",
                    attempt + 1,
                    self.MAX_RETRIES,
                    wait,
                )
                time.sleep(wait)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def table(self, name):
        """Return table name with prefix applied."""
        return f"{self.table_prefix}{name}"

    def _setup(self):
        """Initialize database schema and macros."""
        # Enable 1-bit Hamming Distance Macro
        # Calculates bitwise XOR using xor() function, then counts set bits
        self.conn.execute("""
            CREATE MACRO IF NOT EXISTS hamming_dist(a, b) AS
            bit_count(xor(a, b));
        """)

        # UBIGINT-based Hamming distance: 6 x 64-bit XOR + popcount
        # Cast bit_count results to INTEGER to prevent TINYINT overflow (max 384 > 127)
        self.conn.execute("""
            CREATE MACRO IF NOT EXISTS hamming_u6(
                a0, a1, a2, a3, a4, a5,
                b0, b1, b2, b3, b4, b5
            ) AS
                bit_count(xor(a0, b0))::INTEGER + bit_count(xor(a1, b1))::INTEGER +
                bit_count(xor(a2, b2))::INTEGER + bit_count(xor(a3, b3))::INTEGER +
                bit_count(xor(a4, b4))::INTEGER + bit_count(xor(a5, b5))::INTEGER;
        """)

        self._create_tables()

    def _create_tables(self):
        """Define the Graph RAG schema."""

        # 1. Raw Documents
        self.conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table("raw_documents")} (
                document_id TEXT PRIMARY KEY,
                title TEXT,
                body TEXT,
                body_stripped TEXT,
                source_path TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                processed_status TEXT DEFAULT 'new'
            )
        """)

        # 1b. Attachments table
        # No FK constraint --DuckDB blocks UPDATE on parent rows with FK children
        self.conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table("attachments")} (
                id INTEGER PRIMARY KEY,
                document_id TEXT NOT NULL,
                filename TEXT,
                size_bytes INTEGER
            )
        """)

        # 2. Knowledge Graph (JSON-LD Storage)
        # No FK constraint --DuckDB blocks UPDATE on parent rows with FK children
        self.conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table("knowledge_graphs")} (
                document_id TEXT PRIMARY KEY,
                json_ld JSON,
                body_hash TEXT
            )
        """)

        # 3. Graph Nodes (Entities & Vectors)
        # embedding_bit is a BIT string (384 bits)
        # bit_u0..bit_u5 are 6 x UBIGINT decomposition for fast Hamming distance
        # bit_popcnt is pre-computed popcount for triangle inequality pre-filter
        self.conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table("graph_nodes")} (
                node_id TEXT PRIMARY KEY,
                node_type TEXT,
                name TEXT,
                embedding_bit BIT,
                bit_u0 UBIGINT,
                bit_u1 UBIGINT,
                bit_u2 UBIGINT,
                bit_u3 UBIGINT,
                bit_u4 UBIGINT,
                bit_u5 UBIGINT,
                bit_popcnt USMALLINT,
                pagerank DOUBLE DEFAULT 1.0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 4. Semantic Edges (Relationships)
        self.conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table("semantic_edges")} (
                source_id TEXT,
                target_id TEXT,
                edge_type TEXT,
                weight DOUBLE,
                FOREIGN KEY (source_id) REFERENCES {self.table("graph_nodes")}(node_id),
                FOREIGN KEY (target_id) REFERENCES {self.table("graph_nodes")}(node_id),
                PRIMARY KEY (source_id, target_id, edge_type)
            )
        """)

        # 5. Query Cache (for RAG pipeline)
        self.conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table("query_cache")} (
                cache_key TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                result JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 6. Pipeline Logs (checkpoint/resume)
        self.conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table("pipeline_logs")} (
                document_id TEXT,
                task TEXT,
                status TEXT,
                details JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (document_id, task)
            )
        """)

        # Add metric columns to graph_nodes if missing
        graph_nodes_table = self.table("graph_nodes")
        for col, col_type, default in [
            ("authority_score", "DOUBLE", "0.0"),
            ("hub_score", "DOUBLE", "0.0"),
            ("community_id", "INTEGER", "-1"),
            ("embedding_cluster_id", "INTEGER", "-1"),
        ]:
            try:
                self.conn.execute(f"SELECT {col} FROM {graph_nodes_table} LIMIT 1")
            except Exception:
                self.conn.execute(f"ALTER TABLE {graph_nodes_table} ADD COLUMN {col} {col_type} DEFAULT {default}")

        # Add UBIGINT Hamming columns to graph_nodes if missing (migration)
        for col, col_type in [
            ("bit_u0", "UBIGINT"),
            ("bit_u1", "UBIGINT"),
            ("bit_u2", "UBIGINT"),
            ("bit_u3", "UBIGINT"),
            ("bit_u4", "UBIGINT"),
            ("bit_u5", "UBIGINT"),
            ("bit_popcnt", "USMALLINT"),
        ]:
            try:
                self.conn.execute(f"SELECT {col} FROM {graph_nodes_table} LIMIT 0")
            except Exception:
                self.conn.execute(f"ALTER TABLE {graph_nodes_table} ADD COLUMN {col} {col_type}")

        # Backfill UBIGINT columns from existing embedding_bit data
        self._backfill_ubigint_columns()

        # Add body_hash column to knowledge_graphs if missing
        knowledge_graphs_table = self.table("knowledge_graphs")
        try:
            self.conn.execute(f"SELECT body_hash FROM {knowledge_graphs_table} LIMIT 1")
        except Exception:
            self.conn.execute(f"ALTER TABLE {knowledge_graphs_table} ADD COLUMN body_hash TEXT")

        # === Evaluation Infrastructure Tables (fixed names, no prefix) ===

        # Gold standard for Stage 02 (verify)
        # fixture_order preserves original line number from source JSONL
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS eval_gold_02 (
                document_id TEXT PRIMARY KEY,
                expected_status TEXT NOT NULL,
                reason TEXT,
                fixture_order INTEGER
            )
        """)

        # Gold standard for Stage 03 (decompose)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS eval_gold_03 (
                document_id TEXT PRIMARY KEY,
                expected_summary TEXT,
                expected_entities JSON
            )
        """)

        # Gold standard for Stage 04 (vectorize) - just checks nodes exist
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS eval_gold_04 (
                document_id TEXT PRIMARY KEY,
                expected_node_count INTEGER
            )
        """)

        # Gold standard for Stage 05 (link) - expected edge types
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS eval_gold_05 (
                document_id TEXT PRIMARY KEY,
                expected_edge_types JSON
            )
        """)

        # Experiment tracking
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS eval_experiments (
                experiment_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                email_limit INTEGER,
                stages JSON,
                config JSON,
                status TEXT DEFAULT 'running'
            )
        """)

        # Metrics per experiment/stage
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS eval_metrics (
                experiment_id TEXT,
                stage TEXT,
                metric_name TEXT,
                metric_value DOUBLE,
                details JSON,
                PRIMARY KEY (experiment_id, stage, metric_name)
            )
        """)

        # Performance indexes (include table_prefix in index names for uniqueness)
        prefix = self.table_prefix
        self.conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{prefix}raw_documents_processed_status ON {self.table('raw_documents')}(processed_status)")
        self.conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{prefix}graph_nodes_node_type ON {self.table('graph_nodes')}(node_type)")
        self.conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{prefix}semantic_edges_source_id ON {self.table('semantic_edges')}(source_id)")
        self.conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{prefix}semantic_edges_target_id ON {self.table('semantic_edges')}(target_id)")
        self.conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{prefix}knowledge_graphs_document_id ON {self.table('knowledge_graphs')}(document_id)")
        self.conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{prefix}knowledge_graphs_body_hash ON {self.table('knowledge_graphs')}(body_hash)")

    def _backfill_ubigint_columns(self):
        """Populate bit_u0..bit_u5 and bit_popcnt from existing embedding_bit data.

        Runs once on migration: finds rows where embedding_bit is set but bit_u0 is NULL,
        converts the BIT string to 6 UBIGINTs in Python, and batch-updates.
        """
        graph_nodes_table = self.table("graph_nodes")
        rows = self.conn.execute(f"SELECT node_id, embedding_bit::VARCHAR FROM {graph_nodes_table} WHERE embedding_bit IS NOT NULL AND bit_u0 IS NULL").fetchall()

        if not rows:
            return

        import numpy as np

        logger.info("Backfilling %d graph_nodes with UBIGINT columns...", len(rows))

        updates = []
        for node_id, bit_str in rows:
            if not bit_str or len(bit_str) < 384:
                continue
            bits = np.array([1 if c == "1" else 0 for c in bit_str[:384]], dtype=np.uint8)
            ubigints = []
            for i in range(6):
                chunk = bits[i * 64 : (i + 1) * 64]
                val = int.from_bytes(np.packbits(chunk).tobytes(), "big")
                ubigints.append(val)
            popcount = int(bits.sum())
            updates.append((*ubigints, popcount, node_id))

        if updates:
            self.conn.executemany(
                f"UPDATE {graph_nodes_table} SET bit_u0=?, bit_u1=?, bit_u2=?, bit_u3=?, bit_u4=?, bit_u5=?, bit_popcnt=? WHERE node_id=?",
                updates,
            )
            logger.info("Backfilled %d rows.", len(updates))

    def query(self, sql, params=None):
        if params:
            return self.conn.execute(sql, params).fetchall()
        return self.conn.execute(sql).fetchall()

    def cache_get(self, cache_key):
        """Retrieve a cached query result by key."""
        res = self.conn.execute(
            f"SELECT result FROM {self.table('query_cache')} WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
        if res and res[0]:
            val = res[0]
            if isinstance(val, str):
                return json.loads(val)
            return val
        return None

    def cache_set(self, cache_key, query, result):
        """Store a query result in the cache."""
        result_json = json.dumps(result)
        self.conn.execute(
            f"""
            INSERT INTO {self.table("query_cache")} (cache_key, query, result, created_at)
            VALUES (?, ?, ?, now())
            ON CONFLICT (cache_key) DO UPDATE SET
                result = excluded.result,
                created_at = now()
            """,
            (cache_key, query, result_json),
        )

    def search_nodes_with_citations(self, query_ubigints, query_popcnt, limit=10):
        """Search graph_nodes by UBIGINT Hamming distance with popcount pre-filter.

        Args:
            query_ubigints: List of 6 UBIGINT values from quantize_ubigint().
            query_popcnt: Popcount of the query vector.
            limit: Max results to return.

        Returns list of (node_id, name, node_type, distance, document_id, title,
                         source_path).
        """
        # Use generous pre-filter threshold for retrieval (wider than linking)
        pre_filter_threshold = 120
        return self.conn.execute(
            f"""
            SELECT
                n.node_id,
                n.name,
                n.node_type,
                hamming_u6(n.bit_u0, n.bit_u1, n.bit_u2, n.bit_u3, n.bit_u4, n.bit_u5,
                           ?, ?, ?, ?, ?, ?) AS distance,
                k.document_id,
                r.title,
                r.source_path
            FROM {self.table("graph_nodes")} n
            LEFT JOIN {self.table("knowledge_graphs")} k ON n.node_id = k.document_id
            LEFT JOIN {self.table("raw_documents")} r ON k.document_id = r.document_id
            WHERE n.bit_u0 IS NOT NULL
              AND abs(n.bit_popcnt::INTEGER - ?::INTEGER) <= {pre_filter_threshold}
            ORDER BY distance ASC
            LIMIT ?
            """,
            (*query_ubigints, query_popcnt, limit),
        ).fetchall()

    def expand_nodes_1hop(self, node_ids, max_neighbors=3):
        """Follow semantic_edges to get 1-hop neighbor nodes with document metadata.

        Returns list of (node_id, name, node_type, weight, document_id, title,
                         source_path).
        """
        if not node_ids:
            return []
        placeholders = ",".join(["?"] * len(node_ids))
        return self.conn.execute(
            f"""
            WITH ranked AS (
                SELECT
                    e.source_id,
                    e.target_id,
                    e.weight,
                    ROW_NUMBER() OVER (
                        PARTITION BY e.source_id
                        ORDER BY e.weight DESC
                    ) AS rn
                FROM {self.table("semantic_edges")} e
                WHERE e.source_id IN ({placeholders})
                  AND e.target_id NOT IN ({placeholders})
            )
            SELECT DISTINCT
                t.node_id,
                t.name,
                t.node_type,
                r.weight,
                k.document_id,
                rd.title,
                rd.source_path
            FROM ranked r
            JOIN {self.table("graph_nodes")} t ON r.target_id = t.node_id
            LEFT JOIN {self.table("knowledge_graphs")} k ON t.node_id = k.document_id
            LEFT JOIN {self.table("raw_documents")} rd ON k.document_id = rd.document_id
            WHERE r.rn <= ?
              AND t.name IS NOT NULL
            ORDER BY r.weight DESC
            """,
            (*node_ids, *node_ids, max_neighbors),
        ).fetchall()

    def expand_nodes_nhop(self, node_ids, hops=1, max_neighbors=3):
        """Follow semantic_edges to get N-hop neighbor nodes with document metadata.

        Iteratively expands from seed nodes, collecting unique neighbors at each hop.
        Returns same schema as expand_nodes_1hop for compatibility.
        """
        if not node_ids or hops < 1:
            return []

        all_results = []
        seen_ids = set(node_ids)
        current_seeds = list(node_ids)

        for _hop in range(hops):
            if not current_seeds:
                break

            hop_results = self.expand_nodes_1hop(current_seeds, max_neighbors=max_neighbors)
            new_seeds = []
            for row in hop_results:
                nid = row[0]
                if nid not in seen_ids:
                    seen_ids.add(nid)
                    all_results.append(row)
                    new_seeds.append(nid)
            current_seeds = new_seeds

        return all_results

    # === Evaluation Helper Methods ===

    def eval_setup(self, limit=10):
        """Set up eval tables by copying first N documents by fixture_order.

        Includes both verified and skipped documents (useful for Stage 02 testing).

        Args:
            limit: Number of documents to copy (default 10)

        Returns:
            Number of documents copied
        """
        if self.table_prefix != "eval_":
            raise ValueError("eval_setup requires table_prefix='eval_'")

        # Clear existing eval data
        for table in ["raw_documents", "knowledge_graphs", "graph_nodes", "semantic_edges", "pipeline_logs"]:
            self.conn.execute(f"DELETE FROM {self.table(table)}")

        # Copy first N documents by fixture_order from gold standard
        self.conn.execute(
            f"""
            INSERT INTO {self.table("raw_documents")}
            SELECT r.* FROM raw_documents r
            JOIN eval_gold_02 g ON r.document_id = g.document_id
            ORDER BY g.fixture_order
            LIMIT ?
        """,
            (limit,),
        )

        count = self.conn.execute(f"SELECT COUNT(*) FROM {self.table('raw_documents')}").fetchone()[0]
        return count

    def eval_setup_all(self, limit=10):
        """Set up eval tables with first N documents from gold standard (all statuses).

        Copies documents with status='new' so Stage 02 verify step will process them.
        This enables testing the full pipeline including verification heuristics.

        Uses fixture_order to preserve original source JSONL line order.

        Args:
            limit: Number of documents to copy (default 10)

        Returns:
            Number of documents copied
        """
        if self.table_prefix != "eval_":
            raise ValueError("eval_setup_all requires table_prefix='eval_'")

        # Clear existing eval data
        for table in ["raw_documents", "knowledge_graphs", "graph_nodes", "semantic_edges", "pipeline_logs"]:
            self.conn.execute(f"DELETE FROM {self.table(table)}")

        # Copy first N documents from gold standard (both verified and skipped), ordered by fixture_order
        self.conn.execute(
            f"""
            INSERT INTO {self.table("raw_documents")}
            SELECT r.* FROM raw_documents r
            JOIN eval_gold_02 g ON r.document_id = g.document_id
            ORDER BY g.fixture_order
            LIMIT ?
        """,
            (limit,),
        )

        # Set status to 'new' so verify step will process them
        self.conn.execute(f"""
            UPDATE {self.table("raw_documents")}
            SET processed_status = 'new'
        """)

        count = self.conn.execute(f"SELECT COUNT(*) FROM {self.table('raw_documents')}").fetchone()[0]
        return count

    def eval_setup_verified(self, limit=10):
        """Set up eval tables with first N documents that have gold 'verified' status.

        DEPRECATED: Use eval_setup_all() for full pipeline parity.

        Uses fixture_order to preserve original source JSONL line order.

        Args:
            limit: Number of verified documents to copy (default 10)

        Returns:
            Number of documents copied
        """
        if self.table_prefix != "eval_":
            raise ValueError("eval_setup_verified requires table_prefix='eval_'")

        # Clear existing eval data
        for table in ["raw_documents", "knowledge_graphs", "graph_nodes", "semantic_edges", "pipeline_logs"]:
            self.conn.execute(f"DELETE FROM {self.table(table)}")

        # Copy first N documents that are verified in gold standard, ordered by fixture_order
        self.conn.execute(
            f"""
            INSERT INTO {self.table("raw_documents")}
            SELECT r.* FROM raw_documents r
            JOIN eval_gold_02 g ON r.document_id = g.document_id
            WHERE g.expected_status = 'verified'
            ORDER BY g.fixture_order
            LIMIT ?
        """,
            (limit,),
        )

        # Set their status to verified so pipeline stages will process them
        self.conn.execute(f"""
            UPDATE {self.table("raw_documents")}
            SET processed_status = 'verified'
        """)

        count = self.conn.execute(f"SELECT COUNT(*) FROM {self.table('raw_documents')}").fetchone()[0]
        return count

    def eval_get_gold_02(self, document_ids=None):
        """Get Stage 02 gold standard entries.

        Args:
            document_ids: Optional list of document_ids to filter

        Returns:
            Dict mapping document_id -> {expected_status, reason}
        """
        if document_ids:
            placeholders = ",".join(["?"] * len(document_ids))
            rows = self.conn.execute(
                f"""
                SELECT document_id, expected_status, reason
                FROM eval_gold_02
                WHERE document_id IN ({placeholders})
            """,
                document_ids,
            ).fetchall()
        else:
            rows = self.conn.execute("""
                SELECT document_id, expected_status, reason
                FROM eval_gold_02
            """).fetchall()

        return {did: {"expected_status": status, "reason": reason} for did, status, reason in rows}

    def eval_get_gold_03(self, document_ids=None):
        """Get Stage 03 gold standard entries.

        Args:
            document_ids: Optional list of document_ids to filter

        Returns:
            Dict mapping document_id -> {expected_summary, expected_entities}
        """
        if document_ids:
            placeholders = ",".join(["?"] * len(document_ids))
            rows = self.conn.execute(
                f"""
                SELECT document_id, expected_summary, expected_entities
                FROM eval_gold_03
                WHERE document_id IN ({placeholders})
            """,
                document_ids,
            ).fetchall()
        else:
            rows = self.conn.execute("""
                SELECT document_id, expected_summary, expected_entities
                FROM eval_gold_03
            """).fetchall()

        result = {}
        for did, summary, entities in rows:
            ents = entities if isinstance(entities, list) else json.loads(entities) if entities else []
            result[did] = {"expected_summary": summary, "expected_entities": ents}
        return result

    def eval_store_metric(self, experiment_id, stage, metric_name, metric_value, details=None):
        """Store a metric for an experiment.

        Args:
            experiment_id: Experiment identifier
            stage: Stage number (e.g., "02", "03")
            metric_name: Name of metric (e.g., "precision", "recall", "f1")
            metric_value: Numeric value
            details: Optional JSON details
        """
        self.conn.execute(
            """
            INSERT INTO eval_metrics (experiment_id, stage, metric_name, metric_value, details)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (experiment_id, stage, metric_name) DO UPDATE SET
                metric_value = excluded.metric_value,
                details = excluded.details
        """,
            (experiment_id, stage, metric_name, metric_value, json.dumps(details) if details else None),
        )

    def eval_get_metrics(self, experiment_id=None, stage=None):
        """Get metrics, optionally filtered by experiment and/or stage.

        Returns:
            List of (experiment_id, stage, metric_name, metric_value, details)
        """
        sql = "SELECT experiment_id, stage, metric_name, metric_value, details FROM eval_metrics WHERE 1=1"
        params = []
        if experiment_id:
            sql += " AND experiment_id = ?"
            params.append(experiment_id)
        if stage:
            sql += " AND stage = ?"
            params.append(stage)
        sql += " ORDER BY experiment_id, stage, metric_name"
        return self.conn.execute(sql, params).fetchall()

    def eval_create_experiment(self, name, email_limit, stages, config=None):
        """Create a new experiment record.

        Args:
            name: Experiment name
            email_limit: Number of documents used
            stages: List of stages run
            config: Optional config dict

        Returns:
            experiment_id
        """
        from datetime import UTC, datetime

        experiment_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "_" + name
        self.conn.execute(
            """
            INSERT INTO eval_experiments (experiment_id, name, email_limit, stages, config, status)
            VALUES (?, ?, ?, ?, ?, 'running')
        """,
            (experiment_id, name, email_limit, json.dumps(stages), json.dumps(config) if config else None),
        )
        return experiment_id

    def eval_complete_experiment(self, experiment_id):
        """Mark an experiment as complete."""
        self.conn.execute(
            """
            UPDATE eval_experiments SET status = 'complete' WHERE experiment_id = ?
        """,
            (experiment_id,),
        )

    def eval_list_experiments(self):
        """List all experiments.

        Returns:
            List of (experiment_id, name, created_at, email_limit, stages, status)
        """
        return self.conn.execute("""
            SELECT experiment_id, name, created_at, email_limit, stages, status
            FROM eval_experiments
            ORDER BY created_at DESC
        """).fetchall()

    def eval_table_counts(self):
        """Get row counts for eval_ prefixed tables.

        Returns:
            Dict mapping table name to count
        """
        if self.table_prefix != "eval_":
            raise ValueError("eval_table_counts requires table_prefix='eval_'")

        tables = ["raw_documents", "knowledge_graphs", "graph_nodes", "semantic_edges", "pipeline_logs"]
        counts = {}
        for table in tables:
            count = self.conn.execute(f"SELECT COUNT(*) FROM {self.table(table)}").fetchone()[0]
            counts[self.table(table)] = count
        return counts

    def close(self):
        global _db_instance
        self.conn.close()
        self.conn = None
        if _db_instance is self:
            _db_instance = None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db = CoreDB()
    db.close()
