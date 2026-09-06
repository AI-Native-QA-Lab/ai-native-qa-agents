from pathlib import Path
import subprocess
import hashlib

from qa_agent import review as review_module
from qa_agent.adapters import AdapterRegistry
from qa_agent.review import ReviewRequest, ReviewService
from qa_agent.semantic import SemanticReviewResult, SemanticReviewer


def test_review_produces_evidence_backed_findings_and_fails_gate(tmp_path: Path) -> None:
    test_file = tmp_path / "test_fake.py"
    test_file.write_text("def test_it():\n    assert True\n")

    result = ReviewService().review(ReviewRequest(repository=tmp_path))

    assert {finding.rule_id for finding in result.findings} >= {"TQ005", "TQ014"}
    assert result.decision == "fail"
    assert all(finding.evidence_ids for finding in result.findings)
    assert result.termination_reason == "COMPLETED"


def test_review_stops_with_budget_exhausted_without_fabricating_findings(tmp_path: Path) -> None:
    (tmp_path / "test_ok.py").write_text("def test_it():\n    assert 1 == 1\n")

    result = ReviewService().review(ReviewRequest(repository=tmp_path, max_actions=1))

    assert result.termination_reason == "BUDGET_EXHAUSTED"
    assert result.findings == []


def test_review_detects_playwright_sleep_and_screenshot_only_test(tmp_path: Path) -> None:
    (tmp_path / "checkout.spec.ts").write_text(
        "test('checkout', async ({ page }) => {\n"
        "  await page.waitForTimeout(1000);\n"
        "  await page.screenshot();\n"
        "});\n"
    )

    result = ReviewService().review(ReviewRequest(repository=tmp_path))

    assert {finding.rule_id for finding in result.findings} >= {"TQ011", "TQ012", "TQ014"}


