# v0.9 Implementation Plan — Quality Knowledge Graph

## Workstreams
1. Domain contracts — QualityNode, QualityEdge, GraphEvidence, EntityResolution, TemporalFact, KnowledgeQuery
2. Agent-loop implementation — new evidence → entity resolution → link proposal → verify link → persist → query → next-task context
3. Backend/adapter implementation — QualityGraphBackend; SQLite graph implementation; optional Neo4j adapter
4. Evidence and gates — all persisted important edges retain provenance; Knowledge Verification Gate
5. Model Runtime integration — task/capability based, deterministic-first
6. CLI/CI integration
7. Eval — entity resolution, edge precision, temporal correctness, query accuracy, stale evidence handling
8. Security — Source permissions propagate; sensitive graph access control; unverified LLM inference not persisted as fact
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
