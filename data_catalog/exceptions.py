# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Exception hierarchy for the data catalog application.

All catalog-specific exceptions inherit from CatalogError, making it
easy to catch all catalog errors in a single handler.
"""


class CatalogError(Exception):
    """Base exception for all catalog errors."""

    pass


class DiscoveryError(CatalogError):
    """Error during PK/FK discovery or grain analysis."""

    pass


class ValidationError(CatalogError):
    """Error during data validation (FK validation, uniqueness checks)."""

    pass


class ConfigError(CatalogError):
    """Error loading or parsing configuration files."""

    pass


class ConnectionError(CatalogError):
    """Error connecting to a database (catalog DB or source database)."""

    pass


class PipelineError(CatalogError):
    """Error during pipeline orchestration."""

    pass
