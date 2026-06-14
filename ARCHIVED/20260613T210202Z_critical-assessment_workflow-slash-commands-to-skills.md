# Critical Assessment: From Per-Repo Workflow Scripts to Maintainable Agent-Led Infrastructure

- **Date (UTC):** 2026-06-13T21:02:02Z
- **Scope:** `.claude/commands/workflow/*`, `.claude/skills/*`, the `git`/`full`
  bundles, and the AgentDB/TODO state machinery.
- **Question answered:** Given that built-in slash commands (e.g.
  superpowers, `/code-review`, `/loop`, native worktrees) can now replace or
  augment these hand-built commands, and that Claude can pilot a multi-branch
  release autonomously, **what infrastructure is most maintainable and how
  should this repo change?**
- **Audience:** maintainer (single-author repo, `contrib/stharrold`).
- **Status:** assessment / proposal. Not yet a plan of record.

---

## 1. TL;DR

The repo encodes a *reproducible release process* as ~13,100 lines of Python
plus 5 slash commands plus a 538-line prose "orchestrator." Most of that code
exists to supply **judgment and orchestration** -- "what step is next," "is
context full," "what phase am I in" -- that the model and harness now supply
natively and for free. That layer is the least maintainable thing in the repo
and the highest-value thing to delete.

The recommendation is a three-tier split:

1. **One user-level skill** = a declarative release-pilot *playbook* (branch
   topology, naming, gate definitions, autonomy boundaries). Replaces the four
   `sN` slash commands + the orchestrator + most procedural prose.
2. **A small deterministic helper library** (~1-2k LOC, down from ~13k) =
   only the things that must *not* be left to model judgment: semver math, the
   `apply_bundle.py` file-ownership engine, and the `gh`/`az` VCS abstraction.
3. **In-repo CI/quality artifacts** (unchanged, must stay per-repo) =
   `claude-code-review.yml`, `tests.yml`, `.pre-commit-config.yaml`,
   `Containerfile`. These run where no user-level config exists.

Net effect: the product reframes from "a workflow *engine* you install" to "a
thin user-level pilot skill + a few installable CI artifacts + a tiny
deterministic lib." Delete candidates total roughly 8-10k LOC.

The one place to **resist** the user's framing: do not let "Claude is smart
enough" collapse into "Claude merges to `main` on a 10-minute timer with no
gate." Autonomy is right; a *fixed timer* and *ungated production merge* are
the wrong primitives. Section 6 specifies the replacement.

---

## 2. What exists today (grounded inventory)

| Component | Form | Size | What it really encodes |
|---|---|---|---|
| `commands/workflow/s1..s4`, `status` | Markdown wrappers | 5 files | Thin shells that shell out to Python scripts |
| `workflow-orchestrator` | SKILL.md prose | 6 LOC Python + 538-line SKILL.md | Pseudocode for phase detection, TODO parsing, 100K-token checkpointing |
| `git-workflow-manager` | Python | 3,251 LOC | Worktrees, branches, semver, release/backmerge, PR-feedback->issues |
| `workflow-utilities` | Python | 4,565 LOC | VCS abstraction, archive mgr, TODO manifest, dir-structure, hooks |
| `agentdb-state-manager` | Python | 3,741 LOC | DuckDB state cache, workflow analytics, checkpoints |
| `initialize-repository` | Python | 1,246 LOC | Bootstrap a new repo with the system |
| `tech-stack-adapter` | Python | 92 LOC | Detect `TEST_CMD`/`BUILD_CMD` from `pyproject.toml` |
| `claude-md-hygiene` | Python | 234 LOC | Lint CLAUDE.md discipline |
| Tests mirroring the above | Python | `tests/skills/*` | Carries maintenance weight 1:1 with the code |

**Total skill Python (excl. ARCHIVED): ~13,138 LOC.** Plus a mirroring test
suite. Plus bundle plumbing in `scripts/`.

Two observations that frame everything below:

- **The orchestrator is the canary.** It is 6 lines of real code and 538 lines
  of prose telling Claude how to behave -- `detect_context()`,
  `parse_todo_file()`, a `check_context_usage()` that hand-rolls a 100K-token
  checkpoint protocol. Its own `CLAUDE.md` already documents that `SKILL.md`
  carries **stale drift** (still references the archived `bmad-planner` and
  `speckit-author`). This is what imperative encoding of judgment looks like
  three releases later: prose that no longer matches reality, with a gotcha
  note apologizing for it.
