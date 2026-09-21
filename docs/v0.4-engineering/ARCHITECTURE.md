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

## Inventory and data flow

The v0.4 inventory is intentionally explicit:

```text
Requirement + Evidence
  → TestEffectivenessContext
  → MutationRun / Mutant / MutationResult
  → MutationTraceLink
  → TestEffectivenessAssessment
  → Mutation Gate
```

`TestEffectivenessContext` binds Acceptance Criteria, Risk, Observable Behavior,
Business Oracle, Test Intent, Test Scenario, exact test identities, target/test
paths, and Evidence. `MutationTraceLink` maps each mutant to the strongest
available Requirement/Intent/Scenario/Oracle identity without fabricating
semantic fields. `Assessment/Gate` consumes the normalized run, score, signals,
verified Evidence, and Agent termination.

The first executable slice parses offline report schema 1. A backend may report
process status (`completed`, `partial`, `unavailable`, `error`, `not_run`) and
observation status (`complete`, `partial`, `unknown`), but only Agent Runtime
produces termination reasons. The fixed phase order is
`UNDERSTAND → SELECT → MUTATE → OBSERVE → MAP → EVALUATE → VERIFY → GATE →
DECIDE/STOP`.

The trace database is an additive v0.4 schema version 2. It stores context,
Evidence, runs, mutants, results, links, observations, assessments, and loop
traces with explicit foreign-key relationships. It is a durable output outside
the analyzed repository; the source repository remains read-only.
