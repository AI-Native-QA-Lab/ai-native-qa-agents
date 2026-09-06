# v0.4 Architecture — Test Effectiveness & Mutation

## Delta
- Agents: Quality Reviewer + Test Engineer
- Domain: MutationRun, Mutant, MutationResult, EffectivenessScore, FakeTestSignal, TestEffectivenessAssessment
- Adapters/Backends: MutationBackend; mutmut; PIT; Stryker
- Evidence/Gates: mutation_run, mutant_survived, mutant_killed, effectiveness_score; Mutation Gate

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
