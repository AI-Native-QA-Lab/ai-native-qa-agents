import json
from pathlib import Path

import pytest


def test_v04_migration_preserves_legacy_tables_and_adds_explicit_links(tmp_path) -> None:
    from qa_agent.trace_store import SQLiteTraceStore

    store = SQLiteTraceStore(tmp_path / "trace.db")
    with store._connect() as connection:
        names = {
            row[0]
            for row in connection.execute("select name from sqlite_master where type = 'table'")
        }
        version = connection.execute("pragma user_version").fetchone()[0]
        foreign_keys = connection.execute("pragma foreign_keys").fetchone()[0]
    assert {"requirements", "trace_links", "test_contexts", "mutation_runs", "mutation_results", "mutation_trace_links", "assessments", "observations", "loop_traces"} <= names
    assert version == 2
    assert foreign_keys == 1


def test_v04_evidence_query_is_bounded_and_round_trips(tmp_path) -> None:
    from qa_agent.review import Evidence
    from qa_agent.trace_store import SQLiteTraceStore

    store = SQLiteTraceStore(tmp_path / "trace.db")
    evidence = Evidence(
        "EV-1",
        "test_context",
        "context.json",
        1,
        1,
        "sha256:" + "1" * 64,
        subject="CTX-1",
        source_ref="context.json#L1",
        metadata={"redaction": {"applied": False, "policy": "bounded-redacted-v1", "max_bytes": 4096}, "limits": {"context_bytes": 10, "report_bytes": 10}},
    )
    store.save_evidence([evidence])
    assert store.get_evidence_by_ids(["EV-1"], 1) == [evidence]
    assert store.get_evidence_by_ids(["EV-1"], 0) == []


def test_v04_context_and_mutation_records_round_trip(tmp_path) -> None:
    from qa_agent.effectiveness import MutationResult, MutationRun, MutationTraceLink, Mutant, TestEffectivenessContext
    from qa_agent.trace_store import SQLiteTraceStore

    fixture = Path(__file__).parent / "fixtures" / "v04" / "context-valid.json"
    context = TestEffectivenessContext.from_dict(json.loads(fixture.read_text(encoding="utf-8")), 1_000_000)
    store = SQLiteTraceStore(tmp_path / "trace.db")
    store.save_test_context(context)
    context_id = store.context_id_for(context)
    assert store.get_test_context(context_id) == context

    run = MutationRun("RUN-1", "ASSESS-1", "offline", "REV-1", ("src/checkout.py",), ("tests/test_checkout.py",), ("tests/test_checkout.py::test_declined",), "completed", "complete", ("M-1",), ("EV-RUN-1",))
    mutant = Mutant("M-1", "src/checkout.py", 3, "replace-constant", "False", "True", "active", ("EV-M-1",))
    result = MutationResult("RUN-1", "M-1", "killed", ("tests/test_checkout.py::test_declined",), ("tests/test_checkout.py::test_declined",), 1, None, None, ("EV-RESULT-1",))
    link = MutationTraceLink("RUN-1", "M-1", "REQ-1", "TI-1", "TS-1", "The error state is asserted", "verified", ("EV-LINK-1",))
    store.save_mutation(run, [mutant], [result], [link])
    with store._connect() as connection:
        assert connection.execute("select count(*) from mutation_results where run_id = 'RUN-1'").fetchone()[0] == 1
        assert connection.execute("select count(*) from mutation_trace_links where run_id = 'RUN-1'").fetchone()[0] == 1


def test_v04_rejects_newer_schema_without_overwriting(tmp_path) -> None:
    from qa_agent.trace_store import SQLiteTraceStore

    database = tmp_path / "trace.db"
    store = SQLiteTraceStore(database)
    with store._connect() as connection:
        connection.execute("pragma user_version = 99")
    with pytest.raises(RuntimeError):
        SQLiteTraceStore(database)


def test_v04_service_persists_one_observation_for_each_loop_trace(tmp_path, valid_context, valid_report, monkeypatch) -> None:
    import qa_agent.effectiveness_service as effectiveness_service
    from qa_agent.effectiveness_service import TestEffectivenessRequest, TestEffectivenessService
    from qa_agent.runtime import ExecutionBudget
    from qa_agent.trace_store import SQLiteTraceStore

    monkeypatch.setattr(effectiveness_service, "resolve_repository_revision", lambda _: "REV-1")
    store = SQLiteTraceStore(tmp_path / "trace.db")
    assessment = TestEffectivenessService(store).assess(
        TestEffectivenessRequest("REQ-1", tmp_path, valid_context, valid_report, None, 0.8, ExecutionBudget.v04_defaults())
    )

    with store._connect() as connection:
        observed = connection.execute(
            "select count(*) from observations where assessment_id = ?",
            (assessment.assessment_id,),
        ).fetchone()[0]
    assert observed == len(assessment.loop_trace)
