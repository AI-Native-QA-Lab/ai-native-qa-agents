# v0.3 Domain Model — AI Test Engineer

## Models
TestIntent, TestPlan, TestScenario, GeneratedPatch, ExecutionResult, RepairAttempt, TestCandidateStatus

## Cross-version invariants
- Version schemas.
- Findings and decisions reference evidence.
- AgentState is runtime state, not quality truth.
- Confidence is not verification.
- Durable knowledge must retain provenance.
