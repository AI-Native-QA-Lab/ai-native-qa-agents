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

## v0.4 mapping boundary

The only model task type is `effectiveness-survivor-mapping`. It requires the
`structured_output` capability, a single model call, bounded redacted context,
and the fixed output shape:

```json
{"links":[{"mutant_id":"M-1","requirement_id":null,"intent_id":"TI-1","scenario_id":"TS-1","oracle":null,"rationale":"..."}]}
```

All IDs must exist in the bounded context, every rationale is non-empty, and
unknown/duplicate links or extra keys reject the complete mapping response.
Model-produced links stay `unverified` until deterministic Evidence verification
accepts them; a provider error, schema error, or policy denial cannot change the
Gate or termination.

`ModelFallbackMetadata` always reports `fallback_used`, `requested_provider`,
`selected_provider`, and `fallback_reason`. No fallback uses `false` and a null
reason. Provider-specific business logic does not belong in this runtime.
