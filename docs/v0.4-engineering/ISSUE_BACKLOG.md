# v0.4 Issue Backlog — Test Effectiveness & Mutation

## 1. Domain schemas

**Acceptance:** implementation, tests, documentation, evidence/trace integration where applicable, and no regression of prior contracts.

## 16. v0.4 contract ownership

The following ownership is normative for implementation and review:

- `TestEffectivenessContext`, scoring, signals, `MutationTraceLink`, and Gate:
  `packages/qa_agent/effectiveness.py` with `tests/test_effectiveness.py`.
- Runtime budget, permission, termination, and LoopTrace:
  `packages/qa_agent/runtime.py` with `tests/test_runtime_v04.py`.
- Backend protocol and typed errors: `packages/qa_agent/mutation_backends.py`
  with `tests/test_mutation_backends.py`.
- Offline/mutmut/PIT/Stryker adapters and security fixtures:
  `packages/qa_agent/mutation_adapters.py` with
  `tests/test_mutation_adapters.py` and `tests/fixtures/v04/mutation/`.
- Additive SQLite provenance: `packages/qa_agent/trace_store.py` with
  `tests/test_trace_store_v04.py`.
- Deterministic phase loop and survivor mapping:
  `packages/qa_agent/effectiveness_service.py` with
  `tests/test_effectiveness_service.py`.
- Optional model fallback/mapping contract: `packages/qa_agent/model_runtime.py`
  and `tests/test_model_runtime.py`.
- CLI/eval/reference workflow: `packages/qa_agent/cli.py`, `evals.py`,
  `evals/v04/`, `examples/v04-sample/`, and their tests.
- Real-project benchmark: `packages/qa_agent/benchmark.py`, `benchmarks/v04/`,
  and `docs/v0.4-engineering/REAL_PROJECT_VALIDATION.md`.

Each item must preserve explicit `incomplete`, `unverified`, and `not_run`
states. No issue is accepted solely because a fixture passes; real-project,
CI, package, release, and external-indexing evidence remain separate.

## 2. Agent-loop policy

**Acceptance:** implementation, tests, documentation, evidence/trace integration where applicable, and no regression of prior contracts.

## 3. Backend contracts

**Acceptance:** implementation, tests, documentation, evidence/trace integration where applicable, and no regression of prior contracts.

## 4. Primary adapters

**Acceptance:** implementation, tests, documentation, evidence/trace integration where applicable, and no regression of prior contracts.

## 5. Evidence types

**Acceptance:** implementation, tests, documentation, evidence/trace integration where applicable, and no regression of prior contracts.

## 6. Quality gates

**Acceptance:** implementation, tests, documentation, evidence/trace integration where applicable, and no regression of prior contracts.

## 7. Model task schemas

**Acceptance:** implementation, tests, documentation, evidence/trace integration where applicable, and no regression of prior contracts.

## 8. CLI surface

**Acceptance:** implementation, tests, documentation, evidence/trace integration where applicable, and no regression of prior contracts.

## 9. JSON output

**Acceptance:** implementation, tests, documentation, evidence/trace integration where applicable, and no regression of prior contracts.

## 10. Eval fixtures

**Acceptance:** implementation, tests, documentation, evidence/trace integration where applicable, and no regression of prior contracts.

## 11. Adversarial evals

**Acceptance:** implementation, tests, documentation, evidence/trace integration where applicable, and no regression of prior contracts.

## 12. Security controls

**Acceptance:** implementation, tests, documentation, evidence/trace integration where applicable, and no regression of prior contracts.

## 13. Loop budget tests

**Acceptance:** implementation, tests, documentation, evidence/trace integration where applicable, and no regression of prior contracts.

## 14. Termination tests

**Acceptance:** implementation, tests, documentation, evidence/trace integration where applicable, and no regression of prior contracts.

## 15. Reference example

**Acceptance:** implementation, tests, documentation, evidence/trace integration where applicable, and no regression of prior contracts.
