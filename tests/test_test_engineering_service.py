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
            return GeneratedPatch("GP-1", (PatchFile("tests/test_generated.py", "def test_generated():\n    value = 1\n    assert value == 1\n"),), ("EV-GEN-001",))

    (tmp_path / "tests").mkdir()
    result = TestEngineeringService(generator=Generator()).run(TestEngineeringRequest("REQ-1", tmp_path, ("EV-REQ-001",)))

    assert result.status.decision == "accepted"
    assert result.execution.passed is True
    assert result.gates == {"parse": "passed", "compile": "passed", "assertion": "passed", "reviewer": "passed", "execution": "passed"}


def test_service_rejects_constant_assertion_before_execution(tmp_path: Path) -> None:
    from qa_agent.test_engineering import GeneratedPatch, PatchFile
    from qa_agent.test_engineering_service import TestEngineeringRequest, TestEngineeringService

    class Generator:
        def generate(self, plan, previous=None):
            return GeneratedPatch("GP-1", (PatchFile("tests/test_generated.py", "def test_generated():\n    assert True\n"),), ("EV-GEN-001",))

    result = TestEngineeringService(generator=Generator()).run(TestEngineeringRequest("REQ-1", tmp_path, ("EV-REQ-001",)))

    assert result.status.decision == "rejected"
    assert result.status.termination_reason == "INSUFFICIENT_EVIDENCE"
    assert result.gates["assertion"] == "rejected"


def test_service_stops_after_configured_repairs(tmp_path: Path) -> None:
    from qa_agent.test_engineering import GeneratedPatch, PatchFile
    from qa_agent.test_engineering_service import TestEngineeringRequest, TestEngineeringService

    class Generator:
        def generate(self, plan, previous=None):
            return GeneratedPatch("GP-1", (PatchFile("tests/test_generated.py", "def test_generated():\n    value = 1\n    assert value == 2\n"),), ("EV-GEN-001",))

    (tmp_path / "tests").mkdir()
    result = TestEngineeringService(generator=Generator()).run(
        TestEngineeringRequest("REQ-1", tmp_path, ("EV-REQ-001",), max_repairs=1)
    )

    assert result.status.termination_reason == "BUDGET_EXHAUSTED"
    assert len(result.repairs) == 1
    assert any(item.action_id == "analyze_failure" for item in result.loop_trace)
    assert "exit code" in result.repairs[0].reason


def test_service_preserves_timeout_instead_of_calling_it_budget_exhaustion(tmp_path: Path) -> None:
    from qa_agent.test_engineering import ExecutionResult, GeneratedPatch, PatchFile
    from qa_agent.test_engineering_service import TestEngineeringRequest, TestEngineeringService

    class Generator:
        def generate(self, plan, previous=None):
            return GeneratedPatch("GP-1", (PatchFile("tests/test_generated.py", "def test_generated():\n    value = 1\n    assert value == 1\n"),), ("EV-GEN-001",))

    class TimeoutBackend:
        def execute(self, *args):
            return ExecutionResult("pytest", (), None, False, "TIMEOUT", None, None, 1, ("EV-EXEC-001",))

    result = TestEngineeringService(generator=Generator(), backend=TimeoutBackend()).run(TestEngineeringRequest("REQ-1", tmp_path, ("EV-REQ-001",), max_repairs=1))

    assert result.status.termination_reason == "TIMEOUT"


def test_service_returns_structured_rejection_for_unsafe_patch(tmp_path: Path) -> None:
    from qa_agent.test_engineering import GeneratedPatch, PatchFile
    from qa_agent.test_engineering_service import TestEngineeringRequest, TestEngineeringService

    class Generator:
        def generate(self, plan, previous=None):
            return GeneratedPatch("GP-1", (PatchFile("src/unsafe.py", "def test_unsafe():\n    value = 1\n    assert value == 1\n"),), ("EV-GEN-001",))

    result = TestEngineeringService(generator=Generator()).run(TestEngineeringRequest("REQ-1", tmp_path, ("EV-REQ-001",)))

    assert result.status.decision == "rejected"
    assert result.status.termination_reason == "INSUFFICIENT_EVIDENCE"
