# v0.5 Implementation Plan — Failure Investigator

## Workstreams
1. Domain contracts — FailureRecord, FailureClassification, Hypothesis, SupportingEvidence, ContradictingEvidence, InvestigationResult
2. Agent-loop implementation — failure → hypothesis → gather evidence → challenge → reject/refine → re-plan → verify → conclusion/UNKNOWN
3. Backend/adapter implementation — pytest/JUnit XML/Playwright JSON/Jest/Allure result adapters; log read interface
4. Evidence and gates — test_failure, log_excerpt, hypothesis_support, hypothesis_contradiction; Investigation Evidence Gate
5. Model Runtime integration — task/capability based, deterministic-first
6. CLI/CI integration
7. Eval — product/test/environment classification, UNKNOWN accuracy, false-root-cause rate, evidence alignment
8. Security — Log redaction; context limits; failure text cannot authorize tools; READ/ANALYZE by default
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
