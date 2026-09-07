from pathlib import Path


def test_mapping_proposes_unverified_code_and_test_links(tmp_path: Path) -> None:
    from qa_agent.requirement_mapping import map_requirement
    from qa_agent.requirements import Requirement

    (tmp_path / "checkout.py").write_text("def checkout(): pass\n")
    (tmp_path / "test_checkout.py").write_text("def test_checkout(): pass\n")
    links = map_requirement(Requirement("REQ-1", "Checkout", "checkout", "markdown", "req.md"), ("EV-1",), tmp_path, 500, 1_000_000)

    assert {(item.target_kind, item.target_path, item.status) for item in links} == {
        ("code", "checkout.py", "unverified"),
        ("test", "test_checkout.py", "unverified"),
    }
