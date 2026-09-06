# v0.4 Model Runtime — Test Effectiveness & Mutation

## Principle
```text
Task → Capability → Model
```

Semantic reasoning in this version supports the non-deterministic portions of `Test Effectiveness & Mutation`.

Requirements:
- provider-neutral ModelRequest/ModelResponse
- structured output validation
- capability checks
- task-based routing as supported by current runtime version
- usage/cost/latency metadata
- explicit fallback metadata
- model policy before data upload

Model Runtime cannot mutate AgentState, bypass permissions, or terminate the Agent Loop.
