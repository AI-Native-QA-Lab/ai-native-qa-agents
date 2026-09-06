"""Bounded, redacted semantic-review context construction."""
import re
from .semantic import SemanticReviewRequest

def build_semantic_context(test_source: str, rule_signals: list[str], diff_context: str = "", nearby_production_symbol: str = "") -> SemanticReviewRequest:
    redact = lambda value: re.sub(r"(?i)(bearer\s+|api[_-]?key\s*[:=]\s*|password\s*[:=]\s*)([^\s,'\"]+)", r"\1[REDACTED]", value)[:20_000]
    return SemanticReviewRequest(redact(test_source), tuple(rule_signals), redact(diff_context), redact(nearby_production_symbol))
