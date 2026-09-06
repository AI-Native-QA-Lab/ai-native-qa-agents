# v0.9 Architecture — Quality Knowledge Graph

## Delta
- Agents: All agents consume/write verified quality knowledge
- Domain: QualityNode, QualityEdge, GraphEvidence, EntityResolution, TemporalFact, KnowledgeQuery
- Adapters/Backends: QualityGraphBackend; SQLite graph implementation; optional Neo4j adapter
- Evidence/Gates: all persisted important edges retain provenance; Knowledge Verification Gate

## Runtime
```text
Task
 ↓
Agent Runtime
 ├─ State / Budget / Termination
 ├─ Planner → Executor → Observer → Evaluator
 ├─ Re-plan when justified
 ├─ Evidence Verifier
 └─ Quality Gate → Decision / Stop
        │
        └─ semantic task → Model Runtime → Provider
```

Agent Runtime owns the loop. Model Runtime never owns termination, permissions, or durable evidence truth.
