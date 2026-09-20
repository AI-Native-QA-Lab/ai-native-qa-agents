"""Serializable runtime contracts shared by legacy and v0.4 services."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ExecutionBudget:
    max_iterations: int = 6
    max_tool_calls: int = 32
    max_model_calls: int = 0
    timeout_seconds: int = 60
    max_replans: int | None = None
    max_mutants: int | None = None
    max_report_bytes: int | None = None
    max_context_bytes: int | None = None

    @classmethod
    def v04_defaults(cls) -> "ExecutionBudget":
        return cls(8, 8, 1, 120, 1, 500, 2_000_000, 1_000_000)

    def validate(self, v04: bool = False) -> None:
        if not v04:
            return
        values = (
            self.max_iterations,
            self.max_tool_calls,
            self.max_model_calls,
            self.timeout_seconds,
            self.max_replans,
            self.max_mutants,
            self.max_report_bytes,
            self.max_context_bytes,
        )
        if any(not isinstance(value, int) or isinstance(value, bool) for value in values):
            raise ValueError("v0.4 budget values must be integers")
        if any(value < 0 for value in values):
            raise ValueError("v0.4 budget counters cannot be negative")
        if self.timeout_seconds <= 0 or self.max_report_bytes <= 0 or self.max_context_bytes <= 0:
            raise ValueError("v0.4 timeout and byte limits must be positive")


def budget_to_dict(budget: ExecutionBudget, *, include_v04: bool = False) -> dict[str, int]:
    payload = {
        "max_iterations": budget.max_iterations,
        "max_tool_calls": budget.max_tool_calls,
        "max_model_calls": budget.max_model_calls,
        "timeout_seconds": budget.timeout_seconds,
    }
    extensions = {
        "max_replans": budget.max_replans,
        "max_mutants": budget.max_mutants,
        "max_report_bytes": budget.max_report_bytes,
        "max_context_bytes": budget.max_context_bytes,
    }
    if include_v04 or any(value is not None for value in extensions.values()):
        payload.update(extensions)
    return payload  # type: ignore[return-value]


V04_ACTIONS = {
    "READ",
    "EXECUTE_MUTATION",
    "MODEL_SURVIVOR_MAPPING",
    "WRITE",
    "COMMIT",
    "MERGE",
    "RELEASE",
}


@dataclass(frozen=True)
class PermissionContext:
    repository: Path
    controlled_copy: Path | None
    allowed_actions: tuple[str, ...]
    approval_required_actions: tuple[str, ...]
    max_command_args: int
    max_file_bytes: int

    def __post_init__(self) -> None:
        actions = set(self.allowed_actions) | set(self.approval_required_actions)
        if not actions <= V04_ACTIONS:
            raise ValueError("invalid permission action")
        if self.max_command_args <= 0 or self.max_file_bytes <= 0:
            raise ValueError("permission limits must be positive")


@dataclass(frozen=True)
class PermissionResult:
    action: str
    allowed: bool
    reason: str
    evidence_id: str | None
    external_command_executed: bool

    def __post_init__(self) -> None:
        if self.action not in V04_ACTIONS:
            raise ValueError("invalid permission action")
        if not self.reason.strip():
            raise ValueError("permission reason is required")


@dataclass
class Observation:
    id: str
    action_id: str
    summary: str
    evidence_ids: list[str] = field(default_factory=list)
    structured_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class LoopTrace:
    iteration: int
    action_id: str
    status: str
    observation_id: str | None = None
    assessment_id: str | None = None
    phase: str | None = None
    permission_evidence_id: str | None = None
    evidence_ids: list[str] = field(default_factory=list)
    termination_reason: str | None = None


def loop_trace_to_dict(trace: LoopTrace, *, include_v04: bool = False) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "iteration": trace.iteration,
        "action_id": trace.action_id,
        "status": trace.status,
        "observation_id": trace.observation_id,
    }
    extensions = {
        "assessment_id": trace.assessment_id,
        "phase": trace.phase,
        "permission_evidence_id": trace.permission_evidence_id,
        "evidence_ids": list(trace.evidence_ids),
        "termination_reason": trace.termination_reason,
    }
    if include_v04 or any(value not in (None, []) for value in extensions.values()):
        payload.update(extensions)
    return payload


@dataclass
class AgentState:
    task_id: str
    goal: str
    status: str = "RUNNING"
    iteration: int = 0
    observations: list[Observation] = field(default_factory=list)
    traces: list[LoopTrace] = field(default_factory=list)
    plan: list[str] = field(default_factory=list)
    completed_actions: list[str] = field(default_factory=list)
    pending_actions: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    finding_ids: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    confidence: float | None = None
    budget: ExecutionBudget | None = None
    termination_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "goal": self.goal,
            "status": self.status,
            "iteration": self.iteration,
            "plan": self.plan,
            "completed_actions": self.completed_actions,
            "pending_actions": self.pending_actions,
            "observations": [observation.__dict__ for observation in self.observations],
            "evidence_ids": self.evidence_ids,
            "finding_ids": self.finding_ids,
            "open_questions": self.open_questions,
            "confidence": self.confidence,
            "budget": budget_to_dict(self.budget) if self.budget else None,
            "termination_reason": self.termination_reason,
        }


class TerminationPolicy:
    def evaluate(
        self,
        *,
        budget: ExecutionBudget,
        iteration: int,
        tool_calls: int,
        model_calls: int,
        replans: int,
        elapsed_seconds: float,
        permission: PermissionResult | None,
        process_observation_complete: bool,
        evidence_sufficient: bool,
    ) -> str | None:
        budget.validate(v04=True)
        if permission is not None and not permission.allowed:
            if "approval" in permission.reason.lower():
                return "HUMAN_APPROVAL_REQUIRED"
            return "INSUFFICIENT_EVIDENCE"
        if elapsed_seconds >= budget.timeout_seconds:
            return "TIMEOUT"
        if (
            iteration >= budget.max_iterations
            or tool_calls >= budget.max_tool_calls
            or model_calls >= budget.max_model_calls
            or replans >= budget.max_replans
        ):
            return "BUDGET_EXHAUSTED"
        if not process_observation_complete or not evidence_sufficient:
            return "INSUFFICIENT_EVIDENCE"
        return None

    def should_stop(self, state: AgentState, budget: ExecutionBudget) -> str | None:
        if state.iteration > budget.max_iterations:
            return "BUDGET_EXHAUSTED"
        return None
