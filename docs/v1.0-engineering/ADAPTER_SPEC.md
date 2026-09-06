# v1.0 Adapter Specification — AI Native QA System

## Additions
Plugin Registry; stable backend/adapter contracts; third-party compatibility tests

## Rules
Adapters translate external systems into stable domain objects. They return structured results and never own planning, re-planning, termination, or model selection.

```text
Agent Runtime → Backend Contract → Adapter → External System
```

Every adapter needs detection/capability behavior, typed errors, fixtures and contract tests.
