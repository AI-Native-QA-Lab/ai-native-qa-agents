# v0.7 — Release Guardian

## Goal
Release Guardian

## Positioning
This version extends the evidence-driven QA architecture without weakening prior contracts.

## Active Agents
Release Guardian + upstream agents

## Version-specific Agent Loop
`collect → completeness check → request missing evidence → apply policy → verify → recommend → human approval`

## Estimate
6–8 weeks.

## Non-goals
autonomous deployment, universal hard-coded release thresholds

## Definition of Done
- Real artifacts can drive the workflow end to end.
- High-impact findings/decisions reference Evidence IDs.
- Agent loop is bounded and traceable.
- Model reasoning is schema-validated and subordinate to Agent Runtime.
- New adapters have contract tests.
- Eval set contains positive, negative, ambiguous and adversarial cases.
- Security boundaries are enforced outside prompts.
