# claude-md-hygiene (tactical notes)

Skill auditor for CLAUDE.md discipline. See [`SKILL.md`](SKILL.md) for
the canonical skill definition and rubric.

## Gotchas

- **Running `--strict` on a fresh template checkout will FAIL** until
  the 3 oversized skill CLAUDE.md files are trimmed (initialize-repository,
  git-workflow-manager, workflow-utilities). This is intentional — the
  auditor is a forcing function, not a noop validator.
- **The `[DATED]` category is a warning, not a failure** even in
  `--strict` mode. Dated headers are occasionally useful for pinning
  release announcements or migration notes. If a dated header is stale,
  it will usually be caught by the [OVERSIZED] rule first (stale content
  tends to accumulate).
- **Exclusions**: the scanner skips `.git`, `.tmp`, `.venv`, `venv`,
  `__pycache__`, `node_modules`, `ARCHIVED/`, `archived/`, `_site/`.
  Anything in `ARCHIVED/` is intentional historical record — do not
  trim it when the auditor grows.
- **Stub detection uses two heuristics**: (a) file has `type: claude-context`
  frontmatter, OR (b) file has ≥2 of the stub header markers (`## Contents`,
  `## Related`, `## Related Documentation`, `**Child Directories:**`).
  Both heuristics are required because hand-written skill CLAUDE.md
  files legitimately have "Related" sections — the combined signal
  catches only the auto-generated template pattern.
- **`check_ascii_only` pre-commit hook**: the scripts in this skill
  must stay ASCII-only. No em-dashes in docstrings.

## See also

- [`SKILL.md`](SKILL.md)
- `workflow-utilities` — deleted the `generate_claude_md.py` /
  `check_claude_md_frontmatter.py` scripts that this skill replaces
- Root `CLAUDE.md` "What goes here" rubric — the editorial policy
