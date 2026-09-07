import pytest


def test_requirement_result_has_v02_schema() -> None:
    from qa_agent.requirements import AcceptanceCriterion, Requirement, RequirementContext, RequirementResult

    requirement = Requirement(
        "REQ-1",
        "Checkout",
        "body",
        "markdown",
        "req.md",
        (AcceptanceCriterion("REQ-1-AC-1", "Payment succeeds", 3),),
    )

    payload = RequirementResult(requirement=requirement, context=RequirementContext("CTX-1", requirement.id, ("EV-1",), ("checkout.py",))).to_dict()

    assert payload["schema_version"] == "v0.2"
    assert payload["requirement"]["acceptance_criteria"][0]["line"] == 3
    assert payload["context"]["repository_paths"] == ("checkout.py",)


def test_trace_link_confidence_does_not_upgrade_unverified_status() -> None:
    from qa_agent.requirements import TraceLink

    link = TraceLink("REQ-1", "test", "tests/test_checkout.py", "test_checkout", ("EV-1",), "unverified", 1.0)

    assert link.status == "unverified"


def test_requirement_contracts_reject_invalid_values() -> None:
    from qa_agent.requirements import TestabilityFinding, TraceLink

    with pytest.raises(ValueError):
        TraceLink("REQ-1", "document", "readme.md", "", ("EV-1",), "unverified", 0.2)
    with pytest.raises(ValueError):
        TestabilityFinding("F-1", "ambiguous", "bad", "message", "REQ-1-AC-1", ("EV-1",))
