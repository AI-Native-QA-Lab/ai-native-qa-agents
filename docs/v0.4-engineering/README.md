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

## Frozen v0.4 source of truth

v0.4 is a Test Effectiveness workflow. Mutation is an Evidence Provider, not the
product boundary:

```text
Requirement → TestEffectivenessContext → MutationRun
           → MutationTraceLink → Assessment/Gate → Decision/Termination
```

`TestEffectivenessContext` must carry the requirement id, enriched
`TestIntent`/`TestScenario` records, exact test identities, repository-relative
target/test paths, execution/assertion Evidence IDs, related Requirement,
acceptance-criteria, and risk Evidence, and a verified artifact hash. Missing
Oracle or required Evidence fails closed in `UNDERSTAND`.

The offline input is engine-agnostic report schema 1. Its process statuses are
`completed`, `partial`, `unavailable`, `error`, and `not_run`; its observation
statuses are `complete`, `partial`, and `unknown`. Backend process status is not
an Agent termination reason. `MutationTraceLink` statuses are `verified`,
`unverified`, and `unmapped`; unmapped semantic fields remain null.

Gate precedence is `incomplete → fail → pass → warn`. `incomplete` covers
missing/invalid evidence, revision conflict, unavailable or unassessable runs,
and non-sufficient termination. `fail` covers a complete quality failure,
`pass` requires a clean completed run and verified evidence/mapping, and `warn`
records an assessable partial run or lower-severity limitation.

The v0.4 budget is bounded by `max_iterations=8`, `max_tool_calls=8`,
`max_model_calls=1`, `timeout_seconds=120`, `max_replans=1`, `max_mutants=500`,
`max_report_bytes=2000000`, and `max_context_bytes=1000000`. Only a single
schema-validated `effectiveness-survivor-mapping` model task is optional; the
default path is deterministic and the model cannot alter Evidence truth,
permissions, Gate, or termination.

Real-project benchmark evidence is separate from fixtures and evals. Every case
must retain repository revision, raw artifact hashes, argv audit record,
clean/dirty-tree observation, ground truth, adjudication, metrics, and limits.
Unresolved labels and unmeasured cost/latency remain explicitly unavailable.
