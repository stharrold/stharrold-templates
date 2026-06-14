#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Apply named bundles of files from stharrold-templates to a target repo.

Thin CLI over the deterministic engine in release_lib.bundles (issue #240).

Usage:
    python scripts/apply_bundle.py <source-repo> <target-repo> --bundle <name> [--bundle <name>] [--force] [--dry-run]

Bundles: git, secrets, ci, pipeline, graphrag, sql-pipeline, data-catalog, full
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# release_lib is a top-level package; add the repo root so the script runs
# standalone (sys.path[0] = this scripts dir, which lacks release_lib).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from release_lib.bundles import (  # noqa: E402
    BUNDLE_DEFINITIONS,  # noqa: F401  re-exported for `from apply_bundle import BUNDLE_DEFINITIONS`
    VALID_BUNDLE_NAMES,
    apply_bundle,
    resolve_bundles,
    validate_source,
    validate_target,
)


def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Apply named bundles of files from stharrold-templates to a target repo.",
        epilog="Example: python scripts/apply_bundle.py . ../my-project --bundle git --bundle secrets",
    )
    parser.add_argument("source_repo", type=Path, help="Path to cloned stharrold-templates")
    parser.add_argument("target_repo", type=Path, help="Path to target repo (must be a git repo)")
    parser.add_argument(
        "--bundle",
        dest="bundles",
        action="append",
        required=True,
        choices=sorted(VALID_BUNDLE_NAMES),
        help="Bundle to apply (repeatable)",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite files that would normally be skipped (e.g. skip_on_update entries)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would change, make no modifications")

    args = parser.parse_args()

    source = args.source_repo.resolve()
    target = args.target_repo.resolve()

    # Validate
    ok, msg = validate_source(source)
    if not ok:
        print(f"ERROR: {msg}", file=sys.stderr)
        return 1

    ok, msg = validate_target(target)
    if not ok:
        print(f"ERROR: {msg}", file=sys.stderr)
        return 1

    # Resolve bundles (expand composites, deduplicate)
    try:
        resolved = resolve_bundles(args.bundles)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        print("=== DRY RUN ===\n")

    # Apply each bundle
    for name in resolved:
        apply_bundle(source, target, name, force=args.force, dry_run=args.dry_run)

    summary = ", ".join(resolved)
    print(f"Done. Bundles applied: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
