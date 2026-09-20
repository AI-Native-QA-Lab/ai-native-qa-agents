# v0.4 Domain Model — Test Effectiveness & Mutation

## Models
MutationRun, Mutant, MutationResult, EffectivenessScore, FakeTestSignal, TestEffectivenessAssessment

## Cross-version invariants
- Version schemas.
- Findings and decisions reference evidence.
- AgentState is runtime state, not quality truth.
- Confidence is not verification.
- Durable knowledge must retain provenance.

## v0.4 contracts

`TestEffectivenessContext` is versioned as `v0.4` and contains one or more
enriched intents and scenarios, exact `test_ids`, repository-relative
`target_paths`/`test_paths`, execution/assertion Evidence IDs, related semantic
Evidence records, and a canonical artifact hash. Its Evidence references must
resolve locally or through the trace store; an ID without a record is not
evidence.

`MutationRun` records backend, repository revision, selected test identities and
paths, process/observation status, mutants, and Evidence IDs. `MutationResult`
uses exactly one of `killed`, `survived`, `timeout`, `error`, or `not_run`.
`MutationTraceLink` uses `verified`, `unverified`, or `unmapped`; an unmapped link
has null Requirement, Intent, Scenario, and Oracle fields. Exact test identity
plus verified semantic Evidence is required for a verified link.

`EffectivenessScore` counts only killed and survived mutants in its denominator,
keeps timeout/error/not_run counts separate, and uses `None` when the denominator
is zero. `FakeTestSignal` is Evidence-backed and carries source and verification
status. `TestEffectivenessAssessment` combines the run, score, links, signals,
Gate, decision, termination reason, Evidence IDs, LoopTrace, and budget.

The Mutation Gate first determines `input_complete`, `assessable_run`,
`quality_failure`, and `clean_pass`, then applies the fixed precedence
`incomplete → fail → pass → warn`. A partial process with complete observation
can warn or fail, but a partial/unknown observation, unavailable backend, missing
Oracle, missing threshold, or non-`EVIDENCE_SUFFICIENT` termination is
`incomplete`.

## v0.3 compatibility

The v0.3 `TestIntent`, `TestScenario`, and `TestEngineeringRequest` contracts keep
their old positional fields and append optional semantic fields. Legacy
serializers omit empty v0.4-only keys. A v0.3 context is accepted only through
an explicit `import_v03` path and remains marked as legacy; it is never silently
upgraded and the text `test passes` is never turned into a Business Oracle.
