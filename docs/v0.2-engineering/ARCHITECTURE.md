# v0.2 Architecture — Requirement Intelligence

## Delta
- Agents: Quality Analyst + Quality Reviewer
- Domain: Requirement, AcceptanceCriterion, TestabilityFinding, RiskItem, TraceLink, RequirementContext
- Adapters/Backends: RequirementBackend; MarkdownRequirementAdapter; GitHubIssueAdapter; SQLite trace store
- Evidence/Gates: requirement, acceptance_criteria, trace_link, risk_analysis; Requirement Gate

## Runtime
```text
Task
 ↓
Agent Runtime
 ├─ State / Budget / Termination
 ├─ Planner → Executor → Observer → Evaluator
 ├─ Re-plan when justified
 ├─ Evidence Verifier
 └─ Quality Gate → Decision / Stop
        │
        └─ semantic task → Model Runtime → Provider
```

Agent Runtime owns the loop. Model Runtime never owns termination, permissions, or durable evidence truth.
