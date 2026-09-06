# v0.9 Agent Loop — Quality Knowledge Graph

## Loop
```text
new evidence → entity resolution → link proposal → verify link → persist → query → next-task context
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
