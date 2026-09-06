# v0.8 Architecture — Production Quality Agent

## Delta
- Agents: Production Quality Agent + Failure Investigator + Test Engineer proposal path
- Domain: Incident, LogEvidence, MetricEvidence, TraceEvidence, ProductionPattern, RegressionGap, RegressionProposal
- Adapters/Backends: ObservabilityBackend; OpenTelemetry; Generic JSON Logs; later Grafana/Datadog
- Evidence/Gates: incident, log, metric, trace, production_pattern, regression_gap

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
