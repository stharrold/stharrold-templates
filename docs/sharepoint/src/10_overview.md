# Project Documentation

<!-- last_built_utc: PLACEHOLDER -->
<!-- last_built_commit: PLACEHOLDER -->

## Overview

This project uses a Python-orchestrated SQL Server ETL pipeline to execute stored procedures in dependency order. Each pipeline run produces auditable JSONL logs with YAML frontmatter.

## Architecture

- **Pipeline orchestrator** (`src/execute_pipeline.py`): Executes steps defined in `pipeline_config.json`
- **Query runner** (`src/query_runner.py`): Ad-hoc query execution with paginated output
- **Deployer** (`src/deployer.py`): SQL file deployment with GO-batch splitting
- **Config validator** (`src/config_validator.py`): Validates `config.{env}.json` against schema

## Getting Started

```bash
# Install dependencies
uv sync

# Run pipeline (dev environment)
uv run python -m src.execute_pipeline --environment dev

# Deploy a SQL file
uv run python -m src.deployer sql/v1/example_view.sql --environment dev

# Run a query
uv run python -m src.query_runner --sql-file sql/v1/example_view.sql --query-type schema_info --environment dev
```