def test_detect_uses_playwright_package_metadata(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text('{"devDependencies":{"@playwright/test":"1.0.0"}}')
    assert "Playwright" in ReviewService().detect(tmp_path)[1]


def test_json_and_sarif_are_machine_readable(tmp_path: Path) -> None:
    (tmp_path / "test_empty.py").write_text("def test_it():\n    pass\n")
    result = ReviewService().review(ReviewRequest(repository=tmp_path))

    assert '"findings"' in result.to_json()
    assert result.to_sarif()["version"] == "2.1.0"
    assert result.to_sarif()["runs"][0]["results"][0]["ruleId"] == "TQ001"
    payload = result.to_dict()
    assert payload["loop_trace"][0]["action_id"] == "detect"
    assert payload["budget"]["max_iterations"] == 6


def test_review_flags_skipped_and_todo_python_tests(tmp_path: Path) -> None:
    (tmp_path / "test_deferred.py").write_text(
        "import pytest\n\n"
        "@pytest.mark.skip\n"
        "def test_later():\n"
        "    # TODO: implement this\n"
        "    pass\n"
    )

    result = ReviewService().review(ReviewRequest(repository=tmp_path))

    assert {finding.rule_id for finding in result.findings} >= {"TQ002", "TQ004"}


def test_review_flags_excessive_mocks_duplicate_assertions_and_dead_assertion(tmp_path: Path) -> None:
    (tmp_path / "test_weak.py").write_text(
        "from unittest.mock import Mock\n\n"
        "def test_weak():\n"
        "    one, two, three = Mock(), Mock(), Mock()\n"
        "    assert 2 == 2\n"
        "    assert 2 == 2\n"
        "    return\n"
        "    assert False\n"
    )

    result = ReviewService().review(ReviewRequest(repository=tmp_path))

    assert {finding.rule_id for finding in result.findings} >= {"TQ007", "TQ008", "TQ009"}


def test_review_does_not_read_secret_named_files(tmp_path: Path) -> None:
    (tmp_path / ".env.production").write_text("API_KEY=not-for-review")
    (tmp_path / "test_ok.py").write_text("def test_it():\n    assert 2 == 2\n")

    result = ReviewService().review(ReviewRequest(repository=tmp_path))

    assert all(".env" not in evidence.path for evidence in result.evidence)


def test_review_excludes_secret_prefixes_and_binary_test_files(tmp_path: Path) -> None:
    (tmp_path / "credentials-prod").write_text("secret")
    (tmp_path / "test_binary.py").write_bytes(b"def test_bad():\x00assert True")
    (tmp_path / "test_ok.py").write_text("def test_ok():\n    assert 2 == 2\n")

    result = ReviewService().review(ReviewRequest(repository=tmp_path))

    assert all("credentials-prod" not in evidence.path and "test_binary" not in evidence.path for evidence in result.evidence)


def test_comment_assertion_is_not_treated_as_test_assertion(tmp_path: Path) -> None:
    (tmp_path / "test_comment.py").write_text("def test_comment():\n    # assert this is prose\n    value = 1\n")
    result = ReviewService().review(ReviewRequest(repository=tmp_path))
    assert {finding.rule_id for finding in result.findings} >= {"TQ001", "TQ014"}


def test_review_flags_hardcoded_success_without_a_behavior_check(tmp_path: Path) -> None:
    (tmp_path / "test_happy.py").write_text(
        "def test_happy_path():\n"
        "    result = {'status': 'success'}\n"
        "    assert result['status'] == 'success'\n"
    )

    result = ReviewService().review(ReviewRequest(repository=tmp_path))

    assert "TQ013" in {finding.rule_id for finding in result.findings}


def test_rule_configuration_can_override_severity_and_suppress_path(tmp_path: Path) -> None:
    (tmp_path / "legacy").mkdir()
    (tmp_path / "legacy" / "test_sleep.py").write_text("def test_sleep():\n    import time\n    time.sleep(1)\n")
    (tmp_path / "test_sleep.py").write_text("def test_sleep():\n    import time\n    time.sleep(1)\n")

    result = ReviewService().review(
        ReviewRequest(repository=tmp_path, rule_severity={"TQ012": "low"}, suppressed_rules={"TQ012": ("legacy/*",)})
    )

    sleeps = [finding for finding in result.findings if finding.rule_id == "TQ012"]
    assert len(sleeps) == 1
    assert sleeps[0].severity == "low"


def test_diff_relevance_reports_changed_source_without_candidate_test(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "orders.py").write_text("def create_order():\n    return 1\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.email=qa@example.test", "-c", "user.name=QA", "commit", "-m", "initial"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "orders.py").write_text("def create_order():\n    return 2\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "-c", "user.email=qa@example.test", "-c", "user.name=QA", "commit", "-m", "change"], cwd=tmp_path, check=True, capture_output=True)
    result = ReviewService().review(ReviewRequest(repository=tmp_path, base="HEAD~1"))

    assert result.coverage_gaps == [{"path": "orders.py", "confidence": 0.2, "status": "unverified"}]


def test_review_returns_insufficient_evidence_for_an_unknown_base(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "test_ok.py").write_text("def test_ok():\n    value = 1\n    assert value == 1\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.email=qa@example.test", "-c", "user.name=QA", "commit", "-m", "initial"], cwd=tmp_path, check=True, capture_output=True)

    result = ReviewService().review(ReviewRequest(repository=tmp_path, base="unknown-base"))

    assert result.decision == "incomplete"
    assert result.termination_reason == "INSUFFICIENT_EVIDENCE"


def test_base_scopes_rule_review_to_changed_test_files(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "test_legacy.py").write_text("def test_legacy():\n    assert True\n")
    (tmp_path / "test_changed.py").write_text("def test_changed():\n    value = 1\n    assert value == 1\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.email=qa@example.test", "-c", "user.name=QA", "commit", "-m", "initial"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "test_changed.py").write_text("def test_changed():\n    value = 2\n    assert value == 2\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.email=qa@example.test", "-c", "user.name=QA", "commit", "-m", "change"], cwd=tmp_path, check=True, capture_output=True)

    result = ReviewService().review(ReviewRequest(repository=tmp_path, base="HEAD~1"))

    assert result.decision == "pass"
    assert result.findings == []


def test_relevance_score_exposes_change_and_candidate_metadata(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "orders.py").write_text("def create_order():\n    return 1\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "-c", "user.email=qa@example.test", "-c", "user.name=QA", "commit", "-m", "initial"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "orders.py").write_text("def create_order():\n    return 2\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "-c", "user.email=qa@example.test", "-c", "user.name=QA", "commit", "-m", "change"], cwd=tmp_path, check=True, capture_output=True)
    result = ReviewService().review(ReviewRequest(repository=tmp_path, base="HEAD~1"))
    assert result.changes[0].path == "orders.py"
    assert result.changes[0].confidence == 0.2


