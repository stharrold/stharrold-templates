# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Tests for scripts/apply_bundle.py and release_lib.bundles."""

import subprocess
import sys
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT))
from apply_bundle import BUNDLE_DEFINITIONS, resolve_bundles

from release_lib.bundles import _insert_deps_into_array, copy_tree, merge_gitignore, merge_pyproject_deps


def test_apply_bundle_help_exits_zero():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "apply_bundle.py"), "--help"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    assert "bundle" in result.stdout.lower()


def test_bundle_definitions_have_required_keys():
    """Every bundle has at least: skills, commands, copy_files, merge_pyproject_deps.
    The 'full' bundle also has 'includes'."""
    required_keys = {"skills", "commands", "copy_files", "merge_pyproject_deps"}
    for name, defn in BUNDLE_DEFINITIONS.items():
        for key in required_keys:
            assert key in defn, f"Bundle {name!r} missing required key {key!r}"
            assert isinstance(defn[key], list), f"Bundle {name!r} key {key!r} should be a list"
    # full bundle must have includes
    assert "includes" in BUNDLE_DEFINITIONS["full"]
    assert isinstance(BUNDLE_DEFINITIONS["full"]["includes"], list)


def test_full_bundle_includes_all_others():
    """The 'full' bundle's 'includes' list contains git, secrets, ci, graphrag,
    sql-pipeline, and data-catalog."""
    assert BUNDLE_DEFINITIONS["full"]["includes"] == [
        "git",
        "secrets",
        "ci",
        "graphrag",
        "sql-pipeline",
        "data-catalog",
    ]


def test_all_referenced_paths_exist():
    """Every path referenced in bundle definitions actually exists in the source repo."""
    for name, defn in BUNDLE_DEFINITIONS.items():
        # Skills -> .claude/skills/{skill}/
        for skill in defn.get("skills", []):
            skill_dir = REPO_ROOT / ".claude" / "skills" / skill
            assert skill_dir.exists(), f"Bundle {name!r}: skill dir {skill_dir} does not exist"

        # Commands
        for cmd in defn.get("commands", []):
            cmd_path = REPO_ROOT / cmd
            assert cmd_path.exists(), f"Bundle {name!r}: command path {cmd_path} does not exist"

        # Copy files
        for f in defn.get("copy_files", []):
            file_path = REPO_ROOT / f
            assert file_path.exists(), f"Bundle {name!r}: copy_file {file_path} does not exist"

        # Skip on update (entry is either a str path or a (src, dst) tuple)
        for f in defn.get("skip_on_update", []):
            src_rel = f[0] if isinstance(f, tuple) else f
            file_path = REPO_ROOT / src_rel
            assert file_path.exists(), f"Bundle {name!r}: skip_on_update {file_path} does not exist"

        # Copy dirs
        for d in defn.get("copy_dirs", []):
            dir_path = REPO_ROOT / d
            assert dir_path.exists(), f"Bundle {name!r}: copy_dir {dir_path} does not exist"


def test_no_overlapping_skills_between_non_full_bundles():
    """The 'secrets' and 'ci' bundles have empty skills lists.
    No skill appears in more than one non-'full' bundle."""
    non_full = {k: v for k, v in BUNDLE_DEFINITIONS.items() if k != "full"}
    assert BUNDLE_DEFINITIONS["secrets"]["skills"] == []
    assert BUNDLE_DEFINITIONS["ci"]["skills"] == []

    seen_skills: dict[str, str] = {}
    for name, defn in non_full.items():
        for skill in defn.get("skills", []):
            assert skill not in seen_skills, f"Skill {skill!r} appears in both {seen_skills[skill]!r} and {name!r}"
            seen_skills[skill] = name


