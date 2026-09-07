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
