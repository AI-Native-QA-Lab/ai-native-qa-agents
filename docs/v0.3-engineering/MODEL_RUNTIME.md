# v0.3 Model Runtime — AI Test Engineer

## Principle
```text
Task → Capability → Model
```

Semantic reasoning in this version supports the non-deterministic portions of `AI Test Engineer`.

Requirements:
- provider-neutral ModelRequest/ModelResponse
- structured output validation
- capability checks
- task-based routing as supported by current runtime version
- usage/cost/latency metadata
- explicit fallback metadata
- model policy before data upload

Model Runtime cannot mutate AgentState, bypass permissions, or terminate the Agent Loop.
