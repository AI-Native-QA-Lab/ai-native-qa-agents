# v0.6 Implementation Plan — CI / Pull Request Agent

## Workstreams
1. Domain contracts — Baseline, Suppression, PRReviewSummary, Annotation, CIContext, GatePolicy
2. Agent-loop implementation — collect PR context → run relevant analyses → aggregate → baseline delta → verify → gate → concise publish
3. Backend/adapter implementation — GitHub Actions; GitHub PR metadata; SARIF; later GitLab CI
4. Evidence and gates — ci_run, baseline_delta, suppression; PR Gate
5. Model Runtime integration — task/capability based, deterministic-first
6. CLI/CI integration
7. Eval — decision accuracy, new-vs-existing findings, annotation location, spam rate, fork behavior, cost
8. Security — Fork PR secret protection; minimal token permissions; AI safe-disable; PR content untrusted
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
6 weeks.

## Release Criteria
No release until loop termination, evidence provenance, adapter contracts, evals and security checks pass.
