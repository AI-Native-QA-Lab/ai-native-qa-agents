# v0.3 — AI Test Engineer

## Goal
AI Test Engineer

## Positioning
This version extends the evidence-driven QA architecture without weakening prior contracts.

## Active Agents
Test Engineer + Quality Reviewer + Quality Analyst

## Version-specific Agent Loop
`Test intent → generate → parse → compile → execute → review → analyze failure → repair → retry → accept/reject`

## Estimate
8–10 weeks.

## Non-goals
Mutation, autonomous production-code repair, unattended writes

## Definition of Done
- Real artifacts can drive the workflow end to end.
- High-impact findings/decisions reference Evidence IDs.
- Agent loop is bounded and traceable.
- Model reasoning is schema-validated and subordinate to Agent Runtime.
- New adapters have contract tests.
- Eval set contains positive, negative, ambiguous and adversarial cases.
- Security boundaries are enforced outside prompts.
