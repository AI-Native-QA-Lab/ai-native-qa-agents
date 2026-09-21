# v0.4 Agent Loop — Test Effectiveness & Mutation

## Loop
```text
select tests/change → mutation → observe survivors → map to tests/requirements → evaluate → verify effectiveness
```

## Common state machine
```text
UNDERSTAND → PLAN → ACT → OBSERVE → EVALUATE
                 ↑                    │
                 └──── RE-PLAN ───────┘
                                      ↓
                                   VERIFY
                                      ↓
                                    GATE
                                      ↓
                                 DECIDE/STOP
```

## Required controls
- ExecutionBudget
- TerminationPolicy
- LoopTrace
- permission check before action
- Observation before Evidence
- Evaluate separate from Verify
- valid terminal states: EVIDENCE_SUFFICIENT, INSUFFICIENT_EVIDENCE, BUDGET_EXHAUSTED, TIMEOUT, HUMAN_APPROVAL_REQUIRED, ERROR

## v0.4 fixed phases

The executable path is:

```text
UNDERSTAND → SELECT → MUTATE → OBSERVE → MAP → EVALUATE → VERIFY → GATE → DECIDE/STOP
```

Every phase creates an Observation before its Evidence and appends a LoopTrace.
Permission is checked before SELECT and MUTATE. The default path parses report
schema 1 deterministically; the backend reports process/observation status, while
Agent Runtime owns termination and Gate decisions.

The v0.4 defaults are `max_iterations=8`, `max_tool_calls=8`,
`max_model_calls=1`, `timeout_seconds=120`, `max_replans=1`, `max_mutants=500`,
`max_report_bytes=2000000`, and `max_context_bytes=1000000`. Phase transitions,
backend capability/read/execute, model invocation, durable queries, re-plans,
and raw input bytes consume their corresponding limits. Timeout uses a monotonic
clock; exhausted limits terminate with `BUDGET_EXHAUSTED`.

Permission actions are `READ`, `EXECUTE_MUTATION`, `MODEL_SURVIVOR_MAPPING`,
`WRITE`, `COMMIT`, `MERGE`, and `RELEASE`. v0.4 allows only the first three,
and WRITE/COMMIT/MERGE/RELEASE are always denied. A permission result records
action, allowed, reason, Evidence ID, and whether an external command ran.

`LoopTrace` preserves the legacy iteration/action/status/observation fields and
adds assessment id, phase, permission Evidence ID, Evidence IDs, and termination
reason. Replanning is limited to one explicit action and cannot be triggered by a
model suggestion alone.
