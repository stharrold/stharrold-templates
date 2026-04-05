# workflow-orchestrator (tactical notes)

Conceptual coordinator skill for the 4-step `sN` workflow
(`s1-worktree` → `s2-integrate` → `s3-release` → `s4-backmerge`). This
skill has **no executable scripts** -- it provides algorithmic guidance
for Claude Code to detect the current workflow context and load the
right sibling skills on demand. See [`SKILL.md`](SKILL.md) for the
canonical orchestration algorithm and phase-detection logic.

This file holds only gotchas that cost someone >30 minutes to
rediscover.

## Gotchas

### The skill has no scripts (and shouldn't)

- **There are zero `.py` files under `scripts/`** -- only an empty
  `__init__.py`. This is intentional. Orchestration is pure prompt
  engineering; executable logic lives in the skills this one calls
  into (`git-workflow-manager`, `workflow-utilities`,
  `tech-stack-adapter`).
- **`SKILL.md` is the authoritative algorithm.** Do not replicate
  the algorithm in this CLAUDE.md or in a README -- that creates
  drift. If you find yourself wanting to document the phase-
  detection logic here, update `SKILL.md` instead.

### Phase detection

- **Git branch + PR state are the primary signals.** `contrib/*` =
  between workflow cycles; `feature/*` = active implementation (s1
  done); open PR from `feature/*` to `contrib/*` = s2 in progress;
  `release/*` = s3 in progress; tag on `main` plus open backmerge PR
  = s4 in progress.
- **AgentDB is NOT required for phase detection** as of v8.9. The
  algorithm in `SKILL.md` references `query_workflow_state.py` as
  an **optional** enrichment for analytics -- not as a load-bearing
  dependency. If the `agentdb-state-manager` skill isn't installed,
  phase detection still works via git state alone.
- **Detached HEAD is treated as "between phases"**, not as an
  error. Claude Code sometimes lands in detached HEAD after a
  subagent invocation; the orchestrator should not try to recover,
  just report the state and ask the user.

### Skill loading order

- **`tech-stack-adapter` is always loaded first**, regardless of
  phase. It emits `TEST_CMD`, `BUILD_CMD`, `COVERAGE_CMD`, etc. by
  inspecting `pyproject.toml` / `package.json`. Every subsequent
  skill assumes these are available.
- **`git-workflow-manager` is loaded in all four sN steps.** It's
  the workhorse; every workflow phase calls one of its scripts.
- **`workflow-utilities` is loaded on demand**, typically when a
  script needs the VCS wrapper (`gh`/`az` auto-detect) or the TODO
  archiver.
- **No skill should be loaded unconditionally in every session.**
  Context tokens are precious; the orchestrator picks skills based
  on detected phase, not "just in case".

### Removed / archived skills

The earlier algorithm in this file referenced three skills that were
archived during the 2025-early-2026 migration:

- **`bmad-planner`** (archived): replaced by autonomous planning
  during s1. The orchestrator no longer `load_skill('bmad-planner')`
  in any branch of its algorithm.
- **`speckit-author`** (archived): replaced by autonomous
  implementation in the feature worktree. Claude Code writes specs
  directly when needed.
- **`quality-enforcer`** (archived): replaced by the
  `claude-code-review.yml` GitHub Actions workflow that runs on
  every PR (s2). Quality gates are enforced in CI, not by a skill.
- **`agentdb-state-manager`** (opt-in as of v8.9): moved to its own
  `agentdb` bundle. The orchestrator still references it but only
  as an optional analytics layer -- not as a required dependency.

If you see pseudocode in `SKILL.md` or any other doc that calls
`load_skill('bmad-planner')` or `load_skill('speckit-author')`,
that's stale drift -- file an issue or fix it in place.

### The `sN` rename (v8.9)

- **Slash commands are `sN`** (`s1-worktree` .. `s4-backmerge`),
  renamed from `v7x1_N` in v8.9. The algorithm's phase-map uses
  `sN` in all new code.
- **Internal AgentDB schema keys are still `phase_v7x1_*`** --
  deliberately, for backward compatibility with existing AgentDB
  databases. Do not rename them. See the `agentdb` bundle README
  for the full rationale.
- **"Workflow sN Architecture" is the new section heading** in
  `SKILL.md`, replacing the old "v7x1 Architecture" heading.

### Context budget discipline

- **Load skills lazily, not eagerly.** The original algorithm tried
  to preload every sibling skill "for efficiency"; in practice that
  burned 15-20K tokens on skills that never got called in a given
  session. The current algorithm loads each skill on first use.
- **Unload is not a real operation.** Once a skill's content is in
  Claude's context, you can't free it. Plan the load order so the
  most-likely-needed skill loads first.

## See also

- [`SKILL.md`](SKILL.md) -- canonical orchestration algorithm
- `tech-stack-adapter` -- first skill loaded in every session
- `git-workflow-manager` -- primary script consumer, loaded in all 4 sN steps
- `workflow-utilities` -- VCS wrapper + archive helpers
- `agentdb` bundle -- optional analytics layer (not required for orchestration)
