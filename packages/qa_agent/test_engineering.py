"""Versioned v0.3 AI Test Engineer contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .runtime import ExecutionBudget, LoopTrace


def _required(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} is required")


@dataclass(frozen=True)
class TestIntent:
    id: str
    requirement_id: str
    subject: str
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        for value, name in ((self.id, "test intent id"), (self.requirement_id, "requirement id"), (self.subject, "test subject")):
            _required(value, name)
        if not self.evidence_ids:
            raise ValueError("test intent evidence is required")


@dataclass(frozen=True)
class TestScenario:
    id: str
    intent_id: str
    name: str
    steps: tuple[str, ...]
    expected_outcome: str
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        for value, name in ((self.id, "scenario id"), (self.intent_id, "intent id"), (self.name, "scenario name"), (self.expected_outcome, "expected outcome")):
            _required(value, name)
        if not self.steps or not self.evidence_ids:
            raise ValueError("scenario steps and evidence are required")


@dataclass(frozen=True)
class TestPlan:
    id: str
    intent_id: str
    framework: str
    scenarios: tuple[TestScenario, ...]
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _required(self.id, "test plan id")
        _required(self.intent_id, "intent id")
        if self.framework not in {"pytest", "playwright"}:
            raise ValueError("unsupported test framework")
        if not self.scenarios or not self.evidence_ids:
            raise ValueError("test plan scenarios and evidence are required")


@dataclass(frozen=True)
class PatchFile:
    path: str
    content: str

    def __post_init__(self) -> None:
        _required(self.path, "patch path")
        _required(self.content, "patch content")


@dataclass(frozen=True)
class GeneratedPatch:
    id: str
    files: tuple[PatchFile, ...]
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _required(self.id, "generated patch id")
        if not self.files or not self.evidence_ids:
            raise ValueError("patch files and evidence are required")


@dataclass(frozen=True)
class ExecutionResult:
    framework: str
    command: tuple[str, ...]
    exit_code: int | None
    passed: bool
    termination_reason: str
    stdout_hash: str | None
    stderr_hash: str | None
    duration_ms: int
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.framework not in {"pytest", "playwright"}:
            raise ValueError("unsupported execution framework")
        if self.termination_reason not in {"EVIDENCE_SUFFICIENT", "INSUFFICIENT_EVIDENCE", "TIMEOUT", "ERROR"}:
            raise ValueError("invalid execution termination reason")
        if self.duration_ms < 0 or not self.evidence_ids:
            raise ValueError("execution duration and evidence are required")


@dataclass(frozen=True)
class RepairAttempt:
    number: int
    patch_id: str
    reason: str
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.number < 1:
            raise ValueError("repair attempt number must be positive")
        _required(self.patch_id, "patch id")
        _required(self.reason, "repair reason")
        if not self.evidence_ids:
            raise ValueError("repair evidence is required")


@dataclass(frozen=True)
class TestCandidateStatus:
    decision: str
    termination_reason: str
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.decision not in {"accepted", "rejected", "incomplete"}:
            raise ValueError("invalid test candidate decision")
        if self.termination_reason not in {"EVIDENCE_SUFFICIENT", "INSUFFICIENT_EVIDENCE", "BUDGET_EXHAUSTED", "TIMEOUT", "ERROR"}:
            raise ValueError("invalid test candidate termination reason")
        if not self.evidence_ids:
            raise ValueError("test candidate evidence is required")


@dataclass
class TestEngineeringResult:
    intent: TestIntent | None = None
    plan: TestPlan | None = None
    patch: GeneratedPatch | None = None
    execution: ExecutionResult | None = None
    repairs: list[RepairAttempt] = field(default_factory=list)
    status: TestCandidateStatus | None = None
    evidence_ids: tuple[str, ...] = ()
    loop_trace: list[LoopTrace] = field(default_factory=list)
    budget: ExecutionBudget = field(default_factory=ExecutionBudget)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "v0.3",
            "intent": asdict(self.intent) if self.intent else None,
            "plan": asdict(self.plan) if self.plan else None,
            "patch": asdict(self.patch) if self.patch else None,
            "execution": asdict(self.execution) if self.execution else None,
            "repairs": [asdict(item) for item in self.repairs],
            "status": asdict(self.status) if self.status else None,
            "evidence_ids": list(self.evidence_ids),
            "loop_trace": [asdict(item) for item in self.loop_trace],
            "budget": asdict(self.budget),
        }
