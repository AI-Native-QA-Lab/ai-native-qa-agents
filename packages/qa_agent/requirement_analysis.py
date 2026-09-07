"""Deterministic, bounded Requirement Intelligence analysis."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re

from .requirement_adapters import RequirementSource
from .requirements import AcceptanceCriterion, Requirement, RequirementResult, RiskItem, TestabilityFinding
from .review import Evidence, GateResult
from .runtime import ExecutionBudget, LoopTrace

AMBIGUOUS = re.compile(r"\b(fast|easy|robust|user-friendly|appropriate)\b", re.I)
OBSERVABLE = re.compile(r"\b(display|return|reject|redirect|status|within\s+\d+|must not|can)\b", re.I)
ERROR = re.compile(r"\b(error|fail|declin|invalid|denied|timeout)\b", re.I)


@dataclass(frozen=True)
class RequirementRequest:
    source: RequirementSource
    max_actions: int = 6
    max_file_bytes: int = 1_000_000


class RequirementAnalysisService:
    def analyze(self, request: RequirementRequest) -> RequirementResult:
        budget = ExecutionBudget(max_iterations=request.max_actions)
        requirement = Requirement(request.source.id, request.source.title, request.source.body, request.source.source_kind, request.source.source_ref, tuple(AcceptanceCriterion(f"{request.source.id}-AC-{index}", text, line) for index, (line, text) in enumerate(request.source.criterion_lines, 1)))
        result = RequirementResult(requirement=requirement, budget=budget)
        if request.max_actions < 4:
            result.termination_reason = "BUDGET_EXHAUSTED"
            return result
        for iteration, criterion in enumerate(requirement.acceptance_criteria, 1):
            evidence = Evidence(f"EV-REQ-{iteration:03d}", "acceptance_criteria", requirement.source_ref, criterion.line, criterion.line, "sha256:" + hashlib.sha256(criterion.text.encode()).hexdigest(), loop_iteration=iteration)
            result.evidence.append(evidence)
            if AMBIGUOUS.search(criterion.text):
                result.findings.append(TestabilityFinding(f"F-{len(result.findings)+1:03d}", "ambiguous", "medium", "Criterion uses subjective language", criterion.id, (evidence.id,)))
            if not OBSERVABLE.search(criterion.text):
                result.findings.append(TestabilityFinding(f"F-{len(result.findings)+1:03d}", "unverifiable", "medium", "Criterion has no observable outcome", criterion.id, (evidence.id,)))
        body = " ".join(item.text for item in requirement.acceptance_criteria)
        if not ERROR.search(body):
            evidence = result.evidence[0] if result.evidence else Evidence("EV-REQ-001", "requirement", requirement.source_ref, 1, 1, "sha256:" + hashlib.sha256(requirement.title.encode()).hexdigest())
            if not result.evidence:
                result.evidence.append(evidence)
            result.findings.append(TestabilityFinding(f"F-{len(result.findings)+1:03d}", "missing_error_path", "medium", "Requirement lacks an error path", None, (evidence.id,)))
            result.risks.append(RiskItem("R-001", "missing_error_path", "medium", "Error behavior is unspecified", (), (evidence.id,)))
        result.decision = "fail" if any(item.severity == "critical" for item in result.findings) else "warn" if result.findings else "pass"
        result.termination_reason = "EVIDENCE_SUFFICIENT"
        result.gate = GateResult(result.decision, ["critical"], len(result.findings), 1.0, "medium" if result.findings else "low")
        result.loop_trace = [LoopTrace(index, action, "completed") for index, action in enumerate(("parse-requirement", "analyze-testability", "analyze-risk", "verify-and-gate"), 1)]
        return result
