"""Versioned v0.2 Requirement Intelligence contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .review import Evidence, GateResult
from .runtime import ExecutionBudget, LoopTrace


def _required(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} is required")


@dataclass(frozen=True)
class AcceptanceCriterion:
    id: str
    text: str
    line: int
    parse_status: str = "parsed"

    def __post_init__(self) -> None:
        _required(self.id, "acceptance criterion id")
        _required(self.text, "acceptance criterion text")
        if self.line < 1:
            raise ValueError("acceptance criterion line must be positive")


@dataclass(frozen=True)
class Requirement:
    id: str
    title: str
    body: str
    source_kind: str
    source_ref: str
    acceptance_criteria: tuple[AcceptanceCriterion, ...] = ()

    def __post_init__(self) -> None:
        for value, name in ((self.id, "requirement id"), (self.title, "requirement title"), (self.source_kind, "source kind"), (self.source_ref, "source reference")):
            _required(value, name)


@dataclass(frozen=True)
class TestabilityFinding:
    id: str
    category: str
    severity: str
    message: str
    criterion_id: str | None
    evidence_ids: tuple[str, ...]
    verification_status: str = "verified"
    confidence: float = 1.0

    def __post_init__(self) -> None:
        _required(self.id, "finding id")
        _required(self.category, "finding category")
        if self.severity not in {"critical", "high", "medium", "low"}:
            raise ValueError("invalid finding severity")
        _required(self.message, "finding message")
        if not self.evidence_ids:
            raise ValueError("finding evidence is required")


@dataclass(frozen=True)
class RiskItem:
    id: str
    category: str
    severity: str
    message: str
    criterion_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    verification_status: str = "verified"
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if self.severity not in {"critical", "high", "medium", "low"}:
            raise ValueError("invalid risk severity")
        if not self.evidence_ids:
            raise ValueError("risk evidence is required")


@dataclass(frozen=True)
class TraceLink:
    requirement_id: str
    target_kind: str
    target_path: str
    target_symbol: str
    evidence_ids: tuple[str, ...]
    status: str
    confidence: float

    def __post_init__(self) -> None:
        _required(self.requirement_id, "requirement id")
        if self.target_kind not in {"code", "test"}:
            raise ValueError("invalid trace link target kind")
        _required(self.target_path, "trace link target path")
        if not self.evidence_ids:
            raise ValueError("trace link evidence is required")
        if self.status not in {"verified", "unverified"}:
            raise ValueError("invalid trace link status")
        if not 0 <= self.confidence <= 1:
            raise ValueError("trace link confidence must be between 0 and 1")


@dataclass
class RequirementResult:
    requirement: Requirement | None = None
    findings: list[TestabilityFinding] = field(default_factory=list)
    risks: list[RiskItem] = field(default_factory=list)
    trace_links: list[TraceLink] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    decision: str = "incomplete"
    termination_reason: str = "INSUFFICIENT_EVIDENCE"
    gate: GateResult | None = None
    loop_trace: list[LoopTrace] = field(default_factory=list)
    budget: ExecutionBudget = field(default_factory=ExecutionBudget)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "v0.2",
            "requirement": asdict(self.requirement) if self.requirement else None,
            "findings": [asdict(item) for item in self.findings],
            "risks": [asdict(item) for item in self.risks],
            "trace_links": [asdict(item) for item in self.trace_links],
            "evidence": [asdict(item) for item in self.evidence],
            "decision": self.decision,
            "termination_reason": self.termination_reason,
            "gate": asdict(self.gate) if self.gate else None,
            "loop_trace": [asdict(item) for item in self.loop_trace],
            "budget": asdict(self.budget),
        }
