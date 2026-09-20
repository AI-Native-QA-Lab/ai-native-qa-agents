import sys
import json
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "packages"))


@pytest.fixture
def valid_context():
    from qa_agent.effectiveness import TestEffectivenessContext

    fixture = Path(__file__).parent / "fixtures" / "v04" / "context-valid.json"
    return TestEffectivenessContext.from_dict(json.loads(fixture.read_text(encoding="utf-8")), 1_000_000)


@pytest.fixture
def valid_report(tmp_path: Path) -> Path:
    source = Path(__file__).parent / "fixtures" / "v04" / "mutation" / "report-valid.json"
    target = tmp_path / "report.json"
    target.write_bytes(source.read_bytes())
    return target
