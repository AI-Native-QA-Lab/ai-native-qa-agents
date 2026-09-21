from __future__ import annotations

import json
from pathlib import Path


def test_dirty_case_requires_snapshot_and_reason(tmp_path: Path) -> None:
    from qa_agent.benchmark import load_manifest

    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "case_id": "case-1",
                "repository": {"path": str(tmp_path), "revision": "tree:revision"},
                "framework": "pytest",
                "artifacts": {},
                "argv": ["qa-agent", "assess-effectiveness"],
                "allow_dirty": True,
                "working_tree": {"status": "dirty"},
                "ground_truth": {"survivor_labels": [], "signal_labels": []},
                "adjudication": {"status": "unresolved"},
            }
        ),
        encoding="utf-8",
    )

    result = load_manifest(path)

    assert result.decision == "incomplete"
    assert "snapshot_hash" in result.reasons


def test_zero_metric_denominators_are_none() -> None:
    from qa_agent.benchmark import aggregate_metrics

    metrics = aggregate_metrics([])

    assert metrics["precision"] is None
    assert metrics["false_positive_rate"] is None
    assert metrics["cost_per_report"] is None

