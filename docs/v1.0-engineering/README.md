# v1.0 — AI Native QA System

## Goal
AI Native QA System

## Positioning
This version extends the evidence-driven QA architecture without weakening prior contracts.

## Active Agents
Analyst, Engineer, Reviewer, Investigator, Guardian, Production Agent + Orchestrator

## Version-specific Agent Loop
`understand → plan → act → observe → evaluate → re-plan → verify → gate → decide/stop; agent-specific policies`

## Estimate
8–12 weeks.

## Non-goals
fully autonomous QA, replacing QA/Dev/release owners, unlimited agent proliferation

## Definition of Done
- Real artifacts can drive the workflow end to end.
- High-impact findings/decisions reference Evidence IDs.
- Agent loop is bounded and traceable.
- Model reasoning is schema-validated and subordinate to Agent Runtime.
- New adapters have contract tests.
- Eval set contains positive, negative, ambiguous and adversarial cases.
- Security boundaries are enforced outside prompts.
