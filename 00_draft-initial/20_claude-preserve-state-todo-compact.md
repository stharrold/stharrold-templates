SESSION INITIALIZATION
When starting any session:
1. Check for existing TODO.md - if not present, create it with the structure below
2. Read TODO.md to understand current state and pending work
3. If CLAUDE.md doesn't exist or is outdated, run /init to update project context
4. Monitor context usage throughout the session

TODO.md STRUCTURE
Maintain TODO.md with this exact format for cross-session continuity:

---
# PROJECT STATE TRACKER
Last Updated: [ISO timestamp YYYY-MM-DDTHH:MM:SSZ]
Session ID: [unique-id]
Context Usage: [percentage]
Last Action: [description]

## CURRENT TASK
- Task ID: [identifier]
- Status: [IN_PROGRESS|BLOCKED|COMPLETED]
- Description: [detailed description]
- Dependencies: [list]
- Next Steps: [numbered list]

## COMPLETED TASKS
[List with timestamps and outcomes]

## PENDING TASKS
[Prioritized queue with estimates]

## DECISIONS LOG
[Key architectural/implementation decisions with rationale]

## BLOCKERS
[Issues requiring human intervention]

## SESSION NOTES
[Critical context for next session]

## NEXT SESSION START HERE
[Explicit instructions for resumption]
---

WORKFLOW RULES
1. State Persistence: After EVERY significant action, update TODO.md with current state
2. Context Monitoring: When context reaches 75%, prepare for compaction
3. At 80% Context: Execute /compact preserve: current task implementation, TODO.md state, critical decisions, unresolved blockers
4. Session Handoff: Before ending, write detailed "NEXT SESSION START HERE" section in TODO.md

AUTO-MAINTENANCE TRIGGERS
- Run /init when: 
  - First time in project
  - Major structural changes detected
  - CLAUDE.md is older than 7 days
  
- Run /compact when:
  - Context usage exceeds 80%
  - Before starting new major task
  - Switching between unrelated features

RESUMPTION PROTOCOL
When resuming from TODO.md:
1. Acknowledge previous session's state
2. Verify understanding of current task
3. Continue from exact stopping point
4. Update session metadata in TODO.md

CRITICAL BEHAVIORS
- Always update TODO.md before context compaction
- Never proceed without reading existing TODO.md
- Preserve decision rationale for future sessions
- Mark blockers clearly with resolution steps
- Use consistent task ID format: [TYPE]-[NUMBER]-[SHORT-DESC]
- Write TODO.md updates as if explaining to another developer
- Include error states and recovery instructions
- Document any assumptions made during implementation

EXAMPLE TODO.md ENTRY
---
# PROJECT STATE TRACKER
Last Updated: 2025-01-10T14:30:00Z
Session ID: sess-a1b2c3d4
Context Usage: 72%
Last Action: Implemented user authentication module

## CURRENT TASK
- Task ID: FEAT-001-auth-jwt
- Status: IN_PROGRESS
- Description: Implement JWT-based authentication with refresh tokens
- Dependencies: [bcrypt, jsonwebtoken, express-session]
- Next Steps:
  1. Complete refresh token rotation logic
  2. Add rate limiting to login endpoint
  3. Write integration tests for auth flow

## COMPLETED TASKS
- [2025-01-10T13:00:00Z] SETUP-001-project-init: Initialized Express server with TypeScript
- [2025-01-10T13:45:00Z] FEAT-002-user-model: Created User model with Mongoose

## PENDING TASKS
- HIGH: FEAT-003-password-reset: Password reset flow with email
- MED: TEST-001-auth-coverage: Achieve 80% test coverage for auth module
- LOW: DOC-001-api-swagger: Generate Swagger documentation

## DECISIONS LOG
- Chose JWT over sessions for stateless architecture compatibility
- Using Redis for refresh token storage (performance over PostgreSQL)
- Implemented argon2 instead of bcrypt (security recommendation)

## BLOCKERS
- Email service configuration needed (awaiting SMTP credentials)
- Rate limiting strategy unclear (needs product decision)

## SESSION NOTES
- Auth middleware is in /src/middleware/auth.ts
- Test credentials are in .env.test (gitignored)
- Remember to update API documentation after auth completion

## NEXT SESSION START HERE
Continue with refresh token rotation in /src/services/auth.service.ts line 145.
The validateRefreshToken function needs to check token family for detection of token reuse.
Reference the OWASP guidelines linked in comments.
---