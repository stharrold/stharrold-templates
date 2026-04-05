# claude-md-hygiene

Audit and enforce the CLAUDE.md discipline rubric.

## Quick usage

```bash
# Report only
uv run python .claude/skills/claude-md-hygiene/scripts/audit_claude_md.py

# Fail CI if any file is >500 lines or matches the stub template
uv run python .claude/skills/claude-md-hygiene/scripts/audit_claude_md.py --strict
```

## What it checks

1. **Stub files** — frontmatter + `## Contents` with directory listing,
   no actual content. These are the anti-pattern removed in v8.9.
2. **Oversized files** — anything over 500 lines. Split into
   `docs/architecture.md` or per-subsystem scoped files instead.
3. **Dated section headers** — `(2026-04-02)` etc. in headings. Git
   blame is the canonical answer; inline dates rot.

## Why it exists

See [`SKILL.md`](SKILL.md) for the full background. Short version:
stharrold-templates used to ship a stub generator that polluted every
downstream repo with low-information CLAUDE.md files. This skill is
the replacement discipline.
