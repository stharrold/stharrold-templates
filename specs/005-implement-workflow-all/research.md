# Research: /workflow/all Command

## Executive Summary

The `/workflow/all` command will orchestrate running multiple workflow steps in sequence, with automatic detection of current state and pausing at manual gates (PR merges).

## Existing Workflow Architecture

### Current Commands (7 total)
| Command | Purpose | Manual Gates After |
|---------|---------|-------------------|
| `/1_specify` | Create feature branch + spec | None |
| `/2_plan` | Generate research, data-model, contracts | None |
| `/3_tasks` | Generate task list | None |
| `/4_implement` | Execute tasks | None |
| `/5_integrate` | PR feature→contrib→develop | PR merges (2) |
| `/6_release` | PR develop→release→main | PR merge (1) |
| `/7_backmerge` | PR release→develop, rebase contrib | PR merge (1) |

### Workflow Phases
1. **Feature Development** (0→1→2→3): Fully automatable
2. **Integration** (4): Creates PRs, pauses for manual merges
3. **Release** (5→6): Creates PRs, pauses for manual merges

### Branch Detection Logic
| Branch Pattern | Detected State | Suggested Flow |
|---------------|----------------|----------------|
| `NNN-*` (feature) | Feature in progress | Continue 1→4 |
| `contrib/*` | Integration phase | Run 4 or 5 |
| `develop` | Ready for release | Run 5→6 |
| `release/*` | Release in progress | Run 6 |
| `main` | Production | Start new feature (0) |

## Design Decisions

### Decision 1: Command Modes
**Chosen**: Four modes with state detection
- `new "description"` - Start from /1_specify
- `release` - Run /6_release → /7_backmerge
- `continue` - Resume after manual gate (PR merge)
- Default (no args) - Detect state and continue

**Rationale**: Covers all use cases while keeping interface simple

**Alternatives Rejected**:
- Single mode with interactive prompts - too slow
- Step range syntax (`/all 1-4`) - confusing

### Decision 2: State Detection
**Chosen**: Branch name + artifact existence
- Check branch pattern (feature/contrib/develop/release)
- Check for existing artifacts (spec.md, tasks.md, etc.)
- Determine next logical step

**Rationale**: Non-invasive, no additional state files needed

**Alternatives Rejected**:
- Persist state in file - adds complexity, can desync
- Database tracking - overkill for this use case

### Decision 3: Manual Gate Handling
**Chosen**: Stop execution, report status, show resume command
```
✓ Step 4: /5_integrate complete
⏸ PAUSED: Manual gate - PR merge required

PR URLs:
- feature→contrib: https://github.com/...
- contrib→develop: https://github.com/...

After merging, run: /workflow/all continue
```

**Rationale**: Clear UX, user knows exactly what to do next

### Decision 4: Error Handling
**Chosen**: Stop on first error, report step and error, suggest retry
```
✗ Step 3: /4_implement failed
Error: Test failure in test_auth.py

To retry from this step: /workflow/all --from 3
To skip and continue: /workflow/all --skip 3
```

**Rationale**: Fail-fast prevents cascading issues

## Implementation Approach

### Slash Command Structure
Create `.gemini/commands/workflow/all.md` with:
- Frontmatter (no prev/next since it orchestrates)
- State detection logic
- Mode handling (new/release/continue)
- Step execution loop
- Manual gate detection and pause

### No Python Script Needed
Unlike `/5_integrate`, `/6_release`, `/7_backmerge` which run external Python scripts, `/workflow/all` is purely orchestration - it invokes the other slash commands in sequence. The logic lives entirely in the markdown command file.

### Slash Command Invocation
Use `SlashCommand` tool to invoke each step:
```
/workflow:0_specify "description"
/workflow:1_plan
/workflow:2_tasks
/workflow:3_implement
/workflow:4_integrate
/workflow:5_release
/workflow:6_backmerge
```

## Dependencies

- All 7 existing workflow commands must work independently
- Branch detection via `git branch --show-current`
- Artifact detection via file existence checks
- PR status detection via `gh pr list`

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Command execution fails silently | Check exit status after each step |
| State detection incorrect | Add `--from N` override flag |
| PR merge not detected | Use `gh pr view --json state` |
| User runs from wrong branch | Clear error message with suggestion |
