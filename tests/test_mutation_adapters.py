import json
from pathlib import Path

import pytest


def _report(**overrides):
    report = {
        "schema_version": 1,
        "backend": "offline",
        "repository_revision": "REV-1",
        "observation_status": "complete",
        "target_paths": ["src/cart.py"],
        "selected_test_ids": ["tests/test_cart.py::test_declined"],
        "mutants": [
            {
                "id": "M-1",
                "path": "src/cart.py",
                "line": 12,
                "operator": "replace-constant",
                "original": "False",
                "mutated": "True",
                "outcome": "killed",
                "executed_test_ids": ["tests/test_cart.py::test_declined"],
                "killing_test_ids": ["tests/test_cart.py::test_declined"],
                "duration_ms": 1,
                "stdout_hash": None,
                "stderr_hash": None,
            }
        ],
    }
    report.update(overrides)
    return report


def _write_report(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "report.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_offline_parser_normalizes_valid_report(tmp_path) -> None:
    from qa_agent.mutation_adapters import OfflineMutationReportAdapter
    from qa_agent.runtime import ExecutionBudget

    path = _write_report(tmp_path, _report())
    result = OfflineMutationReportAdapter().parse(path, "REV-1", ExecutionBudget.v04_defaults())
    assert result.results[0].outcome == "killed"
    assert result.observation_status == "complete"
    assert result.process_status == "completed"
    assert result.raw_report_hash.startswith("sha256:")


def test_prompt_data_is_never_executed(tmp_path) -> None:
    from qa_agent.mutation_adapters import OfflineMutationReportAdapter
    from qa_agent.runtime import ExecutionBudget

    path = tmp_path / "report.json"
    fixture = Path(__file__).parent / "fixtures" / "v04" / "mutation" / "report-prompt-data.json"
    path.write_bytes(fixture.read_bytes())
    result = OfflineMutationReportAdapter().parse(path, "REV-1", ExecutionBudget.v04_defaults())
    assert result.results[0].outcome == "survived"


@pytest.mark.parametrize(
    "override",
    [
        {"schema_version": 2},
        {"mutants": [{"id": "M-1"}, {"id": "M-1"}]},
        {"mutants": [{**_report()["mutants"][0], "outcome": "unknown"}]},
        {"mutants": [{**_report()["mutants"][0], "path": "../escape.py"}]},
        {"repository_revision": "REV-2"},
    ],
)
def test_offline_parser_rejects_invalid_input(tmp_path, override) -> None:
    from qa_agent.mutation_adapters import MutationInputError, OfflineMutationReportAdapter
    from qa_agent.runtime import ExecutionBudget

    payload = _report()
    payload.update(override)
    with pytest.raises(MutationInputError):
        OfflineMutationReportAdapter().parse(_write_report(tmp_path, payload), "REV-1", ExecutionBudget.v04_defaults())


def test_offline_parser_preserves_partial_observation_and_not_run(tmp_path) -> None:
    from qa_agent.mutation_adapters import OfflineMutationReportAdapter
    from qa_agent.runtime import ExecutionBudget

    fixture = Path(__file__).parent / "fixtures" / "v04" / "mutation" / "report-partial.json"
    result = OfflineMutationReportAdapter().parse(fixture, "REV-1", ExecutionBudget.v04_defaults())
    assert result.observation_status == "partial"
    assert result.process_status == "partial"
    assert {item.outcome for item in result.results} == {"killed", "not_run"}


def test_parser_rejects_oversized_report(tmp_path) -> None:
    from qa_agent.mutation_adapters import MutationInputError, OfflineMutationReportAdapter
    from qa_agent.runtime import ExecutionBudget

    path = _write_report(tmp_path, _report(mutants=[{**_report()["mutants"][0], "original": "x" * 100_000}]))
    budget = ExecutionBudget.v04_defaults()
    budget.max_report_bytes = 20
    with pytest.raises(MutationInputError):
        OfflineMutationReportAdapter().parse(path, "REV-1", budget)


def test_capability_adapters_do_not_download_or_execute_when_unavailable(monkeypatch, tmp_path) -> None:
    from qa_agent.mutation_adapters import MutmutMutationBackend, PitMutationBackend, StrykerMutationBackend
    from qa_agent.mutation_backends import MutationUnavailableError, MutationUnsupportedError

    monkeypatch.setattr("shutil.which", lambda name: None)
    assert MutmutMutationBackend().detect(tmp_path).status == "unavailable"
    with pytest.raises(MutationUnavailableError):
        MutmutMutationBackend().run(None)
    with pytest.raises(MutationUnsupportedError):
        PitMutationBackend().run(None)
    with pytest.raises(MutationUnsupportedError):
        StrykerMutationBackend().run(None)
