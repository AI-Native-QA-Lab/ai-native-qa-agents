# v0.4 Implementation Plan — Test Effectiveness & Mutation

## Workstreams
1. Domain contracts — MutationRun, Mutant, MutationResult, EffectivenessScore, FakeTestSignal, TestEffectivenessAssessment
2. Agent-loop implementation — select tests/change → mutation → observe survivors → map to tests/requirements → evaluate → verify effectiveness
3. Backend/adapter implementation — MutationBackend; mutmut; PIT; Stryker
4. Evidence and gates — mutation_run, mutant_survived, mutant_killed, effectiveness_score; Mutation Gate
5. Model Runtime integration — task/capability based, deterministic-first
6. CLI/CI integration
7. Eval — mutation parser accuracy, survivor mapping, fake-test precision/recall, score stability
8. Security — Mutation execution isolation; CPU/time budget; working-tree protection; command allowlist
9. Reference example and documentation

## Phases
### 1. Contracts
Freeze schemas, capabilities, evidence types, config and errors.

### 2. Deterministic Core
Implement parsers, mapping, execution or aggregation that can be deterministic.

### 3. Agent Runtime
Implement state transitions, observations, re-plan rules, verifier, budget and termination.

### 4. Semantic Reasoning
Add structured model reasoning only where deterministic evidence is insufficient.

### 5. Gates & Outputs
Human + JSON output; SARIF where applicable.

### 6. Evals & Hardening
Golden/adversarial datasets, false-positive control, security and performance.

## Estimate
6–8 weeks.

## Release Criteria
No release until loop termination, evidence provenance, adapter contracts, evals and security checks pass.
