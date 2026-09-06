# v0.4 — Test Effectiveness & Mutation

## Goal
Test Effectiveness & Mutation

## Positioning
This version extends the evidence-driven QA architecture without weakening prior contracts.

## Active Agents
Quality Reviewer + Test Engineer

## Version-specific Agent Loop
`select tests/change → mutation → observe survivors → map to tests/requirements → evaluate → verify effectiveness`

## Estimate
6–8 weeks.

## Non-goals
all-language mutation support, opaque fake_probability, auto-accept generated tests

## Definition of Done
- Real artifacts can drive the workflow end to end.
- High-impact findings/decisions reference Evidence IDs.
- Agent loop is bounded and traceable.
- Model reasoning is schema-validated and subordinate to Agent Runtime.
- New adapters have contract tests.
- Eval set contains positive, negative, ambiguous and adversarial cases.
- Security boundaries are enforced outside prompts.
