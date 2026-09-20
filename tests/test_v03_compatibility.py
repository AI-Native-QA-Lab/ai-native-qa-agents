def test_v03_result_keeps_legacy_wire_shape() -> None:
    from qa_agent.test_engineering import TestCandidateStatus, TestEngineeringResult, TestIntent

    payload = TestEngineeringResult(
        intent=TestIntent("TI-1", "REQ-1", "checkout", ("EV-REQ-001",)),
        status=TestCandidateStatus("rejected", "INSUFFICIENT_EVIDENCE", ("EV-REQ-001",)),
    ).to_dict()

    assert payload["schema_version"] == "v0.3"
    assert set(payload["intent"]) == {"id", "requirement_id", "subject", "evidence_ids"}


def test_semantic_fields_are_appended_without_changing_old_arguments() -> None:
    from pathlib import Path

    from qa_agent.test_engineering import TestIntent
    from qa_agent.test_engineering_service import TestEngineeringRequest

    intent = TestIntent(
        "TI-1",
        "REQ-1",
        "checkout",
        ("EV-1",),
        ("AC-1",),
        ("RISK-1",),
        "decline",
        "error is visible",
    )
    request = TestEngineeringRequest(
        "REQ-1",
        Path("."),
        ("EV-1",),
        60,
        0,
        ("tests",),
        "pytest",
        ("AC-1",),
        ("RISK-1",),
        "decline",
        "error is visible",
    )
    assert intent.business_oracle == "error is visible"
    assert request.acceptance_criterion_ids == ("AC-1",)


def test_evidence_extensions_are_optional_and_serializable() -> None:
    from qa_agent.review import Evidence

    legacy = Evidence("EV-1", "requirement", "req.md", 1, 1, "sha256:x")
    extended = Evidence(
        "EV-2",
        "test_execution",
        "tests/test_checkout.py",
        1,
        1,
        "sha256:y",
        subject="tests/test_checkout.py::test_declined",
        source_ref="tests/test_checkout.py#L1",
        redacted_excerpt="assert response.error",
        metadata={"redaction": {"applied": False}},
    )

    assert legacy.subject is None
    assert extended.to_dict()["source_ref"] == "tests/test_checkout.py#L1"
