#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Unit tests verifying DuckDB is a required dependency.

DuckDB is required for AgentDB state management. These tests verify
the dependency is properly installed and functional.

Issue: #125
"""

from packaging import version


class TestDuckDBRequired:
    """Verify DuckDB is installed and functional."""

    def test_duckdb_import(self):
        """Test: DuckDB module is importable (required dependency)."""
        import duckdb  # noqa: F401 - Import is the test

    def test_duckdb_version(self):
        """Test: DuckDB version meets minimum requirement (>=1.4.2).

        Uses packaging.version for robust version comparison that handles
        pre-release versions (e.g., "1.5.0-rc1") correctly.
        """
        import duckdb

        min_version = version.parse("1.4.2")
        current_version = version.parse(duckdb.__version__)

        assert current_version >= min_version, f"DuckDB version {duckdb.__version__} < minimum required 1.4.2"

    def test_duckdb_in_memory_connection(self):
        """Test: DuckDB can create in-memory database."""
        import duckdb

        conn = duckdb.connect(":memory:")
        assert conn is not None
        conn.close()

    def test_duckdb_basic_query(self):
        """Test: DuckDB can execute basic SQL."""
        import duckdb

        conn = duckdb.connect(":memory:")
        result = conn.execute("SELECT 1 AS value").fetchone()
        assert result == (1,)
        conn.close()

    def test_duckdb_table_creation(self):
        """Test: DuckDB can create and query tables (AgentDB pattern)."""
        import duckdb

        conn = duckdb.connect(":memory:")

        # Create table similar to AgentDB schema
        conn.execute("""
            CREATE TABLE test_sync (
                sync_id VARCHAR PRIMARY KEY,
                pattern VARCHAR NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert and query
        conn.execute("INSERT INTO test_sync (sync_id, pattern) VALUES ('test-1', 'phase_1_specify')")
        result = conn.execute("SELECT pattern FROM test_sync WHERE sync_id = 'test-1'").fetchone()
        assert result == ("phase_1_specify",)

        conn.close()
