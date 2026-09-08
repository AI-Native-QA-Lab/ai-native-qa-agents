from pathlib import Path

from qa_agent.cli import main


def test_analyze_then_map_coverage_uses_explicit_trace_db(tmp_path: Path, capsys) -> None:
    requirement = tmp_path / "checkout.md"
    database = tmp_path / "trace.db"
    requirement.write_text("# Checkout\n\n## Acceptance Criteria\n- Payment succeeds\n")
    (tmp_path / "checkout.py").write_text("def checkout(): pass\n")

    assert main(["analyze-requirement", str(requirement), "--trace-db", str(database), "--format", "json"]) == 0
    assert main(["map-coverage", "--requirement", "checkout", "--repository", str(tmp_path), "--trace-db", str(database), "--format", "json"]) == 0

    assert '"status": "unverified"' in capsys.readouterr().out


def test_analyze_requirement_human_output_is_a_requirement_report(tmp_path: Path, capsys) -> None:
    requirement = tmp_path / "checkout.md"
    database = tmp_path / "trace.db"
    requirement.write_text("# Checkout\n\n## Acceptance Criteria\n- Payment succeeds\n")

    assert main(["analyze-requirement", str(requirement), "--trace-db", str(database)]) == 0

    output = capsys.readouterr().out
    assert "Decision: warn" in output
    assert "Evidence: 1" in output


def test_requirement_human_report_includes_decision_termination_and_evidence() -> None:
    from qa_agent.reporting import render_requirement_human
    from qa_agent.requirements import RequirementResult
    from qa_agent.review import Evidence

    report = render_requirement_human(
        RequirementResult(
            decision="warn",
            termination_reason="EVIDENCE_SUFFICIENT",
            evidence=[Evidence("EV-1", "requirement", "req.md", 1, 1, "sha256:x")],
        )
    )

    assert "Decision: warn" in report
    assert "Termination: EVIDENCE_SUFFICIENT" in report
    assert "Evidence: 1" in report
