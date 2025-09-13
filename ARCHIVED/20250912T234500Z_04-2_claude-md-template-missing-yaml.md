# Project Configuration for Claude Code

## Project Overview

**Project Name:** [PROJECT_NAME]
**Purpose:** [BRIEF_DESCRIPTION]
**Stage:** [prototype|development|production]
**Critical Systems:** [authentication|payments|user_data|none]

## Technology Stack

<technology>
- **Language:** [e.g., TypeScript 5.x, Python 3.11+]
- **Framework:** [e.g., Next.js 14, Spring Boot 3.x]
- **Database:** [e.g., PostgreSQL 15, MongoDB 6]
- **Infrastructure:** [e.g., AWS, Docker, Kubernetes]
- **Testing:** [e.g., Jest, pytest, React Testing Library]
- **CI/CD:** [e.g., GitHub Actions, Jenkins]
</technology>

## Project Structure

```
src/
├── components/     # React components
├── pages/          # Next.js pages or route handlers
├── services/       # Business logic and API calls
├── utils/          # Shared utilities
├── types/          # TypeScript definitions
└── tests/          # Test files
```

## Code Style and Conventions

<standards>
- **Style Guide:** [ESLint config extends 'next/core-web-vitals']
- **Formatting:** Prettier with 2-space indentation
- **Naming:** camelCase for variables, PascalCase for components
- **Components:** Functional components with hooks only
- **State Management:** [Context API|Redux Toolkit|Zustand]
- **Error Handling:** All async operations wrapped in try-catch
- **Comments:** JSDoc for public APIs, inline for complex logic
</standards>

### Import Order

1. External dependencies
2. Internal aliases (@components, @utils)
3. Relative imports
4. Types/interfaces

## Development Workflow

<workflow>
### Task Execution Pattern (EPCC)
1. **EXPLORE** - Thoroughly understand requirements, examine existing code, identify constraints
2. **PLAN** - Design approach, outline changes, identify affected files and dependencies
3. **CODE** - Implement solution following conventions, include tests
4. **COMMIT** - Review changes, write descriptive commit message, push to branch

### When to Use Plan Mode

- Activate with Shift+Tab x2 for:
  - Architectural decisions
  - Multi-file refactoring
  - Security-sensitive changes
  - Complex algorithm design
- Restricts to read-only operations during analysis

### Git Workflow

- Branch naming: `feature/`, `fix/`, `chore/` prefixes
- Commit format: `type(scope): description` (conventional commits)
- Always create feature branches from main
- Squash commits before merging
  </workflow>

## Testing Requirements

<testing>
- **Coverage Target:** 80% for business logic, 60% for UI
- **Test Types:** Unit, Integration, E2E (when specified)
- **Test Location:** Colocated with source in `__tests__` folders
- **Mocking:** Mock external services, not internal modules
- **Assertions:** Use descriptive matchers and error messages
</testing>

### Test Patterns

```javascript
// GOOD: Descriptive, isolated, follows AAA pattern
describe("ComponentName", () => {
  it("should handle user interaction correctly", () => {
    // Arrange
    // Act
    // Assert
  });
});
```

## Security Protocols

<security level="HIGH">
### ALWAYS
- Validate and sanitize all user inputs
- Use parameterized queries for database operations
- Implement proper authentication checks
- Hash passwords with bcrypt (min 10 rounds)
- Use HTTPS for all external communications
- Implement rate limiting on APIs
- Log security events

### NEVER

- Store secrets in code (use environment variables)
- Trust client-side validation alone
- Use eval() or dynamic code execution
- Expose internal errors to users
- Commit .env files or credentials
  </security>

## Performance Guidelines

<performance>
- Lazy load components and routes
- Implement pagination for lists >50 items
- Use React.memo for expensive components
- Optimize images (WebP, lazy loading, responsive)
- Implement proper caching strategies
- Monitor bundle size (<200KB for initial load)
</performance>

## Error Handling

<error_handling>

### API Errors

- Return consistent error format (RFC 7807)
- Include correlation IDs for tracking
- Log errors with context
- Provide user-friendly messages

### Client Errors

- Use error boundaries for React components
- Implement fallback UI for failures
- Report critical errors to monitoring service
- Maintain error state in global store
  </error_handling>

## Critical DO NOT Rules

<do_not priority="CRITICAL">

1. **DO NOT** modify authentication logic without explicit approval
2. **DO NOT** bypass security validations for convenience
3. **DO NOT** delete existing tests when updating code
4. **DO NOT** use any or unknown TypeScript types
5. **DO NOT** access database directly from components
6. **DO NOT** commit console.log statements
7. **DO NOT** ignore linting errors
8. **DO NOT** use inline styles except for dynamic values
9. **DO NOT** create files larger than 300 lines
10. **DO NOT** nest ternary operators
    </do_not>

## Custom Commands

<commands>
- `/project:test` - Run full test suite with coverage
- `/project:lint` - Run ESLint and Prettier checks
- `/project:review` - Perform security and performance analysis
- `/project:deploy` - Execute deployment pipeline
- `/project:analyze [file]` - Deep analysis of specific file
</commands>

## Context Management

<context_rules>

- Use `/clear` between unrelated features
- Use `/compact` after completing test files
- Maintain conversation under 10 messages
- Request Plan Mode (Shift+Tab x2) for architectural changes
- Include screenshots for UI work
  </context_rules>

## Model Selection Strategy

<model_strategy>

- **Claude Sonnet 4**: Default for all development tasks
- **Claude Opus 4**: Reserve for complex architecture, multi-file refactoring
- **Claude Haiku**: Use for repetitive tasks, simple CRUD operations
- Switch models based on task complexity, not preference
  </model_strategy>

## File References

### Extended Documentation

- Architecture: `./docs/architecture.md`
- API Specifications: `./docs/api/openapi.yaml`
- Database Schema: `./docs/database/schema.sql`
- Deployment Guide: `./docs/deployment.md`

### Configuration Files

- ESLint: `./.eslintrc.json`
- TypeScript: `./tsconfig.json`
- Environment: `./.env.example`

## Team Preferences

<preferences>
- Prefer composition over inheritance
- Use early returns to reduce nesting
- Implement feature flags for gradual rollouts
- Write self-documenting code over extensive comments
- Optimize for readability over cleverness
- Design APIs with backwards compatibility
</preferences>

## Session Initialization

When starting a new session:

1. Identify the task type and complexity
2. Review relevant sections of this document
3. Check for recent changes in git history
4. Verify test suite passes before modifications
5. Note any usage limit considerations

## Quick Reference

<quick_reference>
**Package Manager:** npm (not yarn/pnpm)
**Node Version:** 18.x or higher
**Port:** 3000 (dev), 8080 (prod)
**Database URL:** DATABASE_URL env var
**API Base:** /api/v1
**Auth Header:** Authorization: Bearer [token]
</quick_reference>

---

_Last Updated: [DATE]_
_Version: 1.0.0_
_Maintainer: [TEAM/PERSON]_

<!--
Token Optimization Note:
This core CLAUDE.md is ~2,500 tokens.
Extended docs referenced above provide additional context on-demand.
-->
