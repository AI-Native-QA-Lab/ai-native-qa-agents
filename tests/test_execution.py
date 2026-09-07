from pathlib import Path

import pytest


def _patch(path: str):
    from qa_agent.test_engineering import GeneratedPatch, PatchFile

    return GeneratedPatch("GP-1", (PatchFile(path, "def test_generated():\n    assert True\n"),), ("EV-GEN-001",))


@pytest.mark.parametrize("path", ("src/orders.py", "../test_escape.py", "/tmp/test_escape.py"))
def test_patch_validator_rejects_unsafe_paths(path: str) -> None:
    from qa_agent.execution import PatchSafetyError, validate_patch

    with pytest.raises(PatchSafetyError):
        validate_patch(_patch(path), ("tests",))


def test_pytest_execution_applies_patch_only_in_sandbox(tmp_path: Path) -> None:
    from qa_agent.execution import PytestExecutionBackend

    (tmp_path / "tests").mkdir()
    result = PytestExecutionBackend().execute(tmp_path, _patch("tests/test_generated.py"), 10)

    assert result.passed is True
    assert not (tmp_path / "tests" / "test_generated.py").exists()
