# v0.1 Agent Loop

```text
Detect Project → Inspect Diff → Discover Tests → Run Rules
→ Optional Semantic Review → Observe → Evidence
→ Evaluate → Verify → Gate → Stop
```

The planner is deterministic. Re-plan only chooses another predefined review action. Budgets cap iterations, tool calls and model calls. Valid terminal states include `INSUFFICIENT_EVIDENCE`, `BUDGET_EXHAUSTED`, `UNSUPPORTED_TASK`, `TIMEOUT` and `ERROR`.
