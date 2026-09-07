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


def test_mapping_stops_after_maximum_eligible_files(tmp_path: Path, monkeypatch) -> None:
    from qa_agent.requirement_mapping import map_requirement
    from qa_agent.requirements import Requirement

    for index in range(4):
        (tmp_path / f"other_{index}.py").write_text("value = 1\n")
    reads = []
    original = Path.read_bytes

    def counted_read(path: Path) -> bytes:
        reads.append(path.name)
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", counted_read)

    links = map_requirement(Requirement("REQ-1", "Checkout", "checkout", "markdown", "req.md"), ("EV-1",), tmp_path, 2, 1_000_000)

    assert links == []
    assert len(reads) == 2
