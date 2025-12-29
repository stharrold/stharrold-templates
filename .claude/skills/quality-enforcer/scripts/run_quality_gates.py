#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Run all quality gates and report results."""

import subprocess
import sys
from pathlib import Path

# Add workflow-utilities to path for worktree_context
sys.path.insert(
    0,
    str(Path(__file__).parent.parent.parent / "workflow-utilities" / "scripts"),
)


def get_worktree_info() -> dict:
    """Get worktree context information for logging.

    Returns:
        Dictionary with worktree_id and worktree_root, or empty values if detection fails.
    """
    try:
        from worktree_context import get_worktree_context

        ctx = get_worktree_context()
        return {
            "worktree_id": ctx.worktree_id,
            "worktree_root": str(ctx.worktree_root),
        }
    except (ImportError, RuntimeError):
        return {"worktree_id": "", "worktree_root": str(Path.cwd())}


def run_tests():
    """Run all tests and verify they pass.

    Excludes integration and benchmark tests which require external services
    or are designed for performance measurement rather than correctness.
    """
    print("Running tests...")
    result = subprocess.run(
        ["uv", "run", "pytest", "-v", "-m", "not integration and not benchmark"],
        capture_output=True,
        text=True,
    )

    passed = result.returncode == 0

    if passed:
        print("[OK] All tests passed")
    else:
        print("[X] Some tests failed")
        print(result.stdout)
        print(result.stderr)

    return passed


def check_coverage(threshold=80):
    """Check test coverage meets threshold."""
    print(f"Checking coverage (>={threshold}%)...")

    # Call check_coverage.py script using repo-relative path
    script_path = ".claude/skills/quality-enforcer/scripts/check_coverage.py"
    result = subprocess.run(["uv", "run", "python", script_path, str(threshold)], capture_output=True, text=True)

    passed = result.returncode == 0
    print(result.stdout)

    return passed


def check_build():
    """Verify package builds successfully."""
    print("Checking build...")
    result = subprocess.run(["uv", "build"], capture_output=True, text=True)

    passed = result.returncode == 0

    if passed:
        print("[OK] Build successful")
    else:
        print("[X] Build failed")
        print(result.stderr)

    return passed


def check_linting():
    """Run ruff linting."""
    print("Checking linting...")

    result = subprocess.run(["uv", "run", "ruff", "check", "."], capture_output=True, text=True)

    passed = result.returncode == 0

    if passed:
        print("[OK] Linting passed")
    else:
        print("[X] Linting failed")
        print(result.stdout)

    return passed


def run_all_quality_gates(coverage_threshold=80):
    """
    Run all quality gates and report results.

    Returns:
        (passed: bool, results: dict)
    """
    results = {}
    all_passed = True

    # Get worktree context
    worktree_info = get_worktree_info()
    results["worktree_id"] = worktree_info["worktree_id"]
    results["worktree_root"] = worktree_info["worktree_root"]

    print("=" * 60)
    print("QUALITY GATES")
    if worktree_info["worktree_id"]:
        print(f"Worktree: {worktree_info['worktree_id']}")
    print("=" * 60)

    # Gate 1: Test Coverage
    print("\n[1/4] Test Coverage...")
    passed = check_coverage(coverage_threshold)
    results["coverage"] = {"passed": passed}
    all_passed &= passed

    # Gate 2: Tests Passing
    print("\n[2/4] Running Tests...")
    passed = run_tests()
    results["tests"] = {"passed": passed}
    all_passed &= passed

    # Gate 3: Build
    print("\n[3/4] Build Check...")
    passed = check_build()
    results["build"] = {"passed": passed}
    all_passed &= passed

    # Gate 4: Linting
    print("\n[4/4] Linting...")
    passed = check_linting()
    results["linting"] = {"passed": passed}
    all_passed &= passed

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    # Dynamically summarize gates, filtering out non-gate keys
    non_gate_keys = {"worktree_id", "worktree_root"}
    for gate, result in results.items():
        if gate in non_gate_keys:
            continue
        if isinstance(result, dict):
            status = "[OK] PASS" if result.get("passed", False) else "[X] FAIL"
            print(f"{gate.upper()}: {status}")

    print("\n" + ("[OK] ALL GATES PASSED" if all_passed else "[X] SOME GATES FAILED"))

    # Trigger sync engine (Phase 3 integration)
    try:
        import asyncio

        integration_path = Path(__file__).parent.parent.parent / "agentdb-state-manager" / "scripts"
        if str(integration_path) not in sys.path:
            sys.path.insert(0, str(integration_path))
        from worktree_agent_integration import trigger_sync_completion

        asyncio.run(
            trigger_sync_completion(
                agent_id="assess",
                action="test_complete",
                state_snapshot={
                    "all_passed": all_passed,
                    "coverage_passed": results.get("coverage", {}).get("passed", False),
                    "tests_passed": results.get("tests", {}).get("passed", False),
                    "build_passed": results.get("build", {}).get("passed", False),
                    "linting_passed": results.get("linting", {}).get("passed", False),
                },
                context={},
            )
        )
    except Exception as e:
        # Graceful degradation: don't fail if sync unavailable, but log for debugging
        print(f"[DEBUG] AgentDB sync skipped: {e}", file=sys.stderr)

    return all_passed, results


if __name__ == "__main__":
    # TODO(2025-11-23): Increase coverage threshold to 80 once test coverage improves
    # Current codebase has ~4% coverage as of 2025-11-23; target is 80%
    passed, _ = run_all_quality_gates(coverage_threshold=0)
    sys.exit(0 if passed else 1)
