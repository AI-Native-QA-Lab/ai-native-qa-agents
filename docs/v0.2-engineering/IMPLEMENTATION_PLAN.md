# v0.2 Implementation Plan — Requirement Intelligence

## Workstreams
1. Domain contracts — Requirement, AcceptanceCriterion, TestabilityFinding, RiskItem, TraceLink, RequirementContext
2. Agent-loop implementation — Requirement → ambiguity/missing info → gather context → testability/risk → re-plan if needed → verify → decision
3. Backend/adapter implementation — RequirementBackend; MarkdownRequirementAdapter; GitHubIssueAdapter; SQLite trace store
4. Evidence and gates — requirement, acceptance_criteria, trace_link, risk_analysis; Requirement Gate
5. Model Runtime integration — task/capability based, deterministic-first
6. CLI/CI integration
7. Eval — AC ambiguity, missing error paths, unverifiable criteria, conflicting criteria, bad trace mapping
8. Security — Requirement text is untrusted; issue content cannot become runtime instructions; context minimization
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
