# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Database connection management for the catalog metadata store.

Uses DuckDB with SQLAlchemy for the local metadata repository.
Registers required extensions (vss, json) and Hamming distance macros
on each new connection.
"""

import logging
import os
import time
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event, text as sa_text
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)

# Database URL from environment (default: DuckDB in current directory)
DATABASE_URL = os.getenv("DATABASE_URL", "duckdb:///catalog.duckdb")

# Connection retry for DuckDB IOException (file lock)
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0  # seconds


def _on_connect(dbapi_connection, connection_record):
    """Load extensions and register macros on each new DuckDB connection."""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("INSTALL vss; LOAD vss;")
        cursor.execute("INSTALL json; LOAD json;")

        # Hamming distance macro for BIT-packed vectors
        cursor.execute(
            "CREATE OR REPLACE MACRO hamming_dist(a, b) AS "
            "(bit_count(xor(a, b)));"
        )

        # UBIGINT decomposition macro: 6 x 64-bit POPCNT for SIMD-friendly Hamming
        cursor.execute(
            """CREATE OR REPLACE MACRO hamming_u6(
            a0, a1, a2, a3, a4, a5, b0, b1, b2, b3, b4, b5
        ) AS
            bit_count(xor(a0, b0))::INTEGER + bit_count(xor(a1, b1))::INTEGER +
            bit_count(xor(a2, b2))::INTEGER + bit_count(xor(a3, b3))::INTEGER +
            bit_count(xor(a4, b4))::INTEGER + bit_count(xor(a5, b5))::INTEGER;"""
        )

    except Exception as e:
        logger.warning(f"Could not load DuckDB extensions or macros: {e}")
    finally:
        cursor.close()


def _create_engine_with_retry():
    """Create SQLAlchemy engine with exponential backoff on DuckDB IOException."""
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            eng = create_engine(DATABASE_URL, echo=False)
            event.listen(eng, "connect", _on_connect)
            with eng.connect() as conn:
                conn.execute(sa_text("SELECT 1"))
            return eng
        except Exception as e:
            last_err = e
            if "IOException" in str(type(e).__name__) or "IOException" in str(e):
                delay = RETRY_BASE_DELAY * (2**attempt)
                logger.warning(
                    "DuckDB IOException on connect (attempt %d/%d), "
                    "retrying in %.1fs: %s",
                    attempt + 1,
                    MAX_RETRIES,
                    delay,
                    e,
                )
                time.sleep(delay)
            else:
                raise
    raise last_err  # type: ignore[misc]


# Module-level engine singleton
engine = _create_engine_with_retry()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session() -> Generator[Session, None, None]:
    """Dependency-injectable session generator (e.g. for FastAPI)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Context manager for database sessions.

    Usage::

        with get_db() as db:
            asset = db.query(Asset).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
