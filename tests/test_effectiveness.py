import json
from pathlib import Path

import pytest


FIXTURE = Path(__file__).parent / "fixtures" / "v04" / "context-valid.json"


def _evidence(evidence_id: str, evidence_type: str, subject: str, status: str = "verified"):
    from qa_agent.review import Evidence

    metadata = {
        "redaction": {"applied": False, "policy": "bounded-redacted-v1", "max_bytes": 4096},
        "limits": {"context_bytes": 1_000_000, "report_bytes": 2_000_000},
    }
    return Evidence(
        evidence_id,
        evidence_type,
        "tests/test_checkout.py",
        1,
        1,
        "sha256:" + (evidence_id[-1].lower() * 64 if evidence_id[-1].isalnum() else "a" * 64),
        status=status,
        subject=subject,
        source_ref="tests/test_checkout.py#L1",
        metadata=metadata,
    )


def _run(process_status: str = "completed", observation_status: str = "complete"):
    from qa_agent.effectiveness import MutationResult, MutationRun

    result = MutationResult(
        "RUN-1",
        "M-1",
        "killed",
        ("tests/test_checkout.py::test_declined",),
        ("tests/test_checkout.py::test_declined",),
        1,
        None,
        None,
        ("EV-M-1",),
    )
    run = MutationRun(
        "RUN-1",
        "ASSESS-1",
        "offline",
        "REV-1",
        ("src/checkout.py",),
        ("tests/test_checkout.py",),
        ("tests/test_checkout.py::test_declined",),
        process_status,
        observation_status,
        ("M-1",),
        ("EV-RUN-1",),
    )
    return run, result


def test_context_validates_canonical_artifact_hash() -> None:
    from qa_agent.effectiveness import TestEffectivenessContext, artifact_hash

    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    context = TestEffectivenessContext.from_dict(payload, 1_000_000)
    assert context.requirement_id == "REQ-1"
    assert context.test_ids == ("tests/test_checkout.py::test_declined",)
    assert context.artifact_hash == artifact_hash(payload, omit_field="artifact_hash")
    assert context.to_dict()["schema_version"] == "v0.4"


def test_context_rejects_invalid_evidence_status_and_path_escape() -> None:
    from qa_agent.effectiveness import TestEffectivenessContext

    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["evidence"][0]["status"] = "unknown"
    with pytest.raises(ValueError):
        TestEffectivenessContext.from_dict(payload, 1_000_000)

    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["target_paths"] = ["../checkout.py"]
    with pytest.raises(ValueError):
        TestEffectivenessContext.from_dict(payload, 1_000_000)


def test_partial_one_killed_and_many_not_run_never_passes() -> None:
    from qa_agent.effectiveness import MutationResult, MutationRun, evaluate_mutation_gate, score_results

    results = [
        MutationResult(
            "RUN-1",
            "M-1",
            "killed",
            ("tests/test_checkout.py::test_declined",),
            ("tests/test_checkout.py::test_declined",),
            1,
            None,
            None,
            ("EV-M-1",),
        )
    ] + [
        MutationResult("RUN-1", f"M-{index}", "not_run", (), (), 0, None, None, (f"EV-M-{index}",))
        for index in range(2, 101)
    ]
    score = score_results(results, ("EV-SCORE-1",))
    run = MutationRun(
        "RUN-1",
        "ASSESS-1",
        "offline",
        "REV-1",
        ("src/checkout.py",),
        ("tests/test_checkout.py",),
        ("tests/test_checkout.py::test_declined",),
        "partial",
        "complete",
        tuple(item.mutant_id for item in results),
        ("EV-RUN-1",),
    )
    verified_execution = _evidence("EV-EXEC-1", "test_execution", "tests/test_checkout.py::test_declined")
    verified_assertion = _evidence("EV-ASSERT-1", "test_assertion", "tests/test_checkout.py::test_declined")
    gate = evaluate_mutation_gate(
        True,
        run,
        score,
        (),
        (),
        0.8,
        [verified_execution],
        [verified_assertion],
        "EVIDENCE_SUFFICIENT",
    )
    assert score.score == 1.0
    assert score.not_run_mutants == 99
    assert gate.decision == "warn"


def test_unmapped_survivor_keeps_null_semantic_fields() -> None:
    from qa_agent.effectiveness import MutationTraceLink

    link = MutationTraceLink("RUN-1", "M-1", None, None, None, None, "unmapped", ("EV-M-1",))
    assert link.mapping_status == "unmapped"
    assert link.intent_id is None


def test_score_and_gate_cover_pass_fail_and_incomplete() -> None:
    from qa_agent.effectiveness import FakeTestSignal, evaluate_mutation_gate, score_results

    run, killed = _run()
    evidence = [_evidence("EV-EXEC-1", "test_execution", "tests/test_checkout.py::test_declined"), _evidence("EV-ASSERT-1", "test_assertion", "tests/test_checkout.py::test_declined")]
    score = score_results([killed], ("EV-SCORE-1",))
    passed = evaluate_mutation_gate(True, run, score, (), (), 0.8, [evidence[0]], [evidence[1]], "EVIDENCE_SUFFICIENT")
    assert passed.decision == "pass"

    survived = killed.__class__("RUN-1", "M-1", "survived", (), (), 1, None, None, ("EV-M-1",))
    failed_score = score_results([survived], ("EV-SCORE-1",))
    failed = evaluate_mutation_gate(True, run, failed_score, (), (), 0.8, [evidence[0]], [evidence[1]], "EVIDENCE_SUFFICIENT")
    assert failed.decision == "fail"

    high_signal = FakeTestSignal("SIG-1", "mutation_survivor", "high", "high-risk survivor", "deterministic", "verified", ("EV-M-1",))
    high_failure = evaluate_mutation_gate(True, run, score, (), (high_signal,), 0.8, [evidence[0]], [evidence[1]], "EVIDENCE_SUFFICIENT")
    assert high_failure.decision == "fail"

    incomplete = evaluate_mutation_gate(True, run, score, (), (), 0.8, [], [evidence[1]], "INSUFFICIENT_EVIDENCE")
    assert incomplete.decision == "incomplete"


def test_score_rejects_invalid_result_outcome() -> None:
    from qa_agent.effectiveness import MutationResult

    with pytest.raises(ValueError):
        MutationResult("RUN-1", "M-1", "unknown", (), (), 0, None, None, ())