- **Phase detection is already redundant.** The same `CLAUDE.md` states phase
  detection "works via git state alone" and that AgentDB is "NOT required."
  The repo has already half-admitted the state machine is dead weight.

---

## 3. The core problem: encoding judgment as code

These scripts were written when the model could not be trusted to (a) know the
branch topology, (b) decide the next step, (c) manage its own context, or (d)
recover from a half-finished release. So that knowledge was frozen into Python
and into 500-line prose algorithms.

That tradeoff has inverted. What the scripts encode now falls into three
buckets, and only one of them should remain code:

| Bucket | Example in this repo | Who should own it now |
|---|---|---|
| **Orchestration / judgment** | "next step?", phase detection, TODO state, 100K checkpoint, PR-feedback triage | The **model** (+ harness compaction). Delete the code. |
| **Policy / convention** | branch topology, `release/<ts>_<slug>` naming, gate definitions, autonomy limits | A **declarative skill** (markdown). One source of truth. |
| **Determinism / idempotence** | semver bump from last tag, `apply_bundle` file-ownership, `gh`/`az` dispatch | A **small library**. Keep, shrink, test hard. |

The maintainability principle: **encode policy declaratively, keep code only
where non-determinism would be a defect, and let the model orchestrate.** A
13k-LOC orchestration engine fails this on every axis -- it drifts (proven), it
duplicates the harness, and every model upgrade makes more of it dead code that
still has to be read, tested, and reasoned around.

---

## 4. Assessing the three claims

### 4.1 "Built-in slash commands can replace/augment these" -- mostly yes

Direct replacements that already exist:

| Hand-built today | Built-in replacement |
|---|---|
| `create_worktree.py` + `s1-worktree` | Native worktrees / `EnterWorktree`; superpowers `using-git-worktrees` |
| `workflow-orchestrator` "next step?" prose | superpowers `executing-plans` / `subagent-driven-development` |
| `generate_work_items_from_pr.py` + PR-feedback section | superpowers `receiving-code-review`; `/code-review` |
| `quality-enforcer` (already archived) | `claude-code-review.yml` in CI + `verification-before-completion` |
| Manual "wait then re-check" polling | `/loop` (interval or self-paced) |
| `s2-integrate` "finish the branch" prose | superpowers `finishing-a-development-branch` |

**Caveat (the critical part):** built-ins are an *external dependency you do
not own*. They evolve on someone else's schedule and are not guaranteed present
in headless/CI runs. So the policy (topology, gates, naming) must live in
**your** skill; built-ins are the *engine*, your skill is the *score*. Do not
delete your topology knowledge just because superpowers can drive a generic
branch finish -- it does not know your `contrib/stharrold -> develop ->
release/vN.N.N -> main` chain or your timestamped release-branch convention.

### 4.2 "These should be user-level, not per-repo" -- yes for the pilot, no for the gates

Splitting by *who enforces it* resolves this cleanly:

- **User-level (right):** the release-pilot skill. It is the same for every
  repo you own, it is human-driven, and it benefits from living in
  `~/.claude/skills/` so it is not copied into N repos and drifting N ways.
- **Per-repo (must stay):** anything CI enforces. `claude-code-review.yml`,
  `tests.yml`, and `.pre-commit-config.yaml` run on GitHub's runners where your
  user config does not exist. A user-level skill **cannot** gate a PR. The
  enforcement layer is intrinsically per-repo and is the part actually worth
  shipping as a bundle.

**What user-level costs you (be honest):** reproducibility for anyone who is
not on your exact Claude config -- a teammate, a fresh machine, a cron/headless
agent. Today's per-repo design means the process is *in the repo* and runs
identically for everyone. Moving the pilot to user-level trades that
team-portability for single-author maintainability. For a single-author repo
(`contrib/stharrold`) that is the correct trade; for the *bundles you ship to
other repos* it is not, which is why the gates stay in-repo.

### 4.3 "Claude can autonomously pilot the full release" -- yes, with the right primitives

The proposed flow is sound:

