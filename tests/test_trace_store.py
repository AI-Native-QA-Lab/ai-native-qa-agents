from pathlib import Path


def test_trace_store_round_trips_requirement_and_link(tmp_path: Path) -> None:
    from qa_agent.requirements import Requirement, TraceLink
    from qa_agent.review import Evidence
    from qa_agent.trace_store import SQLiteTraceStore

    store = SQLiteTraceStore(tmp_path / "trace.db")
    requirement = Requirement("REQ-1", "Checkout", "body", "markdown", "req.md")
    link = TraceLink("REQ-1", "code", "checkout.py", "checkout", ("EV-1",), "unverified", 0.2)
    store.save_requirement(requirement, [Evidence("EV-1", "requirement", "req.md", 1, 1, "sha256:x")])
    store.replace_links("REQ-1", [link])

    assert store.get_requirement("REQ-1") == requirement
    assert store.get_links("REQ-1") == [link]
