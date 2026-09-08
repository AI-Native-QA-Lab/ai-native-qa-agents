import json
from pathlib import Path

import pytest


def test_json_generator_reads_a_local_test_patch_fixture(tmp_path: Path) -> None:
    from qa_agent.test_engineering import TestIntent, TestPlan, TestScenario
    from qa_agent.test_generation import JsonTestGenerator

    fixture = tmp_path / "candidate.json"
    fixture.write_text(json.dumps({"files": [{"path": "tests/test_generated.py", "content": "def test_generated():\n    assert True\n"}]}))
    intent = TestIntent("TI-1", "REQ-1", "checkout", ("EV-REQ-001",))
    plan = TestPlan("TP-1", intent.id, "pytest", (TestScenario("TS-1", intent.id, "candidate", ("run",), "pass", ("EV-REQ-001",)),), ("EV-REQ-001",))

    patch = JsonTestGenerator(fixture).generate(plan)

    assert patch.files[0].path == "tests/test_generated.py"
    assert patch.evidence_ids == ("EV-GEN-001",)


def test_json_generator_rejects_malformed_fixture(tmp_path: Path) -> None:
    from qa_agent.test_generation import JsonTestGenerator

    fixture = tmp_path / "candidate.json"
    fixture.write_text("[]")

    with pytest.raises(ValueError):
        JsonTestGenerator(fixture)
