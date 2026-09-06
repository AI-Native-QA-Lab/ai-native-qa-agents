# v0.6 Adapter Specification — CI / Pull Request Agent

## Additions
GitHub Actions; GitHub PR metadata; SARIF; later GitLab CI

## Rules
Adapters translate external systems into stable domain objects. They return structured results and never own planning, re-planning, termination, or model selection.

```text
Agent Runtime → Backend Contract → Adapter → External System
```

Every adapter needs detection/capability behavior, typed errors, fixtures and contract tests.
