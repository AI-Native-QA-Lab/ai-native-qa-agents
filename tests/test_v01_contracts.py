from pathlib import Path

from qa_agent.adapters import PlaywrightAdapter, PytestAdapter
from qa_agent.config import load_config
from qa_agent.model_runtime import ModelRequest, ModelResponse, ModelUsage, OpenAIProvider, StructuredOutputValidator
from qa_agent.semantic import SemanticReviewer, SemanticReviewRequest
from qa_agent.relevance import CodeChange, related_tests
from qa_agent.rules import RuleContext, RuleRegistry, RuleRunner


def test_rule_registry_exposes_all_v01_rules(tmp_path: Path) -> None:
    assert len(RuleRegistry.default().ids()) == 15


def test_rule_runner_returns_structured_match() -> None:
    context = RuleContext(path="test.py", code="def test_x():\n    pass\n", language="python", framework="pytest")
    matches = RuleRunner(RuleRegistry.default()).run(context)
    assert {item.rule_id for item in matches} >= {"TQ001", "TQ003", "TQ014"}


def test_adapter_extracts_structured_metadata(tmp_path: Path) -> None:
    path = tmp_path / "test_x.py"
    path.write_text("from unittest.mock import Mock\ndef test_x():\n    Mock()\n    assert 1 == 1\n")
    entity = PytestAdapter().discover_tests(path)[0]
    assert entity.assertions == 1
    assert entity.mocks == 1


def test_playwright_adapter_extracts_actions_and_expect(tmp_path: Path) -> None:
    path = tmp_path / "checkout.spec.ts"
    path.write_text("test('checkout', async ({ page }) => { await page.goto('/'); expect(page).toBeDefined(); });")
    entity = PlaywrightAdapter().discover_tests(path)[0]
    assert entity.assertions == 1
    assert "goto" in entity.actions


def test_config_loader_reads_yaml_subset(tmp_path: Path) -> None:
    path = tmp_path / ".qa-agent.yaml"
    path.write_text("gates:\n  fail_on:\n    - critical\n    - high\nrules:\n  TQ012:\n    severity: low\n")
    config = load_config(path)
    assert config.fail_on == ("critical", "high")
    assert config.rule_severity["TQ012"] == "low"


def test_config_loader_reads_yaml_ignore_paths(tmp_path: Path) -> None:
    path = tmp_path / ".qa-agent.yaml"
    path.write_text("ignore:\n  - rule: TQ012\n    paths:\n      - legacy/**\n")
    assert load_config(path).suppressed_rules == {"TQ012": ("legacy/**",)}


def test_model_runtime_validates_structured_response() -> None:
    request = ModelRequest(task_type="semantic_test_review", output_schema={"type": "object"})
    response = ModelResponse(provider="test", model="fake", structured_output={"issues": []}, usage=ModelUsage())
    assert StructuredOutputValidator().validate(request, response).structured_output == {"issues": []}


def test_semantic_reviewer_uses_provider_neutral_model_runtime() -> None:
    provider = OpenAIProvider("fake", lambda request: {"intent": "review", "oracle_quality": "weak", "confidence": 0.8, "issues": ["x"]})
    result = SemanticReviewer(provider).review(SemanticReviewRequest("test source", ()))
    assert result and result.issues == ("x",)
    assert provider.provider_name == "openai"


def test_semantic_reviewer_passes_bounded_evidence_context() -> None:
    seen = []
    provider = OpenAIProvider("fake", lambda request: seen.append(request) or {"issues": []})
    SemanticReviewer(provider).review(SemanticReviewRequest("test", ("TQ001",), "diff", "def checkout(): pass"))
    assert "RULE SIGNALS:\nTQ001" in seen[0].messages[0]["content"]
    assert "NEARBY PRODUCTION SYMBOL" in seen[0].messages[0]["content"]


def test_relevance_uses_documented_weights(tmp_path: Path) -> None:
    test = tmp_path / "test_checkout.py"
    test.write_text("from checkout import checkout\ndef test_checkout(): assert checkout()\n")
    score = related_tests(CodeChange("src/checkout.py"), [test])
    assert score.candidates and score.confidence == 1.0