```
release/<YYYYMMDDTHHMMSSZ>_<slug>   (worktree)
  -> contrib/stharrold
  -> develop
  -> release/vN.N.N -> main (+ tag vN.N.N)
  release/vN.N.N -> develop          (backmerge)
  rebase contrib/stharrold onto develop
```

Claude can absolutely drive this end to end. But two of the user's stated
primitives are weak and should not be encoded as-is:

1. **"Wait a fixed time (say 10 min) for reviews"** is the wrong gate. Reviews
   do not arrive on a timer; CI does not finish on a timer. A fixed sleep is
   both too long (when checks pass in 90s) and too short (when a human is
   mid-review). **Replace with state polling + a timeout ceiling**, not a
   fixed wait. See 6.1.
2. **"Then merge"** -- into `main` -- is an irreversible, outward-facing
   action. The harness's own guidance is to confirm hard-to-reverse actions
   unless durably authorized. **Production merge + tag + push should be gated**
   behind either an explicit confirm or a clearly opted-in
   `--autonomous-prod` flag. Merges to `contrib`/`develop` can be fully
   autonomous; `main` should not be, by default.

So: autonomy yes, *fixed timer and ungated prod merge* no.

---

## 5. What infrastructure is most maintainable

**A declarative skill plus a thin deterministic library, with CI as the only
hard gate.** Concretely:

### Tier 1 -- One user-level skill: `release-pilot` (markdown, declarative)
Contains, as prose/tables (not pseudocode):
- the branch topology and the `release/<ts>_<slug>` naming rule;
- the gate definitions (what "reviews addressed" and "CI green" mean in terms
  of `gh pr checks` / review state);
- the autonomy boundary (auto through `develop`; gate `main`);
- the recovery rules (resume a half-done release from git state).

This replaces: the 4 `sN` commands, `workflow-orchestrator` entirely, and the
procedural narration inside `git-workflow-manager`. It is the single source of
truth for *policy*. ~1 file, a few hundred lines of markdown, no tests needed
(it is instructions, not code).

### Tier 2 -- A minimal deterministic library: `release-lib` (~1-2k LOC)
Keep only what must be deterministic and is genuinely algorithmic:
- **semver bump** from the last tag (do not let the model "compute" the next
  version by vibes -- this is the strongest argument for keeping *some* code);
- **`apply_bundle.py` file-ownership** engine (template-owned / user-merge /
  user-skip) -- idempotent file mutation is exactly where you want tested code,
  not judgment;
- **VCS abstraction** (`gh`/`az` auto-detect) -- real value that no built-in
  covers, and Azure DevOps parity is a differentiator worth keeping.

These keep their tests. Everything else loses its tests because it loses its
code.

### Tier 3 -- In-repo CI artifacts (unchanged)
`claude-code-review.yml`, `tests.yml`, `.pre-commit-config.yaml`,
`Containerfile`. The actual enforcement. Per-repo by necessity. This is the
part of the "bundle" product that still earns its keep.

### Why this is more maintainable than the status quo
- **Drift surface collapses.** One markdown playbook cannot drift from "another
  copy of the algorithm" because there is no other copy. The current
  SKILL.md-vs-reality drift becomes structurally impossible.
- **Model upgrades become free.** When the model gets better at orchestration,
  a declarative playbook gets *better* automatically; an imperative engine just
  accumulates more dead branches.
- **Tests track only determinism.** You test semver math and file-ownership --
  things with right answers -- not "did the orchestrator pick the right next
  step," which was always a brittle test of prose.

---

## 6. Concretely, how this repo should change

### 6.1 Specify the autonomous release as a polling state machine (in the skill, as prose)
Replace the fixed-timer idea with explicit gates the pilot polls:

| Gate | Signal | Action |
|---|---|---|
| Reviews | `gh pr view --json reviews,reviewDecision`; unresolved threads | Address review comments on the source branch; re-request; loop |
| CI | `gh pr checks <pr> --watch` (or poll) | Block on required checks; on failure, fix and push, re-poll |
| Timeout ceiling | max wait (e.g. 30 min) per gate, **not** a fixed sleep | On ceiling, stop and report -- never merge on timeout |
| Prod merge | merge to `main` + tag + push | **Gated**: explicit confirm or `--autonomous-prod` opt-in |

