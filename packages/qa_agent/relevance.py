"""Small deterministic change-to-test relevance contracts for v0.1."""
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class CodeChange:
    path: str
    change_type: str = "modified"


@dataclass(frozen=True)
class RelatedTestCandidate:
    path: str
    score: float
    reason: str


@dataclass(frozen=True)
class RelevanceScore:
    path: str
    confidence: float
    candidates: tuple[RelatedTestCandidate, ...] = ()


def related_tests(change: CodeChange, tests: list[Path]) -> RelevanceScore:
    """v0.1 deterministic 0.5 import + 0.3 symbol + 0.2 filename scoring."""
    stem = Path(change.path).stem.replace("-", "_")
    candidates = []
    for test in tests:
        source = test.read_text(encoding="utf-8", errors="replace")
        reasons, score = [], 0.0
        if re.search(rf"(?:from|import|require).*\b{re.escape(stem)}\b", source): score += 0.5; reasons.append("import")
        if re.search(rf"\b{re.escape(stem)}\b", source): score += 0.3; reasons.append("symbol")
        if stem and stem in test.stem.replace("-", "_"): score += 0.2; reasons.append("filename")
        if score: candidates.append(RelatedTestCandidate(str(test), round(min(score, 1.0), 2), "+".join(reasons)))
    candidates.sort(key=lambda item: (-item.score, item.path))
    # A missing candidate remains an explicitly low-confidence coverage gap.
    return RelevanceScore(change.path, candidates[0].score if candidates else 0.2, tuple(candidates))
