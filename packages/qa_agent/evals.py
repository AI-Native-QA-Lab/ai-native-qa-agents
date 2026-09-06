"""Small, dependency-free runner for deterministic v0.1 rule regressions."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

from .review import ReviewRequest, ReviewService


@dataclass(frozen=True)
class EvalCase:
    id: str
    source: str
    expected_rule: str
    suffix: str = ".py"
    forbidden_rules: tuple[str, ...] = ()
    expected_rules: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvalMetrics:
    cases: int
    precision: float
    recall: float


def v01_cases() -> list[EvalCase]:
    """Return 80 labeled variants covering the stable deterministic rule seam."""
    seeds = [
        ("TQ001", "def test_case():\n    value = 1\n"),
        ("TQ003", "def test_case():\n    pass\n"),
        ("TQ005", "def test_case():\n    assert True\n"),
        ("TQ012", "def test_case():\n    import time\n    time.sleep(1)\n"),
        ("TQ002", "import pytest\n@pytest.mark.skip\ndef test_case():\n    pass\n"),
        ("TQ004", "def test_case():\n    # TODO: implement\n    pass\n"),
        ("TQ006", "def test_case():\n    try:\n        pass\n    except ValueError:\n        pass\n"),
        ("TQ007", "from unittest.mock import Mock\ndef test_case():\n    Mock(); Mock(); Mock()\n    assert 1\n"),
        ("TQ008", "def test_case():\n    return\n    assert False\n"),
        ("TQ009", "def test_case():\n    assert 1\n    assert 1\n"),
        ("TQ010", "def test_case():\n    response = client.get('/')\n    assert response.status_code == 200\n"),
        ("TQ011", "test('case', async ({ page }) => {\n await page.screenshot();\n});\n"),
        ("TQ013", "def test_case():\n    result = {'status': 'success'}\n    assert result['status'] == 'success'\n"),
        ("TQ014", "def test_case():\n    value = 1\n"),
        ("TQ015", "def test_case():\n    try:\n        pass\n    except Exception:\n        pass\n"),
    ]
    cases = []
    expected = {
        "TQ001": ("TQ001", "TQ014"), "TQ003": ("TQ001", "TQ003", "TQ014"),
        "TQ005": ("TQ005", "TQ014"), "TQ012": ("TQ001", "TQ012", "TQ014"),
        "TQ002": ("TQ001", "TQ002", "TQ003", "TQ014"), "TQ004": ("TQ001", "TQ003", "TQ004", "TQ014"),
        "TQ006": ("TQ001", "TQ003", "TQ006", "TQ014"), "TQ007": ("TQ007",), "TQ008": ("TQ008",),
        "TQ009": ("TQ009",), "TQ010": ("TQ010",), "TQ011": ("TQ001", "TQ011", "TQ014"),
        "TQ013": ("TQ013",), "TQ014": ("TQ001", "TQ014"), "TQ015": ("TQ001", "TQ003", "TQ006", "TQ014", "TQ015"),
    }
    for rule, source in seeds:
        for index in range(1, 6):
            suffix = ".spec.ts" if rule == "TQ011" else ".py"
            cases.append(EvalCase(f"V01-{rule}-{index:02d}", source.replace("test_case", f"test_case_{index}"), rule, suffix, expected_rules=expected[rule]))
        for index in range(1, 6):
            suffix = ".spec.ts" if rule == "TQ011" else ".py"
            source = "test('valid', async ({ page }) => {\n await page.goto('/');\n expect(page).toBeDefined();\n});\n" if rule == "TQ011" else f"def test_valid_{rule.lower()}_{index}():\n    value = 1\n    assert value == 1\n"
            cases.append(EvalCase(f"V01-{rule}-NEG-{index:02d}", source, "", suffix, (rule,)))
    cases.extend([
        EvalCase("V01-ADV-01", "def test_comment():\n    # assert is prose\n    value = 1\n", "TQ001", ".py", ("TQ005",), ("TQ001", "TQ014")),
        EvalCase("V01-ADV-02", "def test_string():\n    note = 'assert is prose'\n    value = 1\n", "TQ001", ".py", ("TQ005",), ("TQ001", "TQ014")),
        EvalCase("V01-ADV-03", "def test_url():\n    url = 'https://x/#assert'\n    value = 1\n", "TQ001", ".py", ("TQ005",), ("TQ001", "TQ014")),
        EvalCase("V01-ADV-04", "def test_real_assert():\n    value = 1\n    assert value == 1\n", "", ".py", ("TQ001", "TQ014")),
        EvalCase("V01-ADV-05", "test('real', async () => {\n expect(true).toBe(true);\n});\n", "TQ005", ".spec.ts", expected_rules=("TQ005", "TQ014")),
    ])
    return cases


def run_cases(cases: list[EvalCase]) -> tuple[int, list[str]]:
    failures = []
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for case in cases:
            path = root / f"test_{case.id.lower()}{case.suffix}"
            path.write_text(case.source)
            result = ReviewService().review(ReviewRequest(repository=root))
            actual = {finding.rule_id for finding in result.findings}
            if case.expected_rule and case.expected_rule not in actual:
                failures.append(case.id)
            if case.expected_rules and actual != set(case.expected_rules):
                failures.append(case.id + "-unexpected")
            if any(rule in actual for rule in case.forbidden_rules):
                failures.append(case.id + "-forbidden")
            path.unlink()
    return len(cases), failures


def run_v01_evals() -> tuple[int, list[str]]:
    return run_cases(v01_cases())


def run_metrics(cases: list[EvalCase]) -> EvalMetrics:
    total, failures = run_cases(cases)
    true_positive = false_positive = false_negative = 0
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for case in cases:
            path = root / f"test_{case.id.lower()}{case.suffix}"
            path.write_text(case.source)
            actual = {finding.rule_id for finding in ReviewService().review(ReviewRequest(repository=root)).findings}
            expected = set(case.expected_rules or ((case.expected_rule,) if case.expected_rule else ()))
            true_positive += len(actual & expected)
            false_positive += len(actual - expected)
            false_negative += len(expected - actual)
            path.unlink()
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 1.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 1.0
    return EvalMetrics(total, round(precision, 4), round(recall, 4))
