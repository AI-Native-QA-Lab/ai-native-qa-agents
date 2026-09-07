from pathlib import Path

import pytest


def test_markdown_adapter_extracts_title_criteria_and_lines(tmp_path: Path) -> None:
    from qa_agent.requirement_adapters import MarkdownRequirementAdapter

    path = tmp_path / "checkout.md"
    path.write_text("# Checkout\n\n## Acceptance Criteria\n- Payment succeeds\n- Declined card is shown\n")
    source = MarkdownRequirementAdapter().fetch(path)

    assert source.title == "Checkout"
    assert source.criterion_lines == ((4, "Payment succeeds"), (5, "Declined card is shown"))


def test_github_adapter_reads_local_payload_without_network(tmp_path: Path) -> None:
    from qa_agent.requirement_adapters import GitHubIssueAdapter

    path = tmp_path / "issue.json"
    path.write_text('{"number":123,"title":"Checkout","body":"## Acceptance Criteria\\n- Pay","html_url":"https://example.test/123"}')

    source = GitHubIssueAdapter().fetch("GH-123", path)

    assert (source.id, source.source_kind, source.source_ref) == ("GH-123", "github_issue", "https://example.test/123")


def test_adapter_rejects_secret_binary_and_malformed_inputs(tmp_path: Path) -> None:
    from qa_agent.requirement_adapters import MarkdownRequirementAdapter, RequirementAccessDenied, RequirementBackendError

    secret = tmp_path / ".env.secret"
    secret.write_text("# secret")
    binary = tmp_path / "binary.md"
    binary.write_bytes(b"# x\x00")

    with pytest.raises(RequirementAccessDenied):
        MarkdownRequirementAdapter().fetch(secret)
    with pytest.raises(RequirementBackendError):
        MarkdownRequirementAdapter().fetch(binary)
