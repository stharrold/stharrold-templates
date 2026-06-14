#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""
Install user-level Claude Code skills from stharrold-templates into ~/.claude/skills/.

Skills are copied from user-skills/<bundle>/ to --target (default: ~/.claude/skills/).
Existing files are skipped by default; use --force to overwrite.

Usage:
    python scripts/install_user_skills.py <source_repo> [--bundle workflow] [--bundle research]
    python scripts/install_user_skills.py <source_repo> --bundle all
    python scripts/install_user_skills.py <source_repo> --bundle workflow --force
    python scripts/install_user_skills.py <source_repo> --dry-run

Bundles:
    workflow  -- release-pilot, branch-release.md, branch-start.md, pr-ship.md
    research  -- scholar-labs-search
    all       -- all of the above
"""

import argparse
import shutil
import sys
from pathlib import Path

BUNDLES = {
    "workflow": [
        "release-pilot",
        "branch-release.md",
        "branch-start.md",
        "pr-ship.md",
    ],
    "research": [
        "scholar-labs-search",
    ],
}


def _resolve_bundles(requested):
    if "all" in requested:
        return list(BUNDLES.keys())
    unknown = set(requested) - set(BUNDLES)
    if unknown:
        print(f"ERROR: unknown bundle(s): {', '.join(sorted(unknown))}", file=sys.stderr)
        print(f"Available: {', '.join(BUNDLES)}, all", file=sys.stderr)
        sys.exit(1)
    return list(requested)


def _copy_entry(src, dst, force, dry_run, *, label):
    """Copy a file or directory tree from src to dst, respecting skip-on-update."""
    if dst.exists() and not force:
        print(f"  skip   {label}  (exists; use --force to overwrite)")
        return
    action = "dry-run" if dry_run else ("overwrite" if dst.exists() else "install")
    print(f"  {action:<9} {label}")
    if dry_run:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source_repo", type=Path, help="path to the stharrold-templates repo")
    ap.add_argument("--bundle", action="append", default=[], metavar="NAME", help="bundle to install (workflow, research, all); repeatable")
    ap.add_argument("--target", type=Path, default=Path.home() / ".claude" / "skills", help="destination directory (default: ~/.claude/skills/)")
    ap.add_argument("--force", action="store_true", help="overwrite existing files")
    ap.add_argument("--dry-run", action="store_true", help="show what would happen without writing")
    args = ap.parse_args()

    if not args.bundle:
        ap.print_help()
        print("\nERROR: at least one --bundle is required.", file=sys.stderr)
        sys.exit(1)

    bundles = _resolve_bundles(args.bundle)
    user_skills_root = args.source_repo / "user-skills"

    if not user_skills_root.is_dir():
        print(f"ERROR: {user_skills_root} not found. Is source_repo correct?", file=sys.stderr)
        sys.exit(1)

    args.target.mkdir(parents=True, exist_ok=True)

    print(f"Installing user skills -> {args.target}")
    if args.force:
        print("  (--force: existing files will be overwritten)")
    if args.dry_run:
        print("  (--dry-run: no files will be written)")
    print()

    for bundle_name in bundles:
        bundle_dir = user_skills_root / bundle_name
        print(f"[{bundle_name}]")
        for entry_name in BUNDLES[bundle_name]:
            src = bundle_dir / entry_name
            dst = args.target / entry_name
            if not src.exists():
                print(f"  ERROR: source missing: {src}", file=sys.stderr)
                sys.exit(1)
            _copy_entry(src, dst, args.force, args.dry_run, label=entry_name)
        print()

    if args.dry_run:
        print("Dry run complete. Rerun without --dry-run to apply.")
    else:
        print("Done.")


if __name__ == "__main__":
    main()
