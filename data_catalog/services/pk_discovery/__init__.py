# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Primary Key Discovery Algorithm -- Progressive Scanning.

This package implements a progressive scanning algorithm for efficient
primary key discovery on large datasets (100M+ rows).

The algorithm uses inverse progression of row samples vs column subsets
to eliminate poor candidates early, achieving 40-60% runtime reduction
compared to naive full-table approaches.

Modules:
    models: Data classes for scan configuration and results
    scanner: ProgressiveScanner orchestration class
    decision: Decision engine for candidate management

Example::

    from data_catalog.services.pk_discovery import ProgressiveScanner
    from data_catalog.services.dialects import SQLServerDialect

    dialect = SQLServerDialect()
    scanner = ProgressiveScanner(cursor, dialect=dialect)
    result = scanner.scan("[dbo].[Orders]")
    print(result.primary_key)  # ['OrderID']
"""

from data_catalog.services.pk_discovery.models import (
    ColumnCandidate,
    CompositeCandidate,
    Decision,
    ScanResult,
    ScanStep,
    StepResult,
)
from data_catalog.services.pk_discovery.decision import DecisionEngine
from data_catalog.services.pk_discovery.scanner import ProgressiveScanner

__all__ = [
    "ScanStep",
    "ColumnCandidate",
    "CompositeCandidate",
    "StepResult",
    "ScanResult",
    "Decision",
    "ProgressiveScanner",
    "DecisionEngine",
]
