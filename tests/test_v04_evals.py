from __future__ import annotations


def test_v04_eval_manifest_covers_required_case_labels() -> None:
    from qa_agent.evals import v04_cases

    labels = {case["id"] for case in v04_cases()}

    assert {
        "valid-pass",
        "partial-warning",
        "low-score-failure",
        "missing-oracle",
        "unmapped-survivor",
        "bad-revision",
        "duplicate-id",
        "path-escape",
        "prompt-in-data",
        "permission-denial",
        "budget-exhaustion",
        "unavailable-backend",
    } <= labels


def test_v04_evals_have_no_failures() -> None:
    from qa_agent.evals import run_v04_evals

    total, failures = run_v04_evals()

    assert total >= 12
    assert failures == []
