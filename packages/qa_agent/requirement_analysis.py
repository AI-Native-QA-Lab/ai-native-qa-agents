"""Deterministic, bounded Requirement Intelligence analysis."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re

from .requirement_adapters import RequirementSource
from .requirements import AcceptanceCriterion, Requirement, RequirementResult, RiskItem, TestabilityFinding
from .review import Evidence, GateResult
from .runtime import ExecutionBudget, LoopTrace
from .review import ReviewRequest, ReviewService

AMBIGUOUS = re.compile(r"\b(fast|easy|robust|user-friendly|appropriate)\b", re.I)
OBSERVABLE = re.compile(r"\b(display|return|reject|redirect|status|within\s+\d+|must not|can)\b", re.I)
ERROR = re.compile(r"\b(error|fail|declin|invalid|denied|timeout)\b", re.I)
_REQUIRED_ACTION = re.compile(r"\bmust\s+(not\s+)?(.+?)\s*[.!]?$", re.I)


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
        actions: dict[str, tuple[AcceptanceCriterion, Evidence]] = {}
        for criterion, evidence in zip(requirement.acceptance_criteria, result.evidence):
            match = _REQUIRED_ACTION.search(criterion.text)
            if match is None:
                continue
            action = match.group(2).casefold()
            if match.group(1):
                positive = actions.get(action)
                if positive is not None:
                    evidence_ids = (positive[1].id, evidence.id)
                    result.findings.append(TestabilityFinding(f"F-{len(result.findings)+1:03d}", "conflicting_criteria", "high", "Criteria require both an action and its negation", criterion.id, evidence_ids))
                    result.risks.append(RiskItem(f"R-{len(result.risks)+1:03d}", "conflicting_criteria", "high", "Conflicting acceptance criteria prevent a deterministic test outcome", (positive[0].id, criterion.id), evidence_ids))
            else:
                actions[action] = (criterion, evidence)
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

    def review_pr(self, requirement: Requirement, requirement_evidence: list[Evidence], repository, base: str | None = None) -> RequirementResult:
        if not requirement_evidence:
            return RequirementResult(requirement=requirement)
        review = ReviewService().review(ReviewRequest(repository, base=base))
        if review.decision == "incomplete":
            return RequirementResult(requirement=requirement, evidence=requirement_evidence, decision="incomplete", termination_reason=review.termination_reason)
        result = RequirementResult(requirement=requirement, evidence=[*requirement_evidence, *review.evidence], decision=review.decision, termination_reason=review.termination_reason)
        result.findings = [TestabilityFinding(item.id, item.rule_id, item.severity, item.message, None, tuple(item.evidence_ids), item.verification_status, item.confidence) for item in review.findings]
        return result