Use `/loop` (self-paced) as the polling driver; pick poll cadence by what is
being watched (CI ~60-270s, idle review waits longer). The 10-minute figure
becomes a *ceiling*, not a *sleep*.

### 6.2 Delete / archive (rough LOC freed)
- `agentdb-state-manager` (~3,741) -- redundant with git state + harness; the
  repo already made it opt-in and removed it from `full`. Finish the job.
- `workflow-orchestrator` SKILL.md prose (~538 lines) -- superseded by the
  Tier-1 playbook.
- TODO_*.md state machine + `context_checkpoints` + the 100K-token protocol in
  `workflow-utilities` -- the harness handles compaction now.
- PR-feedback->issues generator -- superseded by `receiving-code-review` +
  inline `/code-review` comments, unless you specifically want the issue
  paper-trail (keep only if so).
- The bulk of procedural narration in `git-workflow-manager` once the genuinely
  deterministic functions are extracted to `release-lib`.

Estimated reduction: **~8-10k LOC of code + its mirror tests.**

### 6.3 Keep and harden
- `release-lib`: semver, `apply_bundle` ownership, VCS abstraction (+ tests).
- `tech-stack-adapter` (92 LOC) -- tiny, deterministic, useful. Keep.
- `claude-md-hygiene` (234 LOC) -- independent utility, fine as-is.
- CI artifacts (Tier 3).

### 6.4 Reframe the bundle product
- The `pipeline` / `sql-pipeline` / `graphrag` / `data-catalog` bundles are
  *application code* unrelated to this critique -- leave them.
- The `git` / `full` *workflow* bundle shrinks to: the `release-pilot` skill
  (optionally installed user-level by `initialize-repository`) + `release-lib`
  + the CI artifacts. The 13k-LOC "workflow engine" stops being the headline.
- Slash commands: collapse `s1..s4` into one `/release` thin command backed by
  the skill, or drop the commands entirely and invoke the skill by name.

### 6.5 Update the docs that describe the old model
`WORKFLOW.md`, `BUNDLES.md`, and `CLAUDE.md` all describe the `sN` engine as the
product. They need to follow the reframe. (`CLAUDE.md`'s gotchas about
`release_workflow.py`, backmerge order, and `uv.lock` drift mostly survive --
those are deterministic-lib concerns and stay true.)

---

## 7. Risks, counterarguments, and what is lost

- **External-dependency risk.** Leaning on superpowers/`/code-review`/`/loop`
  means relying on tooling you do not version. Mitigation: keep *policy* in your
  own skill so a built-in changing behavior cannot silently change your release
  topology.
- **Loss of team/headless reproducibility.** User-level pilot does not run for a
  teammate or a cron agent without your config. Mitigation: the *gates* stay in
  CI (which is reproducible for everyone); only the *human-driven convenience
  layer* goes user-level. Acceptable for a single-author repo; revisit if the
  repo gains contributors.
- **Loss of deterministic audit trail.** AgentDB analytics and TODO state gave a
  queryable history. In practice git history + PR/Action logs already provide
  this; the DuckDB layer was a second, drifting copy. Low real loss.
- **Over-trusting autonomy on `main`.** The single most important guardrail:
  production merge stays gated by default. Everything below `main` can be
  autonomous.
- **Determinism regressions.** If semver/file-ownership are *not* kept as tested
  code and are instead handed to the model, expect occasional wrong version
  bumps and clobbered user files. This is the bucket that must stay code.

---

## 8. Recommended next step

Do **not** big-bang rewrite. Sequence it so each step is independently
reversible:

1. Author the `release-pilot` skill (Tier 1) and run one real release through it
   *manually-but-skill-guided*, with the `main` merge gated. Prove the playbook
   before deleting anything.
2. Extract `release-lib` (Tier 2) from `git-workflow-manager` /
   `workflow-utilities`; keep its tests green.
3. Once a release has gone through cleanly on the new path, archive
   `agentdb-state-manager`, the orchestrator prose, and the TODO/checkpoint
   machinery (Tier-2-leftovers + Tier-1-superseded).
4. Reframe `BUNDLES.md` / `WORKFLOW.md` / `README.md` around the three tiers.

Brainstorm and pressure-test step 1's autonomy contract (poll cadences,
timeout ceilings, the exact `main` gate) before writing it -- that contract is
the part most likely to be wrong on the first try.
