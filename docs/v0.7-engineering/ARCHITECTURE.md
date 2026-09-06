# v0.7 Architecture — Release Guardian

## Delta
- Agents: Release Guardian + upstream agents
- Domain: ReleaseCandidate, ReleasePolicy, EvidenceCompleteness, ReleaseRisk, ReleaseRecommendation, ApprovalRecord
- Adapters/Backends: ReleaseBackend; CI/repository/defect/performance/security evidence import contracts
- Evidence/Gates: release_candidate, known_defect, performance_result, security_result, approval; Release Gate

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
