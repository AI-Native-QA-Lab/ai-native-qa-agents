# v0.5 — Failure Investigator

## Goal
Failure Investigator

## Positioning
This version extends the evidence-driven QA architecture without weakening prior contracts.

## Active Agents
Failure Investigator + Quality Reviewer

## Version-specific Agent Loop
`failure → hypothesis → gather evidence → challenge → reject/refine → re-plan → verify → conclusion/UNKNOWN`

## Estimate
6–8 weeks.

## Non-goals
automatic production fixes, forced root cause, full observability integration

## Definition of Done
- Real artifacts can drive the workflow end to end.
- High-impact findings/decisions reference Evidence IDs.
- Agent loop is bounded and traceable.
- Model reasoning is schema-validated and subordinate to Agent Runtime.
- New adapters have contract tests.
- Eval set contains positive, negative, ambiguous and adversarial cases.
- Security boundaries are enforced outside prompts.
