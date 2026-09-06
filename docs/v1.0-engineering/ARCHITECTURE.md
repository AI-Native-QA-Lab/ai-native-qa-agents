# v1.0 Architecture — AI Native QA System

## Delta
- Agents: Analyst, Engineer, Reviewer, Investigator, Guardian, Production Agent + Orchestrator
- Domain: Stable QAAgent, AgentTask, AgentState, AgentResult, SkillManifest, ToolContract, PermissionPolicy, RuntimeEvent
- Adapters/Backends: Plugin Registry; stable backend/adapter contracts; third-party compatibility tests
- Evidence/Gates: unified Evidence Spec, decision provenance, cross-agent traces; all important decisions auditable

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
