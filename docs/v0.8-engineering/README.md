# v0.8 — Production Quality Agent

## Goal
Production Quality Agent

## Positioning
This version extends the evidence-driven QA architecture without weakening prior contracts.

## Active Agents
Production Quality Agent + Failure Investigator + Test Engineer proposal path

## Version-specific Agent Loop
`incident → telemetry → pattern → related code/requirement/test → gap hypothesis → verify → regression proposal`

## Estimate
8 weeks.

## Non-goals
production changes, unlimited log collection, replacing APM

## Definition of Done
- Real artifacts can drive the workflow end to end.
- High-impact findings/decisions reference Evidence IDs.
- Agent loop is bounded and traceable.
- Model reasoning is schema-validated and subordinate to Agent Runtime.
- New adapters have contract tests.
- Eval set contains positive, negative, ambiguous and adversarial cases.
- Security boundaries are enforced outside prompts.
