# v0.6 Architecture — CI / Pull Request Agent

## Delta
- Agents: PR orchestration of Reviewer / Analyst / Investigator
- Domain: Baseline, Suppression, PRReviewSummary, Annotation, CIContext, GatePolicy
- Adapters/Backends: GitHub Actions; GitHub PR metadata; SARIF; later GitLab CI
- Evidence/Gates: ci_run, baseline_delta, suppression; PR Gate

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
