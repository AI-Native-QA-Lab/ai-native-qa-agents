# v0.5 Architecture — Failure Investigator

## Delta
- Agents: Failure Investigator + Quality Reviewer
- Domain: FailureRecord, FailureClassification, Hypothesis, SupportingEvidence, ContradictingEvidence, InvestigationResult
- Adapters/Backends: pytest/JUnit XML/Playwright JSON/Jest/Allure result adapters; log read interface
- Evidence/Gates: test_failure, log_excerpt, hypothesis_support, hypothesis_contradiction; Investigation Evidence Gate

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
