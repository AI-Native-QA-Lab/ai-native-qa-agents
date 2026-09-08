"""Bounded deterministic orchestration for v0.3 test candidates."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .execution import PatchSafetyError, PlaywrightExecutionBackend, PytestExecutionBackend
from .rules import RuleContext, RuleRegistry, RuleRunner
from .runtime import ExecutionBudget, LoopTrace
from .test_engineering import (
    ExecutionResult,
    GeneratedPatch,
    RepairAttempt,
    TestCandidateStatus,
    TestEngineeringResult,
    TestIntent,
    TestPlan,
    TestScenario,
)


class TestGenerator(Protocol):
    def generate(self, plan: TestPlan, previous: GeneratedPatch | None = None) -> GeneratedPatch: ...


class ExecutionBackend(Protocol):
    def execute(self, repository: Path, patch: GeneratedPatch, timeout_seconds: int, test_roots: tuple[str, ...] = ("tests",)) -> ExecutionResult: ...


@dataclass(frozen=True)
class TestEngineeringRequest:
    requirement_id: str
    repository: Path
    requirement_evidence_ids: tuple[str, ...]
    timeout_seconds: int = 60
    max_repairs: int = 0
    test_roots: tuple[str, ...] = ("tests",)
    framework: str = "pytest"


class TestEngineeringService:
    def __init__(self, generator: TestGenerator | None = None, backend: ExecutionBackend | None = None) -> None:
        self.generator = generator
        self.backend = backend

    def run(self, request: TestEngineeringRequest) -> TestEngineeringResult:
        budget = ExecutionBudget(max_iterations=4 + request.max_repairs, timeout_seconds=request.timeout_seconds)
        traces: list[LoopTrace] = []
        if self.generator is None or not request.requirement_evidence_ids:
            return TestEngineeringResult(
                status=TestCandidateStatus("incomplete", "INSUFFICIENT_EVIDENCE", request.requirement_evidence_ids or ("EV-SERVICE-001",)),
                evidence_ids=request.requirement_evidence_ids,
                budget=budget,
            )
        intent = TestIntent("TI-" + request.requirement_id, request.requirement_id, request.requirement_id, request.requirement_evidence_ids)
        scenario = TestScenario(
            "TS-" + request.requirement_id,
            intent.id,
            "generated candidate",
            ("execute candidate",),
            "test passes",
            request.requirement_evidence_ids,
        )
        plan = TestPlan("TP-" + request.requirement_id, intent.id, request.framework, (scenario,), request.requirement_evidence_ids)
        backend = self.backend or _default_backend(request.framework)
        patch = self.generator.generate(plan)
        traces.append(LoopTrace(1, "generate", "completed"))
        gates, failed_gate = _preflight(patch)
        if failed_gate is not None:
            evidence_ids = tuple(dict.fromkeys((*request.requirement_evidence_ids, *patch.evidence_ids, "EV-GATE-PARSE")))
            traces.append(LoopTrace(2, failed_gate, "rejected"))
            return TestEngineeringResult(
                intent=intent,
                plan=plan,
                patch=patch,
                status=TestCandidateStatus("rejected", "INSUFFICIENT_EVIDENCE", evidence_ids),
                gates=gates,
                evidence_ids=evidence_ids,
                loop_trace=traces,
                budget=budget,
            )
        traces.append(LoopTrace(2, "parse", "completed"))
        traces.append(LoopTrace(3, "compile", "completed"))
        try:
            execution = backend.execute(request.repository, patch, request.timeout_seconds, request.test_roots)
        except PatchSafetyError:
            evidence_ids = tuple(dict.fromkeys((*request.requirement_evidence_ids, *patch.evidence_ids, "EV-GATE-PATCH")))
            traces.append(LoopTrace(4, "patch-safety", "rejected"))
            return TestEngineeringResult(
                intent=intent,
                plan=plan,
                patch=patch,
                status=TestCandidateStatus("rejected", "INSUFFICIENT_EVIDENCE", evidence_ids),
                gates={**gates, "patch-safety": "rejected"},
                evidence_ids=evidence_ids,
                loop_trace=traces,
                budget=budget,
            )
        traces.append(LoopTrace(4, "execute", "completed" if execution.passed else "failed"))
        repairs: list[RepairAttempt] = []
        for number in range(1, request.max_repairs + 1):
            if execution.passed or execution.termination_reason != "EVIDENCE_SUFFICIENT":
                break
            traces.append(LoopTrace(4 + number, "analyze_failure", "completed"))
            repairs.append(RepairAttempt(number, patch.id, _failure_reason(execution), execution.evidence_ids))
            patch = self.generator.generate(plan, patch)
            traces.append(LoopTrace(4 + number, "repair", "completed"))
            gates, failed_gate = _preflight(patch)
            if failed_gate is not None:
                evidence_ids = tuple(dict.fromkeys((*request.requirement_evidence_ids, *patch.evidence_ids, *execution.evidence_ids, "EV-GATE-PARSE")))
                traces.append(LoopTrace(5 + number, failed_gate, "rejected"))
                return TestEngineeringResult(
                    intent=intent,
                    plan=plan,
                    patch=patch,
                    execution=execution,
                    repairs=repairs,
                    status=TestCandidateStatus("rejected", "INSUFFICIENT_EVIDENCE", evidence_ids),
                    gates=gates,
                    evidence_ids=evidence_ids,
                    loop_trace=traces,
                    budget=budget,
                )
            execution = backend.execute(request.repository, patch, request.timeout_seconds, request.test_roots)
            traces.append(LoopTrace(5 + number, "execute", "completed" if execution.passed else "failed"))
        evidence_ids = tuple(dict.fromkeys((*request.requirement_evidence_ids, *patch.evidence_ids, *execution.evidence_ids)))
        gates["execution"] = "passed" if execution.passed else "rejected"
        if not execution.passed:
            exhausted = execution.termination_reason == "EVIDENCE_SUFFICIENT" and request.max_repairs > 0 and len(repairs) == request.max_repairs
            status = TestCandidateStatus(
                "incomplete" if exhausted else "rejected",
                "BUDGET_EXHAUSTED" if exhausted else execution.termination_reason,
                evidence_ids,
            )
            return TestEngineeringResult(
                intent=intent,
                plan=plan,
                patch=patch,
                execution=execution,
                repairs=repairs,
                status=status,
                gates=gates,
                evidence_ids=evidence_ids,
                loop_trace=traces,
                budget=budget,
            )
        review_findings = _review_patch(patch)
        gates["assertion"] = "passed"
        gates["reviewer"] = "passed" if not review_findings else "rejected"
        traces.append(LoopTrace(len(traces) + 1, "review", "completed" if not review_findings else "rejected"))
        if review_findings:
            evidence_ids = tuple(dict.fromkeys((*evidence_ids, "EV-GATE-REVIEW")))
            return TestEngineeringResult(
                intent=intent,
                plan=plan,
                patch=patch,
                execution=execution,
                repairs=repairs,
                status=TestCandidateStatus("rejected", "INSUFFICIENT_EVIDENCE", evidence_ids),
                gates=gates,
                evidence_ids=evidence_ids,
                loop_trace=traces,
                budget=budget,
            )
        return TestEngineeringResult(
            intent=intent,
            plan=plan,
            patch=patch,
            execution=execution,
            repairs=repairs,
            status=TestCandidateStatus("accepted", "EVIDENCE_SUFFICIENT", evidence_ids),
            gates=gates,
            evidence_ids=evidence_ids,
            loop_trace=traces,
            budget=budget,
        )


def _default_backend(framework: str) -> ExecutionBackend:
    if framework == "playwright":
        return PlaywrightExecutionBackend()
    return PytestExecutionBackend()


def _failure_reason(execution: ExecutionResult) -> str:
    if execution.exit_code is None:
        return f"execution terminated: {execution.termination_reason}"
    return f"execution failed with exit code {execution.exit_code}"


def _review_patch(patch: GeneratedPatch) -> list[str]:
    runner = RuleRunner(RuleRegistry.default())
    findings: list[str] = []
    for file in patch.files:
        has_assert = bool(ast.parse(file.content).body) and ("assert " in file.content or "expect(" in file.content)
        language = "python" if file.path.endswith(".py") else "typescript"
        framework = "pytest" if language == "python" else "Playwright"
        matches = runner.run(RuleContext(file.path, file.content, language, framework, assertion=has_assert))
        findings.extend(match.rule_id for match in matches if match.severity in {"critical", "high"})
    return findings


def _preflight(patch: GeneratedPatch) -> tuple[dict[str, str], str | None]:
    gates = {"parse": "passed", "compile": "passed", "assertion": "passed", "reviewer": "passed"}
    for file in patch.files:
        try:
            tree = ast.parse(file.content, filename=file.path)
        except SyntaxError:
            gates["parse"] = "rejected"
            return gates, "parse"
        try:
            compile(tree, file.path, "exec")
        except ValueError:
            gates["compile"] = "rejected"
            return gates, "compile"
        assertions = [node for node in ast.walk(tree) if isinstance(node, ast.Assert)]
        if not assertions or any(isinstance(node.test, ast.Constant) and isinstance(node.test.value, bool) for node in assertions):
            gates["assertion"] = gates["reviewer"] = "rejected"
            return gates, "assertion"
    return gates, None
