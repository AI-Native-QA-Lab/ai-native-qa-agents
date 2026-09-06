# v0.3 Agent Loop — AI Test Engineer

## Loop
```text
Test intent → generate → parse → compile → execute → review → analyze failure → repair → retry → accept/reject
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
