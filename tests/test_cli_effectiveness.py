from __future__ import annotations

import json
from pathlib import Path
import shutil


def test_missing_effectiveness_arguments_are_structured_and_do_not_create_db(tmp_path: Path, capsys) -> None:
    from qa_agent.cli import main

    database = tmp_path / "trace.db"

    assert main(["assess-effectiveness", "--format", "json", "--trace-db", str(database)]) == 2

    output = capsys.readouterr().out
    assert '"decision": "incomplete"' in output
    assert '"termination_reason": "INSUFFICIENT_EVIDENCE"' in output
    assert not database.exists()


def test_v04_eval_command_is_registered(capsys) -> None:
    from qa_agent.cli import main

    assert main(["eval", "--version", "v0.4"]) == 0
    assert '"failures": []' in capsys.readouterr().out


def test_reference_sample_runs_without_mutating_source_repository(tmp_path: Path, capsys) -> None:
    from qa_agent.cli import main

    sample = Path(__file__).parents[1] / "examples" / "v04-sample"
    repository = tmp_path / "repository"
    shutil.copytree(sample / "repository", repository)
    database = tmp_path / "trace.db"

    result = main(
        [
            "assess-effectiveness",
            "--requirement",
            "REQ-CHECKOUT-001",
            "--repository",
            str(repository),
            "--trace-db",
            str(database),
            "--test-context",
            str(sample / "test-context.json"),
            "--mutation-report",
            str(sample / "mutation-report.json"),
            "--min-score",
            "1.0",
            "--format",
            "json",
        ]
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["decision"] == "pass"
    assert payload["score"]["score"] == 1.0
    assert database.exists()
