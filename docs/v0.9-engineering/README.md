# v0.9 — Quality Knowledge Graph

## Goal
Quality Knowledge Graph

## Positioning
This version extends the evidence-driven QA architecture without weakening prior contracts.

## Active Agents
All agents consume/write verified quality knowledge

## Version-specific Agent Loop
`new evidence → entity resolution → link proposal → verify link → persist → query → next-task context`

## Estimate
8–10 weeks.

## Non-goals
early Neo4j dependency, treating chat memory as verified quality fact

## Definition of Done
- Real artifacts can drive the workflow end to end.
- High-impact findings/decisions reference Evidence IDs.
- Agent loop is bounded and traceable.
- Model reasoning is schema-validated and subordinate to Agent Runtime.
- New adapters have contract tests.
- Eval set contains positive, negative, ambiguous and adversarial cases.
- Security boundaries are enforced outside prompts.
