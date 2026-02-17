# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Shared test fixtures for the data catalog test suite."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from data_catalog.db.models import Base


@pytest.fixture()
def db_engine():
    """Create an in-memory DuckDB engine with all tables."""
    engine = create_engine("duckdb:///:memory:")

    with engine.connect() as conn:
        # Install and load extensions
        conn.execute(text("INSTALL vss; LOAD vss;"))
        conn.execute(text("INSTALL json; LOAD json;"))
        # Register hamming_dist macro (xor() function, not # operator)
        conn.execute(text("""
            CREATE OR REPLACE MACRO hamming_dist(a, b) AS
            bit_count(xor(a::BIT, b::BIT))
        """))
        conn.commit()

    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db(db_engine) -> Session:
    """Create a fresh database session for each test."""
    session_factory = sessionmaker(bind=db_engine)
    session = session_factory()
    yield session
    session.close()
