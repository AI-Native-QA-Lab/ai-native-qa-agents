# v0.3 Domain Model — AI Test Engineer

## Models
TestIntent, TestPlan, TestScenario, GeneratedPatch, ExecutionResult, RepairAttempt, TestCandidateStatus

## Cross-version invariants
- Version schemas.
- Findings and decisions reference evidence.
- AgentState is runtime state, not quality truth.
- Confidence is not verification.
- Durable knowledge must retain provenance.

## v0.4 entry contract

The v0.4 TestEffectivenessContext consumes v0.3 Intent/Scenario records only
through an explicit legacy import. Its appended fields are
`acceptance_criterion_ids`, `risk_ids`, `observable_behavior`, and
`business_oracle`; scenarios also carry acceptance-criterion and exact test
identities. Missing fields keep their v0.3 defaults and do not become fabricated
semantic evidence.

The v0.4 workflow requires a verified Business Oracle and related Evidence before
it can assess Mutation effectiveness. If the Oracle is absent, the workflow
returns `decision=incomplete` and `termination_reason=INSUFFICIENT_EVIDENCE`.
This compatibility rule keeps v0.3 legacy behavior while preventing an old
generated candidate or a plain `test passes` statement from being treated as a
business-quality proof.
