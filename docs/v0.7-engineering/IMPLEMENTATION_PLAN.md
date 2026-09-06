# v0.7 Implementation Plan — Release Guardian

## Workstreams
1. Domain contracts — ReleaseCandidate, ReleasePolicy, EvidenceCompleteness, ReleaseRisk, ReleaseRecommendation, ApprovalRecord
2. Agent-loop implementation — collect → completeness check → request missing evidence → apply policy → verify → recommend → human approval
3. Backend/adapter implementation — ReleaseBackend; CI/repository/defect/performance/security evidence import contracts
4. Evidence and gates — release_candidate, known_defect, performance_result, security_result, approval; Release Gate
5. Model Runtime integration — task/capability based, deterministic-first
6. CLI/CI integration
7. Eval — GO/GO_WITH_RISK/NO_GO/INSUFFICIENT_EVIDENCE accuracy, policy compliance, false-release rate
8. Security — RELEASE requires approval; policy cannot be overridden by model; auditable evidence and approvals
9. Reference example and documentation

## Phases
### 1. Contracts
Freeze schemas, capabilities, evidence types, config and errors.

### 2. Deterministic Core
Implement parsers, mapping, execution or aggregation that can be deterministic.

### 3. Agent Runtime
Implement state transitions, observations, re-plan rules, verifier, budget and termination.

### 4. Semantic Reasoning
Add structured model reasoning only where deterministic evidence is insufficient.

### 5. Gates & Outputs
Human + JSON output; SARIF where applicable.

### 6. Evals & Hardening
Golden/adversarial datasets, false-positive control, security and performance.

## Estimate
6–8 weeks.

## Release Criteria
No release until loop termination, evidence provenance, adapter contracts, evals and security checks pass.
