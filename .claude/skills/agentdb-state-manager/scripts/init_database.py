#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Initialize AgentDB schema for workflow state tracking.

This script initializes the AgentDB database with the canonical schema for
workflow state management. It creates tables, indexes, and loads state
definitions from workflow-states.json.

Usage:
    python init_database.py [--session-id SESSION_ID]

If --session-id is not provided, generates timestamp-based ID.

Constants:
- SCHEMA_VERSION: Current schema version
  Rationale: Track schema evolution for migrations
- WORKFLOW_STATES_PATH: Path to workflow-states.json
  Rationale: Single source of truth for state definitions
"""

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add workflow-utilities to path for worktree_context
sys.path.insert(
    0,
    str(Path(__file__).parent.parent.parent / "workflow-utilities" / "scripts"),
)

# Constants with documented rationale
SCHEMA_VERSION = "2.0.0"  # Current schema version for migrations
WORKFLOW_STATES_PATH = Path(__file__).parent.parent / "templates" / "workflow-states.json"


def get_default_db_path() -> Path:
    """Get default database path in worktree state directory.

    Returns:
        Path to agentdb.duckdb in .claude-state/ directory.
        Falls back to current directory if worktree detection fails.
    """
    try:
        from worktree_context import get_state_dir

        return get_state_dir() / "agentdb.duckdb"
    except (ImportError, RuntimeError):
        # Fallback for non-git environments or missing module
        return Path("agentdb.duckdb")


# ANSI color codes
class Colors:
    """ANSI color codes for terminal output."""

    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    END = "\033[0m"


def error_exit(message: str, code: int = 1) -> None:
    """Print error message and exit.

    Args:
        message: Error message to display
        code: Exit code (default 1)
    """
    print(f"{Colors.RED}[FAIL] Error:{Colors.END} {message}", file=sys.stderr)
    sys.exit(code)


def success(message: str) -> None:
    """Print success message.

    Args:
        message: Success message to display
    """
    print(f"{Colors.GREEN}[OK]{Colors.END} {message}")


def info(message: str) -> None:
    """Print info message.

    Args:
        message: Info message to display
    """
    print(f"{Colors.BLUE}[INFO]{Colors.END} {message}")


def warning(message: str) -> None:
    """Print warning message.

    Args:
        message: Warning message to display
    """
    print(f"{Colors.YELLOW}[WARN]{Colors.END} {message}")


def generate_session_id() -> str:
    """Generate timestamp-based session ID for AgentDB.

    Returns:
        16-character hex session ID

    Rationale: Timestamp-based IDs are reproducible within a timeframe,
    providing a balance between uniqueness and consistency.
    """
    current_time = datetime.now(UTC).isoformat()
    return hashlib.md5(current_time.encode()).hexdigest()[:16]


def load_workflow_states() -> dict[str, Any]:
    """Load canonical state definitions from workflow-states.json.

    Returns:
        Dictionary of state definitions

    Raises:
        FileNotFoundError: If workflow-states.json not found
        json.JSONDecodeError: If JSON is malformed
    """
    if not WORKFLOW_STATES_PATH.exists():
        error_exit(f"workflow-states.json not found: {WORKFLOW_STATES_PATH}")

    info(f"Loading state definitions from {WORKFLOW_STATES_PATH.name}...")

    try:
        with open(WORKFLOW_STATES_PATH, encoding="utf-8") as f:
            states = json.load(f)
        success(f"Loaded {len(states.get('states', {}))} object types")
        return states
    except json.JSONDecodeError as e:
        error_exit(f"Invalid JSON in workflow-states.json: {e}")
    except Exception as e:
        error_exit(f"Failed to load workflow-states.json: {e}")


def create_schema(session_id: str, workflow_states: dict[str, Any], db_path: Path) -> bool:
    """Create AgentDB schema with tables and indexes.

    Args:
        session_id: AgentDB session identifier
        workflow_states: State definitions from workflow-states.json
        db_path: Path to DuckDB database file

    Returns:
        True if schema created successfully, False otherwise
    """
    info("Creating AgentDB schema...")

    sql_statements = [
        # Schema metadata table (tracks schema version)
        """
        CREATE TABLE IF NOT EXISTS schema_metadata (
            schema_name VARCHAR PRIMARY KEY,
            schema_version VARCHAR NOT NULL,
            applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            applied_by VARCHAR NOT NULL,
            description TEXT
        );
        """,
        # Insert schema version record
        f"""
        INSERT INTO schema_metadata (schema_name, schema_version, applied_by, description)
        VALUES (
            'agentdb_sync_schema',
            '{SCHEMA_VERSION}',
            'gemini-code',
            'AgentDB synchronization schema for workflow state tracking'
        )
        ON CONFLICT (schema_name) DO NOTHING;
        """,
        # Agent synchronizations table (main table for record_sync.py + sync_engine.py)
        """
        CREATE TABLE IF NOT EXISTS agent_synchronizations (
            sync_id VARCHAR PRIMARY KEY,
            agent_id VARCHAR NOT NULL,
            worktree_path VARCHAR,
            sync_type VARCHAR NOT NULL,
            source_location VARCHAR NOT NULL,
            target_location VARCHAR NOT NULL,
            pattern VARCHAR NOT NULL,
            status VARCHAR NOT NULL CHECK (status IN (
                'pending', 'in_progress', 'completed', 'failed', 'rolled_back'
            )),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            created_by VARCHAR NOT NULL,
            metadata JSON,
            -- Phase 2 fields for SynchronizationEngine (issue #160)
            trigger_agent_id VARCHAR,
            trigger_action VARCHAR,
            trigger_pattern JSON,
            target_agent_id VARCHAR,
            target_action VARCHAR,
            priority INTEGER DEFAULT 100,
            enabled BOOLEAN DEFAULT TRUE
        );
        """,
        # Indexes for agent_synchronizations
        """
        CREATE INDEX IF NOT EXISTS idx_sync_agent ON agent_synchronizations(agent_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_sync_status ON agent_synchronizations(status);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_sync_created ON agent_synchronizations(created_at DESC);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_sync_pattern ON agent_synchronizations(pattern);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_sync_worktree ON agent_synchronizations(worktree_path);
        """,
        # Phase 2 indexes for SynchronizationEngine queries (issue #160)
        """
        CREATE INDEX IF NOT EXISTS idx_sync_trigger ON agent_synchronizations(trigger_agent_id, trigger_action);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_sync_target ON agent_synchronizations(target_agent_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_sync_enabled ON agent_synchronizations(enabled);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_sync_matching ON agent_synchronizations(
            trigger_agent_id, trigger_action, enabled, priority DESC
        );
        """,
        # Sync executions table (Phase 1 + Phase 2 columns)
        """
        CREATE TABLE IF NOT EXISTS sync_executions (
            execution_id VARCHAR PRIMARY KEY,
            sync_id VARCHAR NOT NULL REFERENCES agent_synchronizations(sync_id) ON DELETE RESTRICT,
            execution_order INTEGER NOT NULL,
            operation_type VARCHAR NOT NULL,
            file_path VARCHAR,
            phi_accessed BOOLEAN NOT NULL DEFAULT FALSE,
            phi_justification TEXT,
            operation_result VARCHAR,
            error_message TEXT,
            started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            duration_ms INTEGER,
            checksum_before VARCHAR,
            checksum_after VARCHAR,
            metadata JSON,
            -- Phase 2 fields (issue #160)
            provenance_hash VARCHAR(64),
            trigger_state_snapshot JSON,
            exec_status VARCHAR
        );
        """,
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_exec_provenance_unique ON sync_executions(provenance_hash);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_exec_status ON sync_executions(exec_status);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_exec_sync_status ON sync_executions(sync_id, exec_status);
        """,
        # Sync audit trail table (healthcare compliance, APPEND-ONLY)
        """
        CREATE TABLE IF NOT EXISTS sync_audit_trail (
            audit_id VARCHAR PRIMARY KEY,
            sync_id VARCHAR NOT NULL REFERENCES agent_synchronizations(sync_id) ON DELETE RESTRICT,
            execution_id VARCHAR REFERENCES sync_executions(execution_id) ON DELETE RESTRICT,
            event_type VARCHAR NOT NULL,
            actor VARCHAR NOT NULL,
            actor_role VARCHAR NOT NULL,
            timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            phi_involved BOOLEAN NOT NULL DEFAULT FALSE,
            compliance_context JSON NOT NULL,
            event_details JSON NOT NULL,
            ip_address VARCHAR,
            session_id VARCHAR
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_audit_sync ON sync_audit_trail(sync_id, timestamp DESC);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_audit_execution ON sync_audit_trail(execution_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_audit_event ON sync_audit_trail(event_type);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON sync_audit_trail(timestamp DESC);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_audit_phi ON sync_audit_trail(phi_involved);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_audit_session ON sync_audit_trail(session_id);
        """,
        # Session metadata table (for workflow state tracking)
        """
        CREATE TABLE IF NOT EXISTS session_metadata (
            key VARCHAR PRIMARY KEY,
            value VARCHAR
        );
        """,
        # Insert session metadata (parameterized - see _insert_session_metadata)
        # Workflow records table (for workflow state queries)
        """
        CREATE TABLE IF NOT EXISTS workflow_records (
            record_id UUID PRIMARY KEY DEFAULT uuid(),
            record_datetimestamp TIMESTAMP DEFAULT current_timestamp,
            object_id VARCHAR NOT NULL,
            object_type VARCHAR NOT NULL,
            object_state VARCHAR NOT NULL,
            object_metadata JSON
        );
        """,
        # Indexes for workflow_records
        """
        CREATE INDEX IF NOT EXISTS idx_records_object
        ON workflow_records(object_id, record_datetimestamp DESC);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_records_type_state
        ON workflow_records(object_type, object_state);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_records_timestamp
        ON workflow_records(record_datetimestamp);
        """,
        # State transitions view for analysis
        """
        CREATE OR REPLACE VIEW state_transitions AS
        SELECT
            record_id,
            object_id,
            object_type,
            LAG(object_state) OVER (PARTITION BY object_id ORDER BY record_datetimestamp) as from_state,
            object_state as to_state,
            record_datetimestamp
        FROM workflow_records;
        """,
        # Sync status view
        """
        CREATE OR REPLACE VIEW v_current_sync_status AS
        SELECT
            sync_id,
            agent_id,
            worktree_path,
            sync_type,
            pattern,
            status,
            created_at,
            completed_at,
            created_by
        FROM agent_synchronizations
        ORDER BY created_at DESC;
        """,
    ]

    # Execute SQL statements against DuckDB
    try:
        import duckdb

        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = duckdb.connect(str(db_path))

        for i, sql in enumerate(sql_statements, 1):
            try:
                conn.execute(sql)
            except Exception as e:
                warning(f"Statement {i} warning: {e}")
                # Continue - some statements may fail if already exists

        # Insert session metadata using parameterized queries (prevent SQL injection)
        workflow_version = workflow_states.get("version", "unknown")
        session_rows = [
            ("session_id", session_id),
            ("schema_version", SCHEMA_VERSION),
            ("workflow_version", workflow_version),
        ]
        for key, value in session_rows:
            try:
                conn.execute(
                    "INSERT INTO session_metadata (key, value) VALUES (?, ?) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
                    [key, value],
                )
            except Exception as e:
                warning(f"Session metadata '{key}' warning: {e}")
        # initialized_at uses current_timestamp (no user input)
        init_at_sql = (
            "INSERT INTO session_metadata (key, value) "
            "VALUES ('initialized_at', CAST(current_timestamp AS VARCHAR)) "
            "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
        )
        try:
            conn.execute(init_at_sql)
        except Exception as e:
            warning(f"Session metadata 'initialized_at' warning: {e}")

        conn.close()
        success(f"Schema created in {db_path}")
        return True

    except ImportError:
        error_exit("DuckDB not installed. Run: uv add duckdb")
    except Exception as e:
        error_exit(f"Failed to create schema: {e}")

    return False


def validate_schema(db_path: Path) -> bool:
    """Validate that schema was created correctly.

    Args:
        db_path: Path to DuckDB database file

    Returns:
        True if validation passed, False otherwise
    """
    info("Validating schema...")

    required_tables = ["agent_synchronizations", "session_metadata", "workflow_records", "schema_metadata", "sync_executions", "sync_audit_trail"]

    try:
        import duckdb

        conn = duckdb.connect(str(db_path))

        # Check all required tables exist
        for table in required_tables:
            result = conn.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{table}'").fetchone()
            if result[0] == 0:
                error_exit(f"Table '{table}' not found in database")
            success(f"Table '{table}' exists")

        conn.close()
        success("Schema validation passed")
        return True

    except ImportError:
        error_exit("DuckDB not installed. Run: uv add duckdb")
    except Exception as e:
        error_exit(f"Schema validation failed: {e}")

    return False


def print_summary(session_id: str, workflow_states: dict[str, Any], db_path: Path) -> None:
    """Print initialization summary.

    Args:
        session_id: AgentDB session identifier
        workflow_states: Loaded state definitions
        db_path: Path to DuckDB database file
    """
    print(f"\n{Colors.BOLD}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}AgentDB Initialization Complete{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 70}{Colors.END}\n")

    print(f"{Colors.BLUE}Database:{Colors.END} {db_path}")
    print(f"{Colors.BLUE}Session ID:{Colors.END} {session_id}")
    print(f"{Colors.BLUE}Schema Version:{Colors.END} {SCHEMA_VERSION}")
    print(f"{Colors.BLUE}Workflow Version:{Colors.END} {workflow_states.get('version', 'unknown')}")

    print(f"\n{Colors.BOLD}Loaded State Definitions:{Colors.END}")
    for obj_type, description in workflow_states.get("object_types", {}).items():
        state_count = len(workflow_states.get("states", {}).get(obj_type, {}))
        print(f"  * {obj_type}: {state_count} states - {description}")

    print(f"\n{Colors.BOLD}Created Tables:{Colors.END}")
    print("  [OK] schema_metadata (schema version tracking)")
    print("  [OK] agent_synchronizations (workflow transitions - used by record_sync.py)")
    print("  [OK] session_metadata (session configuration)")
    print("  [OK] workflow_records (immutable append-only state)")

    print(f"\n{Colors.BOLD}Created Indexes:{Colors.END}")
    print("  [OK] idx_sync_* (agent_synchronizations indexes)")
    print("  [OK] idx_records_* (workflow_records indexes)")

    print(f"\n{Colors.BOLD}Created Views:{Colors.END}")
    print("  [OK] state_transitions (temporal state change analysis)")
    print("  [OK] v_current_sync_status (current sync status)")

    print(f"\n{Colors.BOLD}Next Steps:{Colors.END}")
    print("  1. Record sync: python record_sync.py --sync-type workflow_transition --pattern phase_1_specify")
    print("  2. Query state: python query_workflow_state.py")
    print("  3. Analyze metrics: python analyze_metrics.py")

    print(f"\n{Colors.GREEN}[DONE] AgentDB ready for workflow state tracking!{Colors.END}\n")


def main() -> None:
    """Main entry point for AgentDB initialization."""
    parser = argparse.ArgumentParser(
        description="Initialize AgentDB schema for workflow state tracking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize with auto-generated session ID
  python init_database.py

  # Initialize with specific session ID
  python init_database.py --session-id abc123def456

  # Initialize with custom database path
  python init_database.py --db-path /path/to/agentdb.duckdb
""",
    )

    parser.add_argument("--session-id", type=str, help="AgentDB session ID (auto-generated if not provided)")
    parser.add_argument("--db-path", type=str, help="Path to DuckDB database (default: .claude-state/agentdb.duckdb)")

    args = parser.parse_args()

    print(f"\n{Colors.BOLD}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}AgentDB Initialization{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 70}{Colors.END}\n")

    # Get database path
    db_path = Path(args.db_path) if args.db_path else get_default_db_path()
    info(f"Database path: {db_path}")

    # Generate or use provided session ID
    session_id = args.session_id or generate_session_id()
    if not args.session_id:
        info(f"Generated session ID: {session_id}")
    else:
        info(f"Using provided session ID: {session_id}")

    # Load canonical state definitions
    workflow_states = load_workflow_states()

    # Create schema
    if not create_schema(session_id, workflow_states, db_path):
        error_exit("Schema creation failed")

    # Validate schema
    if not validate_schema(db_path):
        error_exit("Schema validation failed")

    # Print summary
    print_summary(session_id, workflow_states, db_path)


if __name__ == "__main__":
    main()
