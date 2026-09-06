# v0.5 Domain Model — Failure Investigator

## Models
FailureRecord, FailureClassification, Hypothesis, SupportingEvidence, ContradictingEvidence, InvestigationResult

## Cross-version invariants
- Version schemas.
- Findings and decisions reference evidence.
- AgentState is runtime state, not quality truth.
- Confidence is not verification.
- Durable knowledge must retain provenance.
