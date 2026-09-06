# v0.1 Model Runtime

v0.1 implements the minimum provider-neutral layer:

- `ModelProvider`
- `ModelRequest` / `ModelResponse`
- structured output validation
- AI enabled/disabled
- OpenAI and Anthropic reference adapters
- usage/latency tracking

Agent Runtime owns the review loop. Model Runtime performs only optional semantic review and cannot bypass evidence verification, permissions or termination.
