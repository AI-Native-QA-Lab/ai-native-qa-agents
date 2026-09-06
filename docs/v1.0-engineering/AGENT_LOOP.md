# v1.0 Agent Loop — AI Native QA System

## Loop
```text
understand → plan → act → observe → evaluate → re-plan → verify → gate → decide/stop; agent-specific policies
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
