# Workflow Phases Diagram

Visual representation of the 7-phase workflow system.

## Phase Flow

```mermaid
flowchart TB
    subgraph Feature["Feature Workflow (Phases 1-5)"]
        P1[1. Specify<br/>Create feature branch<br/>and specification]
        P2[2. Plan<br/>Generate specs via<br/>speckit-author]
        P3[3. Tasks<br/>Validate task list<br/>from plan.md]
        P4[4. Implement<br/>Execute tasks +<br/>run quality gates]
        P5[5. Integrate<br/>Create PRs,<br/>cleanup worktree]

        P1 --> P2 --> P3 --> P4 --> P5
    end

    subgraph Release["Release Workflow (Phases 6-7)"]
        P6[6. Release<br/>develop → release → main]
        P7[7. Backmerge<br/>Sync release to<br/>develop and contrib]

        P6 --> P7
    end

    P5 --> |"Ready for<br/>production"| P6
    P7 --> |"Next feature"| P1
```

## Branch Flow

```mermaid
gitGraph
    commit id: "main"
    branch develop
    commit id: "develop"
    branch contrib/user
    commit id: "contrib"
    branch feature/auth
    commit id: "implement"
    commit id: "tests"
    checkout contrib/user
    merge feature/auth id: "PR: feature→contrib"
    checkout develop
    merge contrib/user id: "PR: contrib→develop"
    branch release/v1.0
    commit id: "release prep"
    checkout main
    merge release/v1.0 id: "PR: release→main" tag: "v1.0.0"
    checkout develop
    merge release/v1.0 id: "backmerge"
```

## Quality Gates

```mermaid
flowchart LR
    subgraph Gates["5 Quality Gates"]
        G1[1. Coverage<br/>≥80%]
        G2[2. Tests<br/>All pass]
        G3[3. Build<br/>uv build]
        G4[4. Linting<br/>ruff check]
        G5[5. AI Sync<br/>CLAUDE.md]

        G1 --> G2 --> G3 --> G4 --> G5
    end

    Start([Start]) --> G1
    G5 --> Pass{All Pass?}
    Pass -->|Yes| PR[Create PR]
    Pass -->|No| Fix[Fix Issues]
    Fix --> Start
```

## Skill Dependencies

```mermaid
flowchart TD
    subgraph Core["Core Skills"]
        WO[workflow-orchestrator]
        TSA[tech-stack-adapter]
        WU[workflow-utilities]
    end

    subgraph Planning["Planning Skills"]
        BP[bmad-planner]
        SA[speckit-author]
    end

    subgraph Execution["Execution Skills"]
        GWM[git-workflow-manager]
        QE[quality-enforcer]
        ADB[agentdb-state-manager]
    end

    subgraph Setup["Setup Skills"]
        IR[initialize-repository]
    end

    WO --> TSA
    WO --> BP
    WO --> SA
    WO --> GWM
    WO --> QE
    WO --> WU
    WO --> ADB

    BP --> SA
    SA --> GWM
    GWM --> QE
    QE --> GWM

    TSA --> |"detect stack"| BP
    TSA --> |"detect stack"| QE

    WU --> |"utilities"| GWM
    WU --> |"utilities"| QE
    WU --> |"utilities"| ADB

    IR --> |"bootstrap"| WO
```

## Slash Command Navigation

```mermaid
flowchart LR
    ALL[/workflow/all] --> |"auto-detect"| STATE{Current State}

    STATE --> |"no feature"| S1[/1_specify]
    STATE --> |"has spec"| S2[/2_plan]
    STATE --> |"has plan"| S3[/3_tasks]
    STATE --> |"has tasks"| S4[/4_implement]
    STATE --> |"implemented"| S5[/5_integrate]
    STATE --> |"on develop"| S6[/6_release]
    STATE --> |"released"| S7[/7_backmerge]

    S1 --> S2 --> S3 --> S4 --> S5
    S5 --> |"feature complete"| S6
    S6 --> S7
    S7 --> |"ready for next"| S1
```

## Document Lifecycle

```mermaid
flowchart LR
    subgraph Research["docs/research/"]
        R1[Exploratory docs]
        R2[Investigation notes]
    end

    subgraph Guides["docs/guides/"]
        G1[Production docs]
        G2[Implementation guides]
    end

    subgraph Archived["docs/archived/"]
        A1[Compressed archives]
        A2[Historical versions]
    end

    Research --> |"mature"| Guides
    Guides --> |"superseded"| Archived
```

## Related Documentation

- [WORKFLOW.md](../../WORKFLOW.md) - Complete workflow guide
- [workflow-planning.md](workflow-planning.md) - Phases 0-3
- [workflow-integration.md](workflow-integration.md) - Phases 4-5
- [workflow-operations.md](workflow-operations.md) - Operations
