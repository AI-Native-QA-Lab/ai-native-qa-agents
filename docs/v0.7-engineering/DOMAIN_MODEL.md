# v0.7 Domain Model — Release Guardian

## Models
ReleaseCandidate, ReleasePolicy, EvidenceCompleteness, ReleaseRisk, ReleaseRecommendation, ApprovalRecord

## Cross-version invariants
- Version schemas.
- Findings and decisions reference evidence.
- AgentState is runtime state, not quality truth.
- Confidence is not verification.
- Durable knowledge must retain provenance.
