# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Abstract base class for source database SQL generation.

The data catalog pipeline generates dynamic SQL for PK discovery, FK
validation, cardinality scanning, and frequency analysis.  Different
source databases (SQL Server, PostgreSQL, Snowflake, etc.) require
different SQL syntax.  This ABC defines the interface that all dialect
implementations must satisfy.

Create a concrete subclass for your source database and pass an
instance to every service that queries the source.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SQLDialect(ABC):
    """Abstract base class for source database SQL generation.

    Every service that builds raw SQL against the source database
    accepts a ``dialect`` argument and delegates SQL string
    construction to the dialect.

    Subclasses MUST implement all abstract methods.
    """

    # ------------------------------------------------------------------
    # Row counting
    # ------------------------------------------------------------------

    @abstractmethod
    def row_count_query(self, schema: str, table: str) -> str:
        """Return SQL that yields a single integer row count.

        May use DMV/catalog shortcuts when available.
        """
        ...

    # ------------------------------------------------------------------
    # Column metadata
    # ------------------------------------------------------------------

    @abstractmethod
    def column_metadata_query(self, schema: str, table: str) -> str:
        """Return SQL that yields (column_name, data_type, ordinal_position)."""
        ...

    # ------------------------------------------------------------------
    # Sample table management
    # ------------------------------------------------------------------

    @abstractmethod
    def create_sample_table(
        self,
        temp_name: str,
        schema: str,
        table: str,
        seed_col: str,
        pct: float,
    ) -> str:
        """Return CREATE TABLE ... AS SELECT for a sampled temp table.

        Args:
            temp_name: Name for the temp table (e.g. ``#pool_1x0_123``).
            schema: Source schema name.
            table: Source table name.
            seed_col: Column used for deterministic sampling (hash-based).
            pct: Sampling percentage (0.1 - 100).  100 means full copy.
        """
        ...

    @abstractmethod
    def drop_temp_table(self, name: str) -> str:
        """Return SQL to conditionally drop a temp table."""
        ...

    # ------------------------------------------------------------------
    # Cardinality / PK discovery
    # ------------------------------------------------------------------

    @abstractmethod
    def count_distinct(
        self,
        source: str,
        columns: list[str],
        composites: list[list[str]] | None = None,
    ) -> str:
        """Return SELECT with COUNT DISTINCT for each column + composites.

        The query should also include ``COUNT(*) AS _row_count``.

        Args:
            source: Table or temp-table name to query.
            columns: Single columns to measure.
            composites: Optional list of column-lists for composite distinctness.
        """
        ...

    @abstractmethod
    def seed_column_query(
        self,
        schema: str,
        table: str,
        columns: list[str],
        top_n: int = 10000,
    ) -> str:
        """Return SQL to find the highest-cardinality column from a small sample."""
        ...

    # ------------------------------------------------------------------
    # Value frequency scanning
    # ------------------------------------------------------------------

    @abstractmethod
    def frequency_query(
        self,
        source: str,
        column: str,
        top_n: int = 100,
    ) -> str:
        """Return SQL for top-N value frequencies of a single column."""
        ...

    @abstractmethod
    def unpivot_frequency_query(
        self,
        source: str,
        columns: list[str],
        top_n: int = 100,
    ) -> str:
        """Return SQL for batched frequency scan using UNPIVOT (or equivalent).

        Not all databases support UNPIVOT; fall back to per-column queries
        when unavailable.
        """
        ...

    # ------------------------------------------------------------------
    # FK validation
    # ------------------------------------------------------------------

    @abstractmethod
    def fk_validation_query(
        self,
        fk_table: str,
        pk_table: str,
        column_mappings: list[tuple[str, str]],
        sample_pct: float = 100.0,
        seed_col: str | None = None,
    ) -> str:
        """Return FULL OUTER JOIN query for FK validation.

        Must return three counts:
        - ``match_count``: FK values with matching PK
        - ``orphan_count``: FK values without PK match
        - ``pk_only_count``: PK values without FK reference
        """
        ...

    @abstractmethod
    def create_hash_temp_table(
        self,
        temp_name: str,
        schema: str,
        table: str,
        columns: list[str],
    ) -> str:
        """Return SQL to create a hash-distributed temp table for FK joins.

        Hash distribution on the join key is critical for FK validation
        performance on distributed databases.
        """
        ...

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    @abstractmethod
    def drain_cursor(self, cursor: Any) -> None:
        """Drain pending result sets to prevent 'Connection is busy' errors."""
        ...

    @abstractmethod
    def set_timeout(self, cursor: Any, seconds: int) -> int:
        """Set query timeout on cursor, returning the previous value."""
        ...

    @abstractmethod
    def check_cursor_health(self, cursor: Any) -> bool:
        """Return True if cursor connection is healthy (e.g. ``SELECT 1``)."""
        ...
