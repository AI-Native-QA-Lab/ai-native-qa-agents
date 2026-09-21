"""Versioned v0.3 AI Test Engineer contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .runtime import ExecutionBudget, LoopTrace, budget_to_dict, loop_trace_to_dict


def _required(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} is required")


@dataclass(frozen=True)
class TestIntent:
    id: str
    requirement_id: str
    subject: str
    evidence_ids: tuple[str, ...]
    acceptance_criterion_ids: tuple[str, ...] = ()
    risk_ids: tuple[str, ...] = ()
    observable_behavior: str | None = None
    business_oracle: str | None = None

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
    business_oracle: str | None = None
    acceptance_criterion_ids: tuple[str, ...] = ()
    test_ids: tuple[str, ...] = ()

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
    gates: dict[str, str] = field(default_factory=dict)
    evidence_ids: tuple[str, ...] = ()
    loop_trace: list[LoopTrace] = field(default_factory=list)
    budget: ExecutionBudget = field(default_factory=ExecutionBudget)

    def to_dict(self, *, include_v04: bool = False) -> dict[str, Any]:
        return {
            "schema_version": "v0.3",
            "intent": _intent_to_dict(self.intent, include_v04=include_v04) if self.intent else None,
            "plan": _plan_to_dict(self.plan, include_v04=include_v04) if self.plan else None,
            "patch": asdict(self.patch) if self.patch else None,
            "execution": asdict(self.execution) if self.execution else None,
            "repairs": [asdict(item) for item in self.repairs],
            "status": asdict(self.status) if self.status else None,
            "gates": self.gates,
            "evidence_ids": list(self.evidence_ids),
            "loop_trace": [loop_trace_to_dict(item) for item in self.loop_trace],
            "budget": budget_to_dict(self.budget),
        }


def _intent_to_dict(intent: TestIntent, *, include_v04: bool) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": intent.id,
        "requirement_id": intent.requirement_id,
        "subject": intent.subject,
        "evidence_ids": list(intent.evidence_ids),
    }
    extensions = {
        "acceptance_criterion_ids": list(intent.acceptance_criterion_ids),
        "risk_ids": list(intent.risk_ids),
        "observable_behavior": intent.observable_behavior,
        "business_oracle": intent.business_oracle,
    }
    if include_v04 or any(value not in (None, []) for value in extensions.values()):
        payload.update(extensions)
    return payload


def _scenario_to_dict(scenario: TestScenario, *, include_v04: bool) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": scenario.id,
        "intent_id": scenario.intent_id,
        "name": scenario.name,
        "steps": list(scenario.steps),
        "expected_outcome": scenario.expected_outcome,
        "evidence_ids": list(scenario.evidence_ids),
    }
    extensions = {
        "business_oracle": scenario.business_oracle,
        "acceptance_criterion_ids": list(scenario.acceptance_criterion_ids),
        "test_ids": list(scenario.test_ids),
    }
    if include_v04 or any(value not in (None, []) for value in extensions.values()):
        payload.update(extensions)
    return payload


def _plan_to_dict(plan: TestPlan, *, include_v04: bool) -> dict[str, Any]:
    return {
        "id": plan.id,
        "intent_id": plan.intent_id,
        "framework": plan.framework,
        "scenarios": [_scenario_to_dict(item, include_v04=include_v04) for item in plan.scenarios],
        "evidence_ids": list(plan.evidence_ids),
    }
