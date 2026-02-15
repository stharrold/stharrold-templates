#!/usr/bin/env python
# SPDX-FileCopyrightText: 2025 stharrold
# SPDX-License-Identifier: Apache-2.0
"""Build the SharePoint documentation from source markdown files.

Assembles docs/sharepoint/src/*.md into a single output file,
optionally rendering Mermaid diagrams to SVG/PNG/PDF via mmdc.

Usage:
    uv run python docs/sharepoint/build.py [--skip-diagrams] [--output PATH]
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR / "src"
DIAGRAMS_DIR = SCRIPT_DIR / "diagrams"

# TODO: Customize -- set to your project's output filename
OUTPUT_FILENAME = "Project_Documentation.md"
DEFAULT_OUTPUT = SCRIPT_DIR / OUTPUT_FILENAME

# TODO: Customize -- set to your project's main heading for TOC injection
MAIN_HEADING_PATTERN = None  # e.g. r"^(# \[Schema\]\.\[Project_\*_vN\])$"


def get_git_short_hash() -> str:
    """Return the current git short commit hash, or 'unknown'."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=SCRIPT_DIR,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def render_diagrams() -> list[str]:
    """Render all .mmd files to SVG, PNG, and PDF. Return list of rendered files."""
    mmd_files = sorted(DIAGRAMS_DIR.glob("*.mmd"))
    if not mmd_files:
        print("  No .mmd files found in diagrams/")
        return []

    # Resolve mmdc executable (handles .cmd on Windows)
    mmdc = shutil.which("mmdc")
    if mmdc is None:
        print("  WARNING: mmdc not found on PATH. Install with: npm install -g @mermaid-js/mermaid-cli")
        return []

    rendered = []
    for mmd in mmd_files:
        stem = mmd.stem
        formats = [
            (f"{stem}.svg", ["-t", "neutral", "--backgroundColor", "transparent"]),
            (f"{stem}.png", ["-t", "neutral", "--backgroundColor", "white", "-s", "4"]),
            (f"{stem}.pdf", ["-t", "neutral"]),
        ]
        for out_name, extra_args in formats:
            out_path = DIAGRAMS_DIR / out_name
            cmd = [mmdc, "-i", str(mmd), "-o", str(out_path)] + extra_args
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                rendered.append(out_name)
                print(f"  Rendered {out_name}")
            except FileNotFoundError:
                print(f"  WARNING: mmdc not found, skipping {out_name}. Install with: npm install -g @mermaid-js/mermaid-cli")
                break
            except subprocess.CalledProcessError as exc:
                print(f"  ERROR rendering {out_name}: {exc.stderr}")
    return rendered


def build_toc(content: str) -> str:
    """Generate a markdown table of contents from # and ## headings."""
    lines = []
    for match in re.finditer(r"^(#{1,2})\s+(.+)$", content, re.MULTILINE):
        level = len(match.group(1))
        title = match.group(2).strip()
        # Create anchor: lowercase, replace spaces with hyphens, strip non-alnum
        anchor = re.sub(r"[^\w\s-]", "", title.lower())
        anchor = re.sub(r"[\s]+", "-", anchor).strip("-")
        indent = "  " * (level - 1)
        lines.append(f"{indent}- [{title}](#{anchor})")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build SharePoint documentation.")
    parser.add_argument(
        "--skip-diagrams",
        action="store_true",
        help="Skip rendering Mermaid diagrams",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output file path (default: {DEFAULT_OUTPUT.name})",
    )
    args = parser.parse_args()

    # Step 1: Render diagrams
    if not args.skip_diagrams:
        print("Rendering diagrams...")
        rendered = render_diagrams()
    else:
        print("Skipping diagram rendering (--skip-diagrams)")
        rendered = []

    # Step 2: Collect and sort source files
    src_files = sorted(SRC_DIR.glob("*.md"))
    if not src_files:
        print("ERROR: No .md files found in src/", file=sys.stderr)
        sys.exit(1)
    print(f"Assembling {len(src_files)} source files...")

    # Step 3: Concatenate
    sections = []
    for src in src_files:
        sections.append(src.read_text(encoding="utf-8").rstrip())
    content = "\n\n".join(sections)

    # Step 4: Inject sync metadata
    now_utc = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    commit = get_git_short_hash()
    content = content.replace(
        "<!-- last_built_utc: PLACEHOLDER -->",
        f"<!-- last_built_utc: {now_utc} -->",
    )
    content = content.replace(
        "<!-- last_built_commit: PLACEHOLDER -->",
        f"<!-- last_built_commit: {commit} -->",
    )

    # Step 5: Resolve .mmd image refs to .svg
    content = re.sub(
        r"!\[([^\]]*)\]\(diagrams/([^)]+)\.mmd\)",
        r"![\1](diagrams/\2.svg)",
        content,
    )

    # Step 6: Generate and insert table of contents after the header
    if MAIN_HEADING_PATTERN:
        toc = build_toc(content)
        header_match = re.search(MAIN_HEADING_PATTERN, content, re.MULTILINE)
        if header_match:
            insert_pos = header_match.end()
            toc_block = f"\n\n## Table of contents\n\n{toc}\n"
            content = content[:insert_pos] + toc_block + content[insert_pos:]

    # Step 7: Write output
    content += "\n"  # Ensure trailing newline
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8")
    print(f"\nOutput written to: {args.output}")
    print(f"  Commit: {commit}")
    print(f"  Timestamp: {now_utc}")
    if rendered:
        print(f"  Diagrams rendered: {len(rendered)}")
    print("\nReminder: Upload SVG/PNG files from diagrams/ to SharePoint if images need to display inline.")


if __name__ == "__main__":
    main()
