from pathlib import Path


def test_service_is_incomplete_without_explicit_generator(tmp_path: Path) -> None:
    from qa_agent.test_engineering_service import TestEngineeringRequest, TestEngineeringService

    result = TestEngineeringService().run(TestEngineeringRequest("REQ-1", tmp_path, ("EV-REQ-001",)))

    assert (result.status.decision, result.status.termination_reason) == ("incomplete", "INSUFFICIENT_EVIDENCE")


def test_service_accepts_passing_test_only_patch(tmp_path: Path) -> None:
    from qa_agent.test_engineering import GeneratedPatch, PatchFile
    from qa_agent.test_engineering_service import TestEngineeringRequest, TestEngineeringService

    class Generator:
        def generate(self, plan, previous=None):
            return GeneratedPatch("GP-1", (PatchFile("tests/test_generated.py", "def test_generated():\n    assert True\n"),), ("EV-GEN-001",))

    (tmp_path / "tests").mkdir()
    result = TestEngineeringService(generator=Generator()).run(TestEngineeringRequest("REQ-1", tmp_path, ("EV-REQ-001",)))

    assert result.status.decision == "accepted"
    assert result.execution.passed is True
