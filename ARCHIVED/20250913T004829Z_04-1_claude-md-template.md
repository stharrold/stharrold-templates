---
version: 1.0
last_updated: 2025-01-27T00:00:00Z
project:
  name: "PROJECT_NAME"
  type: "web_application"
  stage: "development"
  primary_language: "python"
  framework: "django"
  database: "postgresql"
tech_stack:
  languages: ["python", "javascript", "sql"]
  frameworks: ["django", "react", "tailwind"]
  tools: ["docker", "redis", "nginx"]
  services: ["aws", "stripe", "sendgrid"]
context_management:
  auto_compact_at: 95
  max_file_size: 100000
  prefer_streaming: true
agent_capabilities:
  mcp_enabled: true
  sub_agents: false
  parallel_execution: false
---

# CLAUDE.md - Project Context & Agent Instructions

## 📋 Project Overview

**Application**: [Brief description of what this project does]
**Target Users**: [Who will use this application]
**Core Value**: [What problem it solves]
**Current Phase**: [MVP/Beta/Production]

### Key Business Rules
1. [Critical business logic or constraint]
2. [Another important rule]
3. [Domain-specific requirement]

## 🏗️ Architecture Overview

```
src/
├── api/          # REST API endpoints
├── models/       # Database models
├── services/     # Business logic
├── utils/        # Helper functions
└── tests/        # Test suite

frontend/
├── components/   # React components
├── pages/        # Next.js pages
├── styles/       # CSS/Tailwind
└── utils/        # Frontend helpers
```

### Key Design Decisions
- **Pattern**: [MVC/Microservices/Monolith]
- **Authentication**: [JWT/Session/OAuth]
- **State Management**: [Redux/Context/Zustand]
- **API Style**: [REST/GraphQL/gRPC]

## 🎯 Current Focus Areas

### Active Development
- Feature: [What's being built now]
- Priority: [Why this matters]
- Deadline: [If applicable]

### Technical Debt
- [Area needing refactoring]
- [Performance bottleneck]
- [Security concern]

## 📐 Development Standards

### Code Style
```python
# Python: PEP 8 with type hints
def process_data(input_data: dict[str, Any]) -> ProcessResult:
    """Docstring required for all public functions."""
    pass
```

```javascript
// JavaScript: ESLint + Prettier
const processData = async (inputData: InputType): Promise<ResultType> => {
  // Prefer const, async/await, arrow functions
};
```

### Git Workflow
- Branch naming: `feature/`, `fix/`, `chore/`
- Commit style: Conventional Commits
- PR required for main branch
- Squash merge preferred

### Testing Requirements
- Unit tests for business logic (>80% coverage)
- Integration tests for API endpoints
- E2E tests for critical user flows
- Run tests before committing: `npm test`

## 🔒 Security Guidelines

### Critical Rules
1. **Never commit secrets** - Use environment variables
2. **Validate all inputs** - Assume user input is malicious
3. **Parameterize queries** - Prevent SQL injection
4. **Sanitize outputs** - Prevent XSS attacks
5. **Check dependencies** - Run `npm audit` regularly

### Sensitive Areas
- `/src/auth/` - Authentication logic
- `/src/payments/` - Payment processing
- `.env` files - Never commit these
- API keys - Store in secure vault

## 🚀 Development Workflow

### Starting a Session
1. Check `TODO.md` for current tasks
2. Review recent commits: `git log --oneline -10`
3. Pull latest changes: `git pull origin main`
4. Check build status: `npm run build`
5. Run tests: `npm test`

### Making Changes
1. Create feature branch
2. Write tests first (TDD preferred)
3. Implement feature
4. Update documentation
5. Create pull request

### Before Completing Session
1. Update `TODO.md` with progress
2. Commit all changes with clear messages
3. Push to remote repository
4. Update task status in project tracker
5. Leave notes for next session if needed

## 🛠️ Common Commands

```bash
# Development
npm run dev           # Start dev server
npm run build        # Build for production
npm run test         # Run test suite
npm run lint         # Check code style

# Database
npm run db:migrate   # Run migrations
npm run db:seed      # Seed database
npm run db:reset     # Reset database

# Docker
docker-compose up    # Start all services
docker-compose down  # Stop services
docker logs app      # View app logs
```

## 📊 Performance Targets

- Page Load: < 2s (LCP)
- API Response: < 200ms (p95)
- Database Queries: < 50ms
- Bundle Size: < 500KB
- Test Coverage: > 80%

## 🔗 Important Links

- **Repository**: [github.com/org/repo]
- **Documentation**: [docs.example.com]
- **Staging**: [staging.example.com]
- **Production**: [example.com]
- **CI/CD**: [Link to pipeline]
- **Monitoring**: [Link to dashboard]

## 🤖 Agent-Specific Instructions

### Context Awareness
- Always check `TODO.md` at session start
- Maintain awareness of project stage (dev/staging/prod)
- Consider performance impact of changes
- Follow established patterns in codebase

### Decision Making
- Prefer readability over cleverness
- Choose boring technology over cutting edge
- Optimize for maintainability
- Document non-obvious choices

### Error Handling
- Use structured error responses
- Log errors with appropriate severity
- Provide helpful error messages
- Never expose sensitive data in errors

### Communication
- Update task status in real-time
- Leave clear commit messages
- Document complex logic inline
- Flag security concerns immediately

## 📚 Domain Knowledge

### Business Terminology
- **[Term 1]**: [Definition specific to this project]
- **[Term 2]**: [Another domain-specific term]

### External Integrations
- **Payment Provider**: [Stripe/PayPal/etc]
  - Test keys in `.env.development`
  - Webhook endpoint: `/api/webhooks/payment`
  
- **Email Service**: [SendGrid/SES/etc]
  - Template IDs in `/config/email.json`
  - Rate limit: 100/hour

### Data Models
```python
# Key relationships to remember
User -> has_many -> Projects
Project -> has_many -> Tasks
Task -> belongs_to -> User (assignee)
```

## ⚠️ Known Issues & Gotchas

### Current Bugs
- [ ] [Description of known issue]
- [ ] [Another unresolved problem]

### Common Pitfalls
- Database migrations must run in order
- Redis must be running for sessions
- CORS configured for specific domains only
- Rate limiting active on production

## 🔄 Maintenance Tasks

### Daily
- Check error logs
- Monitor performance metrics
- Review security alerts

### Weekly
- Update dependencies
- Run full test suite
- Backup database

### Monthly
- Security audit
- Performance profiling
- Documentation review

---

## Session Notes

<!-- Use this section for temporary notes during active development -->
<!-- Clear this section at the start of each new session -->

### Current Session
- Started: [timestamp]
- Working on: [current task]
- Blockers: [any issues]
- Next steps: [what's next]

---

*This document is the source of truth for project context. Update it as the project evolves.*