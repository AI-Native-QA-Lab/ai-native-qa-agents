# v0.7 Adapter Specification — Release Guardian

## Additions
ReleaseBackend; CI/repository/defect/performance/security evidence import contracts

## Rules
Adapters translate external systems into stable domain objects. They return structured results and never own planning, re-planning, termination, or model selection.

```text
Agent Runtime → Backend Contract → Adapter → External System
```

Every adapter needs detection/capability behavior, typed errors, fixtures and contract tests.
