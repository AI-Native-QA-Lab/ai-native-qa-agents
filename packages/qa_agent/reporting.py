from .review import ReviewResult
from .requirements import RequirementResult

def render_human(result: ReviewResult) -> str:
    risk = "high" if result.decision == "fail" else "unknown" if result.decision == "incomplete" else "low"
    lines = [f"Summary: {result.decision}", f"Risk: {risk}", f"Changed Files: {len(result.changes)}", f"Coverage Gaps: {len(result.coverage_gaps)}", f"Findings: {len(result.findings)}", f"Evidence: {len(result.evidence)}", "Recommendation: resolve blocking findings before merge."]
    return "\n".join(lines)


def render_requirement_human(result: RequirementResult) -> str:
    return "\n".join((
        f"Decision: {result.decision}",
        f"Termination: {result.termination_reason}",
        f"Findings: {len(result.findings)}",
        f"Trace links: {len(result.trace_links)}",
        f"Evidence: {len(result.evidence)}",
    ))
