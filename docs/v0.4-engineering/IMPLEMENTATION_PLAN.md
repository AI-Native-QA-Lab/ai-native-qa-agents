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

## Exact implementation boundaries

| Slice | Source | Tests and assets |
| --- | --- | --- |
| v0.3 semantic compatibility | `packages/qa_agent/test_engineering.py`, `test_engineering_service.py`, `review.py`, `requirements.py` | `tests/test_v03_compatibility.py` and existing v0.3 tests |
| Runtime controls | `packages/qa_agent/runtime.py` | `tests/test_runtime_v04.py` |
| Domain and Gate | `packages/qa_agent/effectiveness.py` | `tests/test_effectiveness.py`, `tests/fixtures/v04/context-valid.json` |
| Backend contracts | `packages/qa_agent/mutation_backends.py` | `tests/test_mutation_backends.py` |
| Adapters | `packages/qa_agent/mutation_adapters.py` | `tests/test_mutation_adapters.py`, `tests/fixtures/v04/mutation/` |
| Persistence | `packages/qa_agent/trace_store.py` | `tests/test_trace_store_v04.py` |
| Deterministic service | `packages/qa_agent/effectiveness_service.py` | `tests/test_effectiveness_service.py` |
| Optional model mapping | `packages/qa_agent/model_runtime.py` | `tests/test_model_runtime.py` |
| CLI/evals/example | `packages/qa_agent/cli.py`, `evals.py` | `tests/test_cli_effectiveness.py`, `tests/test_v04_evals.py`, `evals/v04/`, `examples/v04-sample/` |
| Real-project validation | `packages/qa_agent/benchmark.py` | `tests/test_benchmark.py`, `benchmarks/v04/`, `docs/v0.4-engineering/REAL_PROJECT_VALIDATION.md` |

Every implementation slice follows RED → GREEN → REFACTOR. Deterministic
collection and verification precede model reasoning. Generated patches remain
untrusted and no task may write, commit, merge, or release to the analyzed
repository.

## Frozen output boundary

The v0.4 JSON/human output must distinguish score status, eligible/killed/
survived/timeout/error/not_run counts, survivor mapping, signals, Evidence IDs,
Gate, LoopTrace, budget, and artifact hashes. Local tests and reference fixtures
do not establish real-project, CI, package, release, or external-indexing
evidence.
