from qa_agent.requirement_adapters import RequirementSource


def test_analysis_emits_evidenced_requirement_findings() -> None:
    from qa_agent.requirement_analysis import RequirementAnalysisService, RequirementRequest

    source = RequirementSource("REQ-1", "Checkout", "", "markdown", "req.md", ((2, "Fast checkout"), (3, "System handles errors")))
    result = RequirementAnalysisService().analyze(RequirementRequest(source))

    assert {item.category for item in result.findings} >= {"ambiguous", "unverifiable", "missing_error_path"}
    assert all(item.evidence_ids for item in result.findings)
    assert result.context is not None
    assert result.context.evidence_ids == tuple(item.id for item in result.evidence)


def test_analysis_reports_evidenced_conflicting_criteria() -> None:
    from qa_agent.requirement_analysis import RequirementAnalysisService, RequirementRequest

    source = RequirementSource(
        "REQ-1",
        "Orders",
        "",
        "markdown",
        "req.md",
        ((2, "User must save the order"), (3, "User must not save the order")),
    )

    result = RequirementAnalysisService().analyze(RequirementRequest(source))

    assert any(item.category == "conflicting_criteria" for item in result.findings)
    assert all(item.evidence_ids for item in result.findings)


def test_analysis_reports_conflicts_when_negated_criterion_comes_first() -> None:
    from qa_agent.requirement_analysis import RequirementAnalysisService, RequirementRequest

    source = RequirementSource("REQ-1", "Orders", "", "markdown", "req.md", ((2, "User must not save the order"), (3, "User must save the order")))

    result = RequirementAnalysisService().analyze(RequirementRequest(source))

    assert any(item.category == "conflicting_criteria" for item in result.findings)


def test_analysis_stops_before_scanning_more_criteria_than_budget() -> None:
    from qa_agent.requirement_analysis import RequirementAnalysisService, RequirementRequest

    source = RequirementSource("REQ-1", "Orders", "", "markdown", "req.md", tuple((line, "Payment succeeds") for line in range(1, 10)))

    result = RequirementAnalysisService().analyze(RequirementRequest(source, max_actions=4))

    assert result.termination_reason == "BUDGET_EXHAUSTED"
    assert len(result.evidence) < 9


def test_analysis_stops_when_budget_exhausted() -> None:
    from qa_agent.requirement_analysis import RequirementAnalysisService, RequirementRequest

    result = RequirementAnalysisService().analyze(RequirementRequest(RequirementSource("REQ-1", "Checkout", "", "markdown", "req.md"), max_actions=1))

    assert (result.decision, result.termination_reason) == ("incomplete", "BUDGET_EXHAUSTED")


def test_requirement_review_keeps_requirement_and_review_evidence(tmp_path) -> None:
    from qa_agent.requirement_analysis import RequirementAnalysisService
    from qa_agent.requirements import Requirement
    from qa_agent.review import Evidence

    requirement = Requirement("REQ-1", "Checkout", "", "markdown", "req.md")
    requirement_evidence = [Evidence("EV-REQ-001", "requirement", "req.md", 1, 1, "sha256:x")]
    (tmp_path / "test_empty.py").write_text("def test_empty():\n    pass\n")

    result = RequirementAnalysisService().review_pr(requirement, requirement_evidence, tmp_path)

    assert "EV-REQ-001" in {item.id for item in result.evidence}
    assert result.gate is not None


def test_requirement_aware_review_is_incomplete_without_requirement_evidence(tmp_path) -> None:
    from qa_agent.requirement_analysis import RequirementAnalysisService
    from qa_agent.requirements import Requirement

    result = RequirementAnalysisService().review_pr(Requirement("REQ-1", "Checkout", "body", "markdown", "req.md"), [], tmp_path)

    assert result.termination_reason == "INSUFFICIENT_EVIDENCE"
