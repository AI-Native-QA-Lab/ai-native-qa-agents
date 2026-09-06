# v0.5 Adapter Specification — Failure Investigator

## Additions
pytest/JUnit XML/Playwright JSON/Jest/Allure result adapters; log read interface

## Rules
Adapters translate external systems into stable domain objects. They return structured results and never own planning, re-planning, termination, or model selection.

```text
Agent Runtime → Backend Contract → Adapter → External System
```

Every adapter needs detection/capability behavior, typed errors, fixtures and contract tests.
