# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""File output with YAML frontmatter and atomic writes."""

import json
import os
import tempfile
from collections.abc import Callable, Mapping
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

from .query_types import BaseMetadata


def json_serial(obj: Any) -> str:
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def write_yaml_frontmatter(f: Any, metadata: BaseMetadata) -> None:
    """Write YAML frontmatter to file."""
    f.write("---\n")
    yaml.dump(metadata.to_dict(), f, default_flow_style=False, sort_keys=False)
    f.write("---\n")


def atomic_write(path: Path, content_writer: Callable[[Any], None]) -> None:
    """Atomic file write using temp file and rename."""
    temp_fd, temp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp", prefix=path.stem + "_")

    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
            content_writer(f)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_path, path)

    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def write_sql_file(path: Path, metadata: BaseMetadata, sql: str) -> None:
    """Write SQL file with YAML frontmatter."""

    def writer(f: Any) -> None:
        write_yaml_frontmatter(f, metadata)
        f.write(sql)

    atomic_write(path, writer)


def write_results_jsonl(path: Path, metadata: BaseMetadata, rows: list[dict[str, Any]]) -> None:
    """Write results JSONL file with YAML frontmatter."""

    def writer(f: Any) -> None:
        write_yaml_frontmatter(f, metadata)

        for row_num, row_data in enumerate(rows):
            row_obj = {"row": row_num, "data": row_data}
            f.write(json.dumps(row_obj, ensure_ascii=False, default=json_serial) + "\n")

    atomic_write(path, writer)


def write_log_jsonl(path: Path, metadata: BaseMetadata, log_entries: list[dict[str, Any]]) -> None:
    """Write log JSONL file with YAML frontmatter."""

    def writer(f: Any) -> None:
        write_yaml_frontmatter(f, metadata)

        for entry in log_entries:
            f.write(json.dumps(entry, ensure_ascii=False, default=json_serial) + "\n")

    atomic_write(path, writer)


def write_config_json(path: Path, metadata: BaseMetadata, config: Mapping[str, Any]) -> None:
    """Write config JSON file with YAML frontmatter embedded as JSON."""
    output: dict[str, Any] = {
        "yaml_frontmatter": metadata.to_dict(),
        **config,
    }

    if "connection_template" in output:
        output["connection_template"] = output["connection_template"].replace("{username}", "[REDACTED]").replace("{password}", "[REDACTED]")

    def writer(f: Any) -> None:
        json.dump(output, f, indent=2, ensure_ascii=False, default=json_serial)

    atomic_write(path, writer)


def write_all_files(
    files: dict[str, Path],
    metadata: BaseMetadata,
    sql: str,
    rows: list[dict[str, Any]],
    log_entries: list[dict[str, Any]],
    config: Mapping[str, Any],
) -> None:
    """Write all 4 output files atomically."""
    write_sql_file(files["sql"], metadata, sql)
    write_results_jsonl(files["results"], metadata, rows)
    write_log_jsonl(files["log"], metadata, log_entries)
    write_config_json(files["config"], metadata, config)
