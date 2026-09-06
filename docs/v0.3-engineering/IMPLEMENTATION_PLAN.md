# v0.3 Implementation Plan — AI Test Engineer

## Workstreams
1. Domain contracts — TestIntent, TestPlan, TestScenario, GeneratedPatch, ExecutionResult, RepairAttempt, TestCandidateStatus
2. Agent-loop implementation — Test intent → generate → parse → compile → execute → review → analyze failure → repair → retry → accept/reject
3. Backend/adapter implementation — ExecutionBackend; pytest executor; Playwright executor; TestGenerator; worktree/container sandbox
4. Evidence and gates — generated_patch, compile_result, test_execution, repair_attempt; Parse/Compile/Execution/Assertion/Reviewer Gates
5. Model Runtime integration — task/capability based, deterministic-first
6. CLI/CI integration
7. Eval — generation executability, compile success, oracle quality, repair count, fake tests, unsafe production edits
8. Security — Patch-only generation; no auto-commit; isolated execution; timeout/network/resource policy
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
8–10 weeks.

## Release Criteria
No release until loop termination, evidence provenance, adapter contracts, evals and security checks pass.
