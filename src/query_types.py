# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Type definitions for query runner, deployer, and pipeline tools."""

from dataclasses import asdict, dataclass
from typing import Any, Literal, TypedDict


class ConfigDict(TypedDict, total=False):
    """Typed configuration dictionary for config.{env}.json."""

    environment: str
    connection_template: str
    server: str
    database: str
    port: int
    timeout: int
    username: str


QueryType = Literal["schema_info", "exploratory", "large_query"]
ToolType = Literal["query_runner", "deployer", "pipeline_runner"]
ExitStatus = Literal["success", "timeout", "error"]

# Statement timeout per query type (seconds)
QUERY_TIMEOUTS: dict[str, int] = {
    "schema_info": 120,
    "exploratory": 600,
    "large_query": 7200,
}


@dataclass
class BaseMetadata:
    """Base metadata for all tool executions."""

    tool_type: ToolType
    execution_timestamp: str  # ISO 8601 UTC
    timestamp_iso8601: str  # Compact format
    slug: str
    runtime_seconds: float
    exit_status: ExitStatus
    python_version: str
    arguments: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return asdict(self)


@dataclass
class QueryMetadata(BaseMetadata):
    """Metadata for a query execution."""

    query_type: QueryType
    row_count: int
    connection_params: dict[str, Any]
    batch_size: int
    expected_batches: int
    actual_batches: int
    mb_per_batch: float
    mb_total: float
    sort_columns: list[str]
    last_processed_value: dict[str, str]
    has_phi: bool
    pyodbc_version: str
    driver_version: str


@dataclass
class DeployMetadata(BaseMetadata):
    """Metadata for a deployment execution."""

    file_path: str
    batch_count: int
    batches_processed: int
    connection_params: dict[str, Any]
    driver_version: str
    pyodbc_version: str
