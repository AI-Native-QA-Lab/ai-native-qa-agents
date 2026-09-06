"""Optional semantic-review boundary; providers are deliberately opt-in."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from .model_runtime import ModelRequest, ModelUsageTracker, StructuredOutputValidator


@dataclass(frozen=True)
class SemanticReviewRequest:
    test_source: str
    rule_signals: tuple[str, ...]
    diff_context: str = ""
    nearby_production_symbol: str = ""


@dataclass(frozen=True)
class SemanticReviewResult:
    intent: str
    oracle_quality: str
    confidence: float
    verification_status: str = "unverified"
    issues: tuple[str, ...] = ()


class ModelProvider(Protocol):
    name: str

    def structured_review(self, request: SemanticReviewRequest) -> SemanticReviewResult: ...


class SemanticReviewer:
    """Requires an explicit provider; repository content is data, never instruction."""

    def __init__(self, provider: ModelProvider | None = None) -> None:
        self.provider = provider
        self.usage = ModelUsageTracker()

    def review(self, request: SemanticReviewRequest) -> SemanticReviewResult | None:
        if self.provider is None:
            return None
        if hasattr(self.provider, "structured_review"):
            return self.provider.structured_review(request)
        content = "\n".join((
            "TEST SOURCE:\n" + request.test_source,
            "RULE SIGNALS:\n" + ", ".join(request.rule_signals),
            "DIFF CONTEXT:\n" + request.diff_context,
            "NEARBY PRODUCTION SYMBOL:\n" + request.nearby_production_symbol,
        ))
        model_request = ModelRequest("semantic_test_review", ({"role": "user", "content": content},), {"type": "object"}, ("structured_output",))
        response = StructuredOutputValidator().validate(model_request, self.provider.invoke(getattr(self.provider, "model", "default"), model_request))
        self.usage.record(response)
        payload = response.structured_output or {}
        return SemanticReviewResult(str(payload.get("intent", "unknown")), str(payload.get("oracle_quality", "unknown")), float(payload.get("confidence", 0.0)), issues=tuple(payload.get("issues", ())))
