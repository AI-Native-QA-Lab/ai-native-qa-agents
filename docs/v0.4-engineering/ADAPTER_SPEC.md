# v0.4 Adapter Specification — Test Effectiveness & Mutation

## Additions
MutationBackend; mutmut; PIT; Stryker

## Rules
Adapters translate external systems into stable domain objects. They return structured results and never own planning, re-planning, termination, or model selection.

```text
Agent Runtime → Backend Contract → Adapter → External System
```

Every adapter needs detection/capability behavior, typed errors, fixtures and contract tests.

## Frozen interfaces

```python
detect(repository: Path) -> BackendCapability
run(request: MutationRequest) -> MutationBackendResult
parse(report_path: Path, repository_revision: str, limits: ExecutionBudget) -> MutationBackendResult
```

`MutationBackendResult` contains only backend/tool version, `process_status`,
`observation_status`, normalized mutants/results, provider Evidence, and the raw
report hash. It never contains Agent termination, Gate decisions, replanning, or
durable quality truth. `BackendCapability.status` is one of `available`,
`unavailable`, or `unsupported`.

The offline adapter accepts integer report schema 1 and validates bounded JSON,
repository-relative paths, revision, exact selected/executed/killing test IDs,
duplicate IDs, all five outcomes, and explicit observation status. It computes
the raw SHA-256 before parsing. A malformed report returns a typed
`MutationInputError` without partial success.

Typed errors are `MutationInputError`, `MutationUnavailableError`,
`MutationUnsupportedError`, `MutationConfigurationError`, and
`MutationExecutionError`. mutmut is the first controlled execution adapter and
uses an allowlisted argv, a temporary copy, timeout/resource limits, and a
read-only source boundary. PIT and Stryker provide capability/typed-error
fixtures in this slice and do not claim real execution.

Each adapter has four independent contracts: capability, typed error,
fixed input/output fixture, and security. Security fixtures cover prompt-in-data,
shell-like fields, path escape, report-size limits, and command allowlists.
