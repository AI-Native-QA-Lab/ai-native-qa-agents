from pathlib import Path

from qa_agent.cli import main
from qa_agent.reporting import render_human
from qa_agent.review import ReviewResult


def test_detect_reports_python_and_pytest(tmp_path: Path, capsys) -> None:
    (tmp_path / "test_example.py").write_text("def test_it():\n    assert True\n")

    assert main(["detect", str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "Python" in output
    assert "pytest" in output


def test_review_json_exits_nonzero_for_critical_finding(tmp_path: Path, capsys) -> None:
    (tmp_path / "test_example.py").write_text("def test_it():\n    assert True\n")

    assert main(["review", str(tmp_path), "--format", "json"]) == 1
    assert '"decision": "fail"' in capsys.readouterr().out


def test_config_show_exposes_safe_v01_defaults(capsys) -> None:
    assert main(["config", "show"]) == 0
    assert '"max_actions": 6' in capsys.readouterr().out


def test_rules_list_exposes_all_v01_rules(capsys) -> None:
    assert main(["rules", "list"]) == 0
    output = capsys.readouterr().out
    assert "TQ001" in output and "TQ015" in output


def test_eval_command_reports_metrics(capsys) -> None:
    assert main(["eval"]) == 0
    output = capsys.readouterr().out
    assert '"precision": 1.0' in output and '"cases": 155' in output


def test_review_reads_yaml_project_configuration(tmp_path: Path, capsys) -> None:
    (tmp_path / "test_sleep.py").write_text("def test_sleep():\n    import time\n    time.sleep(1)\n")
    (tmp_path / ".qa-agent.yaml").write_text("rules:\n  TQ012:\n    severity: low\n")

    assert main(["review", str(tmp_path), "--format", "json"]) == 0
    assert '"severity": "low"' in capsys.readouterr().out


def test_review_reads_json_rule_configuration(tmp_path: Path, capsys) -> None:
    (tmp_path / "test_sleep.py").write_text("def test_sleep():\n    import time\n    time.sleep(1)\n")
    config = tmp_path / "qa-agent.json"
    config.write_text('{"rules": {"TQ012": {"severity": "low"}}}')

    assert main(["review", str(tmp_path), "--config", str(config), "--format", "json"]) == 0
    assert '"severity": "low"' in capsys.readouterr().out


def test_human_report_labels_coverage_gaps_correctly() -> None:
    result = ReviewResult(coverage_gaps=[{"path": "orders.py"}])

    assert "Coverage Gaps: 1" in render_human(result)
    assert "Changed Files: 0" in render_human(result)


def test_human_report_marks_incomplete_review_risk_unknown() -> None:
    assert "Risk: unknown" in render_human(ReviewResult(decision="incomplete"))
