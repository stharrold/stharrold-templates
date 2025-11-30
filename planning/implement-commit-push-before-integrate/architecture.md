# Architecture: implement-commit-push-before-integrate

## Approach

Modify the `/4_implement` slash command template to add a final section that:
1. Runs `git add .` to stage all changes
2. Runs `git commit` with a summary message
3. Runs `git push` to push to remote
4. Displays a clear prompt with instructions for next steps

## Components

| Component | Changes |
|-----------|---------|
| `.claude/commands/workflow/4_implement.md` | Add final section for commit/push and user prompt |

## Technical Decisions

1. **Use `git add .`** - Stage all files consistently with workflow patterns
2. **Commit message** - Should summarize implementation work done
3. **Push** - Use current branch tracking
4. **Prompt** - Show exact `cd` command and next slash command

## Integration Points

- Integrates with existing `/4_implement` slash command
- Works with existing `/5_integrate` step which validates context

## Risks

None significant - this is a simple addition to existing workflow

## Testing Approach

Manual testing of workflow steps 4 and 5
