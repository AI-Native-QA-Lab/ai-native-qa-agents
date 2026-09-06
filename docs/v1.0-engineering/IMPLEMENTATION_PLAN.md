# v1.0 Implementation Plan — AI Native QA System

## Workstreams
1. Domain contracts — Stable QAAgent, AgentTask, AgentState, AgentResult, SkillManifest, ToolContract, PermissionPolicy, RuntimeEvent
2. Agent-loop implementation — understand → plan → act → observe → evaluate → re-plan → verify → gate → decide/stop; agent-specific policies
3. Backend/adapter implementation — Plugin Registry; stable backend/adapter contracts; third-party compatibility tests
4. Evidence and gates — unified Evidence Spec, decision provenance, cross-agent traces; all important decisions auditable
5. Model Runtime integration — task/capability based, deterministic-first
6. CLI/CI integration
7. Eval — agent/skill/tool/workflow/system evals; cross-model/framework/version regression; cost/quality benchmark
8. Security — Stable permission model; tool sandbox; model governance; plugin trust; supply-chain controls; approval
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
8–12 weeks.

## Release Criteria
No release until loop termination, evidence provenance, adapter contracts, evals and security checks pass.
