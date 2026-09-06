# v0.3 Architecture — AI Test Engineer

## Delta
- Agents: Test Engineer + Quality Reviewer + Quality Analyst
- Domain: TestIntent, TestPlan, TestScenario, GeneratedPatch, ExecutionResult, RepairAttempt, TestCandidateStatus
- Adapters/Backends: ExecutionBackend; pytest executor; Playwright executor; TestGenerator; worktree/container sandbox
- Evidence/Gates: generated_patch, compile_result, test_execution, repair_attempt; Parse/Compile/Execution/Assertion/Reviewer Gates

## Runtime
```text
Task
 ↓
Agent Runtime
 ├─ State / Budget / Termination
 ├─ Planner → Executor → Observer → Evaluator
 ├─ Re-plan when justified
 ├─ Evidence Verifier
 └─ Quality Gate → Decision / Stop
        │
        └─ semantic task → Model Runtime → Provider
```

Agent Runtime owns the loop. Model Runtime never owns termination, permissions, or durable evidence truth.
