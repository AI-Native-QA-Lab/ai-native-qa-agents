# v0.7 Agent Loop — Release Guardian

## Loop
```text
collect → completeness check → request missing evidence → apply policy → verify → recommend → human approval
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
