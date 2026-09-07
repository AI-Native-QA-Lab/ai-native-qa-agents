from qa_agent.requirement_adapters import RequirementSource


def test_analysis_emits_evidenced_requirement_findings() -> None:
    from qa_agent.requirement_analysis import RequirementAnalysisService, RequirementRequest

    source = RequirementSource("REQ-1", "Checkout", "", "markdown", "req.md", ((2, "Fast checkout"), (3, "System handles errors")))
    result = RequirementAnalysisService().analyze(RequirementRequest(source))

    assert {item.category for item in result.findings} >= {"ambiguous", "unverifiable", "missing_error_path"}
    assert all(item.evidence_ids for item in result.findings)


def test_analysis_stops_when_budget_exhausted() -> None:
    from qa_agent.requirement_analysis import RequirementAnalysisService, RequirementRequest

    result = RequirementAnalysisService().analyze(RequirementRequest(RequirementSource("REQ-1", "Checkout", "", "markdown", "req.md"), max_actions=1))

    assert (result.decision, result.termination_reason) == ("incomplete", "BUDGET_EXHAUSTED")
