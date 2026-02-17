# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
# CUSTOMIZE: Import your dialect implementation here.
# The default ships with a SQL Server / Azure Synapse dialect.
"""SQL dialect implementations for the data catalog pipeline."""

from data_catalog.services.dialects.sqlserver import SQLServerDialect

__all__ = ["SQLServerDialect"]
