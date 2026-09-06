from qa_agent.evals import EvalCase, run_cases, run_metrics, run_v01_evals, v01_cases


def test_v01_eval_catalog_has_80_labeled_cases() -> None:
    assert len(v01_cases()) == 155


def test_v01_eval_runner_has_no_rule_regressions() -> None:
    total, failures = run_v01_evals()
    assert total == 155
    assert failures == []


def test_eval_metrics_report_precision_and_recall() -> None:
    metrics = run_metrics(v01_cases())
    assert metrics.cases == 155
    assert metrics.precision == 1.0
    assert metrics.recall == 1.0


def test_eval_runner_rejects_unexpected_findings() -> None:
    total, failures = run_cases([
        EvalCase("strict", "def test_case():\n    assert True\n", "TQ005", expected_rules=("TQ005",)),
    ])

    assert total == 1
    assert failures == ["strict-unexpected"]
