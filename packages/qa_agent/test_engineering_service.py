"""Bounded deterministic orchestration for v0.3 test candidates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .execution import PytestExecutionBackend
from .runtime import ExecutionBudget, LoopTrace
from .test_engineering import GeneratedPatch, RepairAttempt, TestCandidateStatus, TestEngineeringResult, TestIntent, TestPlan, TestScenario


class TestGenerator(Protocol):
    def generate(self, plan: TestPlan, previous: GeneratedPatch | None = None) -> GeneratedPatch: ...


@dataclass(frozen=True)
class TestEngineeringRequest:
    requirement_id: str
    repository: Path
    requirement_evidence_ids: tuple[str, ...]
    timeout_seconds: int = 60
    max_repairs: int = 0
    test_roots: tuple[str, ...] = ("tests",)


class TestEngineeringService:
    def __init__(self, generator: TestGenerator | None = None, backend: PytestExecutionBackend | None = None) -> None:
        self.generator = generator
        self.backend = backend or PytestExecutionBackend()

    def run(self, request: TestEngineeringRequest) -> TestEngineeringResult:
        budget = ExecutionBudget(max_iterations=4 + request.max_repairs, timeout_seconds=request.timeout_seconds)
        if self.generator is None or not request.requirement_evidence_ids:
            return TestEngineeringResult(status=TestCandidateStatus("incomplete", "INSUFFICIENT_EVIDENCE", request.requirement_evidence_ids or ("EV-SERVICE-001",)), evidence_ids=request.requirement_evidence_ids, budget=budget)
        intent = TestIntent("TI-" + request.requirement_id, request.requirement_id, request.requirement_id, request.requirement_evidence_ids)
        scenario = TestScenario("TS-" + request.requirement_id, intent.id, "generated candidate", ("execute candidate",), "test passes", request.requirement_evidence_ids)
        plan = TestPlan("TP-" + request.requirement_id, intent.id, "pytest", (scenario,), request.requirement_evidence_ids)
        patch = self.generator.generate(plan)
        execution = self.backend.execute(request.repository, patch, request.timeout_seconds, request.test_roots)
        repairs: list[RepairAttempt] = []
        for number in range(1, request.max_repairs + 1):
            if execution.passed:
                break
            repairs.append(RepairAttempt(number, patch.id, "execution failed", execution.evidence_ids))
            patch = self.generator.generate(plan, patch)
            execution = self.backend.execute(request.repository, patch, request.timeout_seconds, request.test_roots)
        evidence_ids = tuple(dict.fromkeys((*request.requirement_evidence_ids, *patch.evidence_ids, *execution.evidence_ids)))
        exhausted = not execution.passed and request.max_repairs > 0
        status = TestCandidateStatus("accepted" if execution.passed else "incomplete" if exhausted else "rejected", "EVIDENCE_SUFFICIENT" if execution.passed else "BUDGET_EXHAUSTED" if exhausted else execution.termination_reason, evidence_ids)
        return TestEngineeringResult(intent=intent, plan=plan, patch=patch, execution=execution, repairs=repairs, status=status, evidence_ids=evidence_ids, loop_trace=[LoopTrace(1, "generate", "completed"), LoopTrace(2, "execute", "completed"), LoopTrace(3, "review", "completed")], budget=budget)
