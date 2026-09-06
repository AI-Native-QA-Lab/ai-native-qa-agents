# v0.4 Domain Model — Test Effectiveness & Mutation

## Models
MutationRun, Mutant, MutationResult, EffectivenessScore, FakeTestSignal, TestEffectivenessAssessment

## Cross-version invariants
- Version schemas.
- Findings and decisions reference evidence.
- AgentState is runtime state, not quality truth.
- Confidence is not verification.
- Durable knowledge must retain provenance.