def test_evidence_hashes_original_source_not_redacted_context(tmp_path: Path) -> None:
    source = "def test_secret():\n    api_key = 'secret-value'\n    assert True\n"
    (tmp_path / "test_secret.py").write_text(source)

    result = ReviewService().review(ReviewRequest(repository=tmp_path))

    evidence = next(item for item in result.evidence if item.type == "static_rule_match")
    assert evidence.content_hash == "sha256:" + hashlib.sha256(source.rstrip().encode()).hexdigest()


def test_adapter_discovery_controls_which_tests_are_reviewed(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "test_fake.py").write_text("def test_it():\n    assert True\n")
    registry = AdapterRegistry()

    class EmptyAdapter:
        def discover_tests(self, path: Path) -> list[object]:
            return []

    registry.register_framework("pytest", EmptyAdapter())
    registry.register_framework("Playwright", EmptyAdapter())
    monkeypatch.setattr(review_module, "default_registry", lambda: registry)

    result = ReviewService().review(ReviewRequest(repository=tmp_path))

    assert result.findings == []


def test_semantic_review_stops_before_provider_when_model_budget_is_exhausted(tmp_path: Path) -> None:
    (tmp_path / "test_ok.py").write_text("def test_ok():\n    assert 1 == 1\n")
    calls = []

    class Provider:
        name = "test"

        def structured_review(self, request):
            calls.append(request)
            return SemanticReviewResult("intent", "good", 1.0)

    result = ReviewService().review(
        ReviewRequest(repository=tmp_path, semantic_reviewer=SemanticReviewer(Provider()), max_model_calls=0)
    )

    assert calls == []
    assert result.termination_reason == "BUDGET_EXHAUSTED"


def test_semantic_findings_remain_unverified_with_source_evidence(tmp_path: Path) -> None:
    (tmp_path / "test_ok.py").write_text("def test_ok():\n    assert 1 == 1\n")

    class Provider:
        name = "test"

        def structured_review(self, request):
            return SemanticReviewResult("intent", "weak", 0.8, issues=("Missing boundary case.",))

    result = ReviewService().review(
        ReviewRequest(repository=tmp_path, semantic_reviewer=SemanticReviewer(Provider()), max_model_calls=1)
    )

    finding = next(item for item in result.findings if item.rule_id == "SEM001")
    evidence = next(item for item in result.evidence if item.id == finding.evidence_ids[0])
    assert finding.verification_status == "unverified"
    assert evidence.status == "unverified"
    assert not Path(evidence.path).is_absolute()


def test_semantic_context_keeps_production_source_out_of_provider_input(tmp_path: Path) -> None:
    (tmp_path / "checkout.py").write_text("def checkout():\n    api_key = 'do-not-send'\n")
    (tmp_path / "test_checkout.py").write_text("def test_checkout():\n    value = 1\n    assert value == 1\n")
    seen = []

    class Provider:
        name = "test"
        def structured_review(self, request):
            seen.append(request)
            return SemanticReviewResult("intent", "good", 1.0)

    ReviewService().review(ReviewRequest(repository=tmp_path, semantic_reviewer=SemanticReviewer(Provider()), max_model_calls=1))

    assert seen and seen[0].nearby_production_symbol == "checkout.py: checkout"
    assert "do-not-send" not in seen[0].nearby_production_symbol


def test_review_does_not_pass_when_repository_is_missing(tmp_path: Path) -> None:
    result = ReviewService().review(ReviewRequest(repository=tmp_path / "missing"))

    assert result.decision == "incomplete"
    assert result.termination_reason == "INSUFFICIENT_EVIDENCE"
    assert result.gate is not None
    assert result.gate.risk == "unknown"


def test_playwright_adapter_keeps_braces_inside_strings_in_test_body(tmp_path: Path) -> None:
    (tmp_path / "brace.spec.ts").write_text(
        "test('brace', async () => {\n"
        "  const value = '}';\n"
        "  expect(value).toBe('}');\n"
        "});\n"
    )

    result = ReviewService().review(ReviewRequest(repository=tmp_path))

    assert "TQ001" not in {item.rule_id for item in result.findings}
