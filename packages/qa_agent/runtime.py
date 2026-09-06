"""Serializable v0.1 runtime contracts used by the bounded review service."""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExecutionBudget:
    max_iterations: int = 6
    max_tool_calls: int = 32
    max_model_calls: int = 0
    timeout_seconds: int = 60


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
            "budget": self.budget.__dict__ if self.budget else None,
            "termination_reason": self.termination_reason,
        }


class TerminationPolicy:
    def should_stop(self, state: AgentState, budget: ExecutionBudget) -> str | None:
        if state.iteration > budget.max_iterations:
            return "BUDGET_EXHAUSTED"
        return None