def test_dry_run_makes_no_changes(tmp_path):
    """Create a tmp git repo, run apply_bundle.py with --dry-run --bundle git,
    verify the target is unchanged (no .claude/ dir created)."""
    # Initialize a bare git repo in tmp_path
    subprocess.run(["git", "init", str(tmp_path)], capture_output=True, check=True)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/apply_bundle.py",
            str(REPO_ROOT),
            str(tmp_path),
            "--bundle",
            "git",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"apply_bundle.py failed: {result.stderr}"
    assert not (tmp_path / ".claude").exists(), ".claude/ dir should not be created in dry-run mode"


def test_resolve_bundles_expands_full():
    """resolve_bundles(['full']) returns all included bundles then 'full'."""
    resolved = resolve_bundles(["full"])
    assert resolved == [
        "git",
        "secrets",
        "ci",
        "pipeline",
        "graphrag",
        "sql-pipeline",
        "data-catalog",
        "full",
    ]


def test_resolve_bundles_deduplicates():
    """resolve_bundles(['git', 'full']) should contain 'git' only once."""
    resolved = resolve_bundles(["git", "full"])
    assert resolved.count("git") == 1
    assert set(resolved) == {
        "git",
        "secrets",
        "ci",
        "pipeline",
        "graphrag",
        "sql-pipeline",
        "data-catalog",
        "full",
    }


# ---------------------------------------------------------------------------
# Robustness fixes (issue #245)
# ---------------------------------------------------------------------------


def test_copy_tree_handles_file_at_dst(tmp_path):
    """copy_tree succeeds when the destination path already exists as a file."""
    src_root = tmp_path / "src"
    (src_root / "rel_dir").mkdir(parents=True)
    (src_root / "rel_dir" / "a.txt").write_text("hello", encoding="utf-8")

    dst_root = tmp_path / "dst"
    dst_root.mkdir()
    # Plant a regular file where copy_tree expects to create a directory.
    (dst_root / "rel_dir").write_text("not-a-dir", encoding="utf-8")

    copy_tree(src_root, dst_root, "rel_dir", dry_run=False)

    assert (dst_root / "rel_dir").is_dir()
    assert (dst_root / "rel_dir" / "a.txt").read_text(encoding="utf-8") == "hello"


def test_insert_deps_inline_array_returns_false_and_leaves_lines_unchanged():
    """_insert_deps_into_array returns False when dev is an inline array and
    must not modify lines -- preventing cross-section dep bleed."""
    content = textwrap.dedent("""\
        [dependency-groups]
        dev = ["ruff>=0.14.1"]

        [project]
        dependencies = [
            "requests",
        ]
    """)
    lines = content.splitlines(keepends=True)
    original = list(lines)

    result = _insert_deps_into_array(lines, "[dependency-groups]", "dev", ["pytest>=8.0.0"])

    assert result is False
    assert lines == original  # lines must be untouched


def test_merge_pyproject_inline_array_warns_and_skips(tmp_path, capsys):
    """merge_pyproject_deps warns and returns 0 when dev array is inline,
    leaving pyproject.toml byte-identical to the original."""
    original = '[dependency-groups]\ndev = ["ruff>=0.14.1"]\n'
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(original, encoding="utf-8")

    ret = merge_pyproject_deps(tmp_path, ["pytest>=8.0.0"], dry_run=False)

    assert ret == 0
    assert "WARN" in capsys.readouterr().out
    assert pyproject.read_text(encoding="utf-8") == original


def test_merge_gitignore_utf8(tmp_path):
    """merge_gitignore reads and writes .gitignore files with UTF-8 encoding."""
    src = tmp_path / "src"
    src.mkdir()
    (src / ".gitignore").write_text("*.log\n.env\n", encoding="utf-8")

    dst = tmp_path / "dst"
    dst.mkdir()
    (dst / ".gitignore").write_text("*.pyc\n", encoding="utf-8")

    merge_gitignore(dst, src, dry_run=False)

    result = (dst / ".gitignore").read_text(encoding="utf-8")
    assert "*.log" in result
    assert ".env" in result
    assert "*.pyc" in result
