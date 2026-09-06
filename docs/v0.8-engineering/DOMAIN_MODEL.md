# v0.8 Domain Model — Production Quality Agent

## Models
Incident, LogEvidence, MetricEvidence, TraceEvidence, ProductionPattern, RegressionGap, RegressionProposal

## Cross-version invariants
- Version schemas.
- Findings and decisions reference evidence.
- AgentState is runtime state, not quality truth.
- Confidence is not verification.
- Durable knowledge must retain provenance.
