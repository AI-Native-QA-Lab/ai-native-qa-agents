from pathlib import Path

import pytest


def _patch(path: str, content: str = "def test_generated():\n    value = 1\n    assert value == 1\n"):
    from qa_agent.test_engineering import GeneratedPatch, PatchFile

    return GeneratedPatch("GP-1", (PatchFile(path, content),), ("EV-GEN-001",))


@pytest.mark.parametrize("path", ("src/orders.py", "../test_escape.py", "/tmp/test_escape.py"))
def test_patch_validator_rejects_unsafe_paths(path: str) -> None:
    from qa_agent.execution import PatchSafetyError, validate_patch

    with pytest.raises(PatchSafetyError):
        validate_patch(_patch(path), ("tests",))


def test_pytest_execution_applies_patch_only_in_sandbox(tmp_path: Path) -> None:
    from qa_agent.execution import PytestExecutionBackend

    (tmp_path / "tests").mkdir()
    marker = tmp_path / "untouched.txt"
    marker.write_text("safe")
    result = PytestExecutionBackend().execute(tmp_path, _patch("tests/test_generated.py"), 10)

    assert result.passed is True
    assert "pytest" in " ".join(result.command)
    assert result.command[-1] == "tests/test_generated.py"
    assert not (tmp_path / "tests" / "test_generated.py").exists()
    assert marker.read_text() == "safe"


def test_docker_pytest_backend_reports_unavailable_without_docker(tmp_path: Path, monkeypatch) -> None:
    from qa_agent.execution import DockerPytestExecutionBackend

    monkeypatch.setattr("qa_agent.execution.shutil.which", lambda name: None)
    (tmp_path / "tests").mkdir()
    result = DockerPytestExecutionBackend().execute(tmp_path, _patch("tests/test_generated.py"), 1)

    assert result.termination_reason == "INSUFFICIENT_EVIDENCE"
    assert result.command == ()


def test_playwright_backend_reports_unavailable_without_installing(tmp_path: Path) -> None:
    from qa_agent.execution import PlaywrightExecutionBackend

    result = PlaywrightExecutionBackend(executable="does-not-exist").execute(tmp_path, _patch("tests/test_generated.py"), 1)

    assert result.termination_reason == "INSUFFICIENT_EVIDENCE"
    assert result.command == ()
