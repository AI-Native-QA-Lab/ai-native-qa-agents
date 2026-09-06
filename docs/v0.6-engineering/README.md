# v0.6 — CI / Pull Request Agent

## Goal
CI / Pull Request Agent

## Positioning
This version extends the evidence-driven QA architecture without weakening prior contracts.

## Active Agents
PR orchestration of Reviewer / Analyst / Investigator

## Version-specific Agent Loop
`collect PR context → run relevant analyses → aggregate → baseline delta → verify → gate → concise publish`

## Estimate
6 weeks.

## Non-goals
release decision, autonomous merge

## Definition of Done
- Real artifacts can drive the workflow end to end.
- High-impact findings/decisions reference Evidence IDs.
- Agent loop is bounded and traceable.
- Model reasoning is schema-validated and subordinate to Agent Runtime.
- New adapters have contract tests.
- Eval set contains positive, negative, ambiguous and adversarial cases.
- Security boundaries are enforced outside prompts.
