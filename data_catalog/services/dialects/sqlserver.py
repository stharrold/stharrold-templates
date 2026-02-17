# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""SQL Server / Azure Synapse dialect for the data catalog pipeline.

This is a skip-on-update file -- customize for your source database.

CUSTOMIZE: If your source is not SQL Server, create a new dialect
subclass (e.g. ``PostgreSQLDialect``) and update
``data_catalog/services/dialects/__init__.py`` to import it.
"""

from __future__ import annotations

import logging
from typing import Any

from data_catalog.services.sql_dialect import SQLDialect
from data_catalog.utils.sql_safety import validate_identifier

logger = logging.getLogger(__name__)

# CUSTOMIZE: Adjust timeout values for your environment.
TIMEOUT_CTAS = 600  # 10 min -- temp table creation
TIMEOUT_COUNT = 300  # 5 min -- COUNT_BIG(*)
TIMEOUT_DISTINCT = 600  # 10 min -- COUNT_BIG(DISTINCT ...)
TIMEOUT_UNPIVOT = 300  # 5 min -- UNPIVOT frequency queries

# CUSTOMIZE: Synapse-specific error codes to handle gracefully.
SYNAPSE_ERROR_NESTING = "102043"  # nested too deeply
SYNAPSE_ERROR_TRANSACTION = "111214"  # transaction corruption
SYNAPSE_ERROR_NONDETERMINISTIC = "107085"  # non-deterministic operation


class SQLServerDialect(SQLDialect):
    """SQL Server / Azure Synapse Analytics dialect.

    Generates T-SQL with Synapse-specific optimizations:
    - ``BINARY_CHECKSUM()`` modulo sampling (deterministic)
    - ``COUNT_BIG(DISTINCT ...)`` for cardinality measurement
    - ``CREATE TABLE #temp WITH (DISTRIBUTION = ROUND_ROBIN) AS SELECT ...``
    - ``UNPIVOT`` for batched frequency scanning
    - ``FULL OUTER JOIN`` with hash-distributed temp tables for FK validation

    CUSTOMIZE: Override methods if your SQL Server version or configuration
    requires different syntax (e.g. on-premises vs. Azure Synapse).
    """

    # ------------------------------------------------------------------
    # Row counting
    # ------------------------------------------------------------------

    def row_count_query(self, schema: str, table: str) -> str:
        validate_identifier(schema)
        validate_identifier(table)
        # Try DMV first (fast for tables), fall back to COUNT for views
        return (
            f"SELECT COUNT_BIG(*) AS row_count "
            f"FROM [{schema}].[{table}]"
        )

    # ------------------------------------------------------------------
    # Column metadata
    # ------------------------------------------------------------------

    def column_metadata_query(self, schema: str, table: str) -> str:
        validate_identifier(schema)
        validate_identifier(table)
        return (
            "SELECT COLUMN_NAME, DATA_TYPE, ORDINAL_POSITION "
            "FROM INFORMATION_SCHEMA.COLUMNS "
            f"WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table}' "
            "ORDER BY ORDINAL_POSITION"
        )

    # ------------------------------------------------------------------
    # Sample table management
    # ------------------------------------------------------------------

    def create_sample_table(
        self,
        temp_name: str,
        schema: str,
        table: str,
        seed_col: str,
        pct: float,
    ) -> str:
        validate_identifier(schema)
        validate_identifier(table)
        validate_identifier(seed_col)

        if pct >= 100:
            return (
                f"CREATE TABLE {temp_name} "
                f"WITH (DISTRIBUTION = ROUND_ROBIN) AS "
                f"SELECT * FROM [{schema}].[{table}]"
            )
        else:
            modulo = int(100 / pct)
            return (
                f"CREATE TABLE {temp_name} "
                f"WITH (DISTRIBUTION = ROUND_ROBIN) AS "
                f"SELECT * FROM [{schema}].[{table}] "
                f"WHERE ABS(CAST(BINARY_CHECKSUM([{seed_col}]) "
                f"AS BIGINT)) % {modulo} = 0"
            )

    def drop_temp_table(self, name: str) -> str:
        return (
            f"IF OBJECT_ID('tempdb..{name}') IS NOT NULL "
            f"DROP TABLE {name}"
        )

    # ------------------------------------------------------------------
    # Cardinality / PK discovery
    # ------------------------------------------------------------------

    def count_distinct(
        self,
        source: str,
        columns: list[str],
        composites: list[list[str]] | None = None,
    ) -> str:
        exprs = ["COUNT_BIG(*) AS _row_count"]
        for i, col in enumerate(columns):
            validate_identifier(col)
            exprs.append(
                f"COUNT_BIG(DISTINCT [{col}]) AS [card_{i}]"
            )
        for j, comp in enumerate(composites or []):
            for c in comp:
                validate_identifier(c)
            concat_expr = " + CHAR(124) + ".join(
                f"ISNULL(CAST([{c}] AS NVARCHAR(MAX)), '')" for c in comp
            )
            exprs.append(
                f"COUNT_BIG(DISTINCT ({concat_expr})) AS [comp_{j}]"
            )
        return f"SELECT {', '.join(exprs)} FROM {source}"

    def seed_column_query(
        self,
        schema: str,
        table: str,
        columns: list[str],
        top_n: int = 10000,
    ) -> str:
        validate_identifier(schema)
        validate_identifier(table)
        exprs = []
        for i, col in enumerate(columns):
            validate_identifier(col)
            exprs.append(f"COUNT(DISTINCT [{col}]) AS [sel_{i}]")
        return (
            f"SELECT {', '.join(exprs)} FROM "
            f"(SELECT TOP {top_n} * FROM [{schema}].[{table}]) AS _sample"
        )

    # ------------------------------------------------------------------
    # Value frequency scanning
    # ------------------------------------------------------------------

    def frequency_query(
        self,
        source: str,
        column: str,
        top_n: int = 100,
    ) -> str:
        validate_identifier(column)
        return (
            f"SELECT TOP {top_n} [{column}] AS val, "
            f"COUNT_BIG(*) AS freq "
            f"FROM {source} "
            f"GROUP BY [{column}] "
            f"ORDER BY freq DESC"
        )

    def unpivot_frequency_query(
        self,
        source: str,
        columns: list[str],
        top_n: int = 100,
    ) -> str:
        for c in columns:
            validate_identifier(c)
        col_list = ", ".join(f"[{c}]" for c in columns)
        return (
            f"SELECT col_name, col_value, freq FROM ("
            f"  SELECT col_name, col_value, COUNT_BIG(*) AS freq, "
            f"    ROW_NUMBER() OVER (PARTITION BY col_name ORDER BY COUNT_BIG(*) DESC) AS rn "
            f"  FROM ("
            f"    SELECT col_name, CAST(col_value AS NVARCHAR(255)) AS col_value "
            f"    FROM {source} "
            f"    UNPIVOT (col_value FOR col_name IN ({col_list})) AS u"
            f"  ) AS raw_vals "
            f"  GROUP BY col_name, col_value"
            f") AS ranked WHERE rn <= {top_n}"
        )

    # ------------------------------------------------------------------
    # FK validation
    # ------------------------------------------------------------------

    def fk_validation_query(
        self,
        fk_table: str,
        pk_table: str,
        column_mappings: list[tuple[str, str]],
        sample_pct: float = 100.0,
        seed_col: str | None = None,
    ) -> str:
        for fk_col, pk_col in column_mappings:
            validate_identifier(fk_col)
            validate_identifier(pk_col)

        join_conditions = " AND ".join(
            f"fk.[{fk_col}] = pk.[{pk_col}]"
            for fk_col, pk_col in column_mappings
        )
        fk_null_checks = " AND ".join(
            f"fk.[{fk_col}] IS NOT NULL"
            for fk_col, _ in column_mappings
        )
        pk_null_checks = " AND ".join(
            f"pk.[{pk_col}] IS NOT NULL"
            for _, pk_col in column_mappings
        )

        # Optional sampling on FK side
        fk_where = ""
        if sample_pct < 100 and seed_col:
            validate_identifier(seed_col)
            modulo = int(100 / sample_pct)
            fk_where = (
                f" WHERE ABS(CAST(BINARY_CHECKSUM([{seed_col}]) "
                f"AS BIGINT)) % {modulo} = 0"
            )

        return (
            f"SELECT "
            f"  SUM(CASE WHEN {fk_null_checks} AND {pk_null_checks} THEN 1 ELSE 0 END) "
            f"    AS match_count, "
            f"  SUM(CASE WHEN {fk_null_checks} AND NOT ({pk_null_checks}) THEN 1 ELSE 0 END) "
            f"    AS orphan_count, "
            f"  SUM(CASE WHEN NOT ({fk_null_checks}) AND {pk_null_checks} THEN 1 ELSE 0 END) "
            f"    AS pk_only_count "
            f"FROM (SELECT * FROM {fk_table}{fk_where}) AS fk "
            f"FULL OUTER JOIN {pk_table} AS pk ON {join_conditions}"
        )

    def create_hash_temp_table(
        self,
        temp_name: str,
        schema: str,
        table: str,
        columns: list[str],
    ) -> str:
        validate_identifier(schema)
        validate_identifier(table)
        for c in columns:
            validate_identifier(c)
        col_list = ", ".join(f"[{c}]" for c in columns)
        hash_col = columns[0]
        return (
            f"CREATE TABLE {temp_name} "
            f"WITH (DISTRIBUTION = HASH([{hash_col}])) AS "
            f"SELECT DISTINCT {col_list} FROM [{schema}].[{table}]"
        )

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def drain_cursor(self, cursor: Any) -> None:
        """Drain pending result sets (pyodbc ``nextset()`` pattern)."""
        try:
            while cursor.nextset():
                pass
        except Exception:
            pass

    def set_timeout(self, cursor: Any, seconds: int) -> int:
        """Set pyodbc connection timeout, return previous value."""
        old = cursor.connection.timeout
        cursor.connection.timeout = seconds
        return old

    def check_cursor_health(self, cursor: Any) -> bool:
        """Test cursor health with ``SELECT 1``."""
        try:
            cursor.execute("SELECT 1")
            cursor.fetchone()
            return True
        except Exception:
            return False
