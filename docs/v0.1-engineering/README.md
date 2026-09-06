# AI Native QA Agents — v0.1 Engineering Pack

This directory contains the engineering design pack for the first implementation milestone of `ai-native-qa-agents`.

The executable baseline and verification record are recorded in [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md).

Documents:

- `ARCHITECTURE.md` — v0.1 system architecture
- `EVIDENCE_SPEC.md` — evidence model and provenance rules
- `RULE_SPEC.md` — test quality rule engine specification
- `ADAPTER_SPEC.md` — language/framework/model adapter contracts
- `CONFIGURATION.md` — repository configuration and bounded budgets
- `V0.1_IMPLEMENTATION_PLAN.md` — implementation phases and Definition of Done
- `EVAL_SPEC.md` — evaluation strategy
- `SECURITY_MODEL.md` — security boundaries
- `ISSUE_BACKLOG.md` — initial GitHub issue backlog

The v0.1 scope is intentionally narrow:

> Evidence-driven test quality review for Python/pytest and TypeScript/Playwright repositories.

---

## Agent Loop in v0.1

v0.1 includes a minimal controlled loop:

```text
Inspect → Observe → Evaluate → Verify → Gate → Stop
                     │
                     └── constrained semantic review when needed
```

It intentionally does not include a general autonomous planner.
