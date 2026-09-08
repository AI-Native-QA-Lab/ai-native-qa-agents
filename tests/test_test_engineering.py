import pytest


def test_v03_result_serializes_evidenced_candidate() -> None:
    from qa_agent.test_engineering import TestCandidateStatus, TestEngineeringResult, TestIntent

    result = TestEngineeringResult(
        intent=TestIntent("TI-1", "REQ-1", "checkout", ("EV-REQ-001",)),
        status=TestCandidateStatus("rejected", "INSUFFICIENT_EVIDENCE", ("EV-REQ-001",)),
    )

    assert result.to_dict()["schema_version"] == "v0.3"
    assert result.to_dict()["status"]["decision"] == "rejected"


def test_generated_patch_requires_files_and_evidence() -> None:
    from qa_agent.test_engineering import GeneratedPatch

    with pytest.raises(ValueError):
        GeneratedPatch("GP-1", (), ("EV-1",))
    with pytest.raises(ValueError):
        GeneratedPatch("GP-1", (), ())
