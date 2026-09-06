"""Provider-neutral model contracts with optional injected provider callables."""

from dataclasses import dataclass, field
import time
from typing import Any, Protocol


@dataclass(frozen=True)
class ModelUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost: float | None = None


@dataclass(frozen=True)
class ModelRequest:
    task_type: str
    messages: tuple[dict[str, str], ...] = ()
    output_schema: dict[str, Any] | None = None
    required_capabilities: tuple[str, ...] = ()
    max_output_tokens: int | None = None


@dataclass(frozen=True)
class ModelResponse:
    provider: str
    model: str
    content: str | None = None
    structured_output: dict[str, Any] | None = None
    usage: ModelUsage = field(default_factory=ModelUsage)
    latency_ms: int | None = None
    finish_reason: str | None = None


@dataclass(frozen=True)
class ModelCapabilities:
    structured_output: bool = False
    tool_calling: bool = False
    reasoning: bool = False
    max_context_tokens: int | None = None


@dataclass
class ModelUsageTracker:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0

    def record(self, response: ModelResponse) -> None:
        self.calls += 1
        self.input_tokens += response.usage.input_tokens or 0
        self.output_tokens += response.usage.output_tokens or 0
        self.latency_ms += response.latency_ms or 0


class ModelProvider(Protocol):
    provider_name: str
    def capabilities(self, model: str) -> ModelCapabilities: ...
    def invoke(self, model: str, request: ModelRequest) -> ModelResponse: ...


class StructuredOutputValidator:
    def validate(self, request: ModelRequest, response: ModelResponse) -> ModelResponse:
        if request.output_schema is not None and not isinstance(response.structured_output, dict):
            raise ValueError("model response does not contain structured output")
        return response


class _CallableProvider:
    provider_name = "injected"
    def __init__(self, provider_name: str, model: str, invoke): self.provider_name, self.model, self._invoke = provider_name, model, invoke
    def capabilities(self, model: str) -> ModelCapabilities: return ModelCapabilities(structured_output=True, reasoning=True)
    def invoke(self, model: str, request: ModelRequest) -> ModelResponse:
        started = time.monotonic()
        value = self._invoke(request)
        response = value if isinstance(value, ModelResponse) else ModelResponse(self.provider_name, model, structured_output=value)
        return ModelResponse(response.provider, response.model, response.content, response.structured_output, response.usage, round((time.monotonic() - started) * 1000), response.finish_reason)


class OpenAIProvider(_CallableProvider):
    def __init__(self, model: str, invoke): super().__init__("openai", model, invoke)


class AnthropicProvider(_CallableProvider):
    def __init__(self, model: str, invoke): super().__init__("anthropic", model, invoke)
