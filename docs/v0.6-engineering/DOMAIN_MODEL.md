# v0.6 Domain Model — CI / Pull Request Agent

## Models
Baseline, Suppression, PRReviewSummary, Annotation, CIContext, GatePolicy

## Cross-version invariants
- Version schemas.
- Findings and decisions reference evidence.
- AgentState is runtime state, not quality truth.
- Confidence is not verification.
- Durable knowledge must retain provenance.
