#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Pre-release sanity check for downstream repos.

Runs a battery of local checks before tagging a release, capturing the
manual pre-release UX checklist pattern used by downstream consumers
(synavistra). Fail-fast: the first failing check exits non-zero and
the rest are skipped unless --continue-on-error is passed.

Usage:
    uv run python scripts/pre_release_sanity.py
    uv run python scripts/pre_release_sanity.py --skip lfs,pytest
    uv run python scripts/pre_release_sanity.py --continue-on-error

Checks (each can be skipped via --skip <name>):

    lfs         -- `git lfs fsck` passes AND no LFS pointer files
                   remain in the working tree (catches the synavistra
                   PR #706 failure mode)
    uncommitted -- `git status --porcelain` is empty
    ruff        -- `uv run ruff check .` passes
    format      -- `uv run ruff format --check .` passes
    pytest      -- `uv run pytest` passes (with --quiet)
    precommit   -- `uv run pre-commit run --all-files` passes
    claude_md   -- claude-md-hygiene auditor passes in strict mode
    changelog   -- CHANGELOG.md has an [Unreleased] section with
                   non-empty content (something to ship)

Exit codes:
    0: all checks passed (or skipped)
    1: one or more checks failed
    2: invocation error (bad arguments, missing tools)

See .claude/skills/claude-md-hygiene/SKILL.md for the audit rubric.
Traced to synavistra's "Pre-Release UX Checklist" in its root
CLAUDE.md.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""


def run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    """Run a command, return (returncode, combined output)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode, result.stdout + result.stderr
    except FileNotFoundError as e:
        return 127, f"Command not found: {e}"


def check_lfs() -> CheckResult:
    """Verify LFS objects are fetched and no pointer files remain."""
    if not shutil.which("git"):
        return CheckResult("lfs", False, "git not available")

    rc, out = run(["git", "lfs", "version"])
    if rc != 0:
        return CheckResult("lfs", True, "git-lfs not installed (skipped)")

    rc, out = run(["git", "lfs", "fsck"])
    if rc != 0:
        return CheckResult("lfs", False, f"git lfs fsck failed:\n{out}")

    # Verify no pointer file is smaller than expected: a pointer is
    # ~130 bytes. If git lfs ls-files returns paths whose working-tree
    # size matches the pointer size, LFS smudge hasn't run.
    rc, out = run(["git", "lfs", "ls-files"])
    if rc != 0:
        return CheckResult("lfs", False, f"git lfs ls-files failed:\n{out}")

    problems = []
    for line in out.splitlines():
        # Format: "<oid> * <path>" or "<oid> - <path>"
        parts = line.split(" ", 2)
        if len(parts) < 3:
            continue
        marker, path = parts[1], parts[2]
        if marker != "*":  # - means pointer-only on disk
            problems.append(path)
    if problems:
        return CheckResult(
            "lfs",
            False,
            "LFS pointer files on disk (run `git lfs pull`):\n  " + "\n  ".join(problems[:10]),
        )

    return CheckResult("lfs", True, "all LFS objects smudged")


def check_uncommitted() -> CheckResult:
    rc, out = run(["git", "status", "--porcelain"])
    if rc != 0:
        return CheckResult("uncommitted", False, out)
    if out.strip():
        return CheckResult(
            "uncommitted",
            False,
            "working tree has uncommitted changes:\n" + out,
        )
    return CheckResult("uncommitted", True, "working tree clean")


def check_ruff() -> CheckResult:
    rc, out = run(["uv", "run", "ruff", "check", "."])
    if rc != 0:
        return CheckResult("ruff", False, out.strip())
    return CheckResult("ruff", True, "ruff check clean")


def check_format() -> CheckResult:
    rc, out = run(["uv", "run", "ruff", "format", "--check", "."])
    if rc != 0:
        return CheckResult("format", False, out.strip())
    return CheckResult("format", True, "ruff format clean")


def check_pytest() -> CheckResult:
    rc, out = run(["uv", "run", "pytest", "--quiet"])
    if rc != 0:
        return CheckResult("pytest", False, out.strip()[-2000:])
    # Extract "N passed" summary line if present
    summary = ""
    for line in reversed(out.splitlines()):
        if "passed" in line or "failed" in line:
            summary = line.strip()
            break
    return CheckResult("pytest", True, summary or "pytest passed")


def check_precommit() -> CheckResult:
    rc, out = run(["uv", "run", "pre-commit", "run", "--all-files"])
    if rc != 0:
        return CheckResult("precommit", False, out.strip()[-2000:])
    return CheckResult("precommit", True, "all pre-commit hooks passed")


def check_claude_md() -> CheckResult:
    script = REPO_ROOT / ".claude" / "skills" / "claude-md-hygiene" / "scripts" / "audit_claude_md.py"
    if not script.exists():
        return CheckResult(
            "claude_md",
            True,
            "claude-md-hygiene skill not installed (skipped)",
        )
    rc, out = run(["uv", "run", "python", str(script), "--strict", "--quiet"])
    if rc != 0:
        return CheckResult("claude_md", False, out.strip())
    return CheckResult("claude_md", True, out.strip())


def check_changelog() -> CheckResult:
    """Verify CHANGELOG.md has a non-empty [Unreleased] section, UNLESS
    the last release was cut today (empty [Unreleased] is expected
    immediately after a release until the next work begins).

    The "last release cut today" heuristic: the most recent dated
    release header matches today's ISO date. Both
    `## [X.Y.Z] - YYYY-MM-DD` and `## [YYYY-MM-DD]` forms are
    accepted.
    """
    import datetime

    changelog = REPO_ROOT / "CHANGELOG.md"
    if not changelog.exists():
        return CheckResult("changelog", True, "no CHANGELOG.md (skipped)")
    content = changelog.read_text(encoding="utf-8")
    if "## [Unreleased]" not in content:
        return CheckResult(
            "changelog",
            False,
            "CHANGELOG.md has no [Unreleased] section",
        )

    # Count non-empty lines after [Unreleased] until the next ## header
    lines = content.splitlines()
    in_unreleased = False
    body_lines = 0
    for line in lines:
        if line.startswith("## [Unreleased]"):
            in_unreleased = True
            continue
        if in_unreleased and line.startswith("## "):
            break
        if in_unreleased and line.strip() and not line.startswith("###"):
            body_lines += 1

    if body_lines >= 2:
        return CheckResult("changelog", True, f"[Unreleased] has {body_lines} content lines")

    # [Unreleased] is empty -- acceptable only if the most recent release
    # was cut today. Grace period: immediately after cutting a release,
    # there's nothing to ship until the next work begins.
    today = datetime.date.today().isoformat()
    if f"- {today}" in content or f"[{today}]" in content:
        return CheckResult(
            "changelog",
            True,
            f"[Unreleased] empty but a release was cut today ({today}); grace period active",
        )

    return CheckResult(
        "changelog",
        False,
        "CHANGELOG.md [Unreleased] section is empty -- nothing to ship",
    )


CHECKS = {
    "lfs": check_lfs,
    "uncommitted": check_uncommitted,
    "ruff": check_ruff,
    "format": check_format,
    "pytest": check_pytest,
    "precommit": check_precommit,
    "claude_md": check_claude_md,
    "changelog": check_changelog,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--skip",
        default="",
        help="Comma-separated list of checks to skip (e.g. 'lfs,pytest')",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Run all checks even if one fails (default: fail fast)",
    )
    parser.add_argument(
        "--only",
        default="",
        help="Comma-separated allowlist: run only these checks",
    )
    args = parser.parse_args()

    skip = {s.strip() for s in args.skip.split(",") if s.strip()}
    only = {s.strip() for s in args.only.split(",") if s.strip()}

    invalid = (skip | only) - set(CHECKS)
    if invalid:
        print(f"Unknown check(s): {', '.join(invalid)}", file=sys.stderr)
        print(f"Available: {', '.join(CHECKS)}", file=sys.stderr)
        return 2

    results: list[CheckResult] = []
    any_failed = False

    for name, fn in CHECKS.items():
        if only and name not in only:
            continue
        if name in skip:
            print(f"  [SKIP] {name}")
            continue

        print(f"  [....] {name}", end="\r")
        result = fn()
        results.append(result)
        status = "[ OK ]" if result.passed else "[FAIL]"
        print(f"  {status} {result.name}: {result.detail.splitlines()[0] if result.detail else ''}")
        if not result.passed:
            any_failed = True
            if not args.continue_on_error:
                print(f"\n{result.detail}\n", file=sys.stderr)
                print("Aborting -- use --continue-on-error to run all checks.", file=sys.stderr)
                return 1

    print()
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"Pre-release sanity: {passed}/{total} checks passed.")

    if any_failed:
        print("\nFailures:")
        for r in results:
            if not r.passed:
                print(f"\n[{r.name}]\n{r.detail}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
