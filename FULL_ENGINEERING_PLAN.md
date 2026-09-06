# AI Native QA Agents — Full Engineering Plan

## Core Architecture

```text
Agent Runtime
+ Model Runtime
+ Skills
+ Tools / Backends / Adapters
+ Evidence
+ Quality Gates
+ Evals
```

## Agent Loop

```text
Understand → Plan → Act → Observe → Evaluate
                  ↑                │
                  └──── Re-plan ───┘
                                   ↓
                                Verify
                                   ↓
                             Quality Gate
                                   ↓
                              Decide / Stop
```

## Complete Version Map

| Version | Theme | Agent-loop evolution |
|---|---|---|
| v0.1 | PR Quality Reviewer | Minimal controlled review loop |
| v0.2 | Requirement Intelligence | Stateful re-plan/context expansion |
| v0.3 | AI Test Engineer | Generate/execute/repair loop |
| v0.4 | Test Effectiveness & Mutation | Mutation/effectiveness loop |
| v0.5 | Failure Investigator | Hypothesis/challenge loop |
| v0.6 | CI / Pull Request Agent | PR aggregation/baseline loop |
| v0.7 | Release Guardian | Policy-aware decision loop |
| v0.8 | Production Quality Agent | Production feedback loop |
| v0.9 | Quality Knowledge Graph | Verified knowledge persistence loop |
| v1.0 | AI Native QA System | Stable generic Agent Runtime |

## Non-negotiable Principles

1. Evidence over opinion.
2. Verification over generation.
3. Deterministic first.
4. Context over giant prompts.
5. Controlled Agent Loops over free-running LLM loops.
6. Explicit budgets and termination.
7. Human approval for WRITE/RELEASE boundaries.
8. Task → Capability → Model.
9. Fewer high-confidence findings over generic warning volume.
10. Evals are part of product behavior.

Every version under `docs/` has architecture, implementation plan, domain model, Agent Loop, adapters, evidence/gates, Model Runtime integration, eval, security and issue backlog.
