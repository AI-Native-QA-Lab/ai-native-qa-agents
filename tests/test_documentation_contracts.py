from pathlib import Path


def test_v04_pack_lists_the_frozen_contracts() -> None:
    root = Path(__file__).parents[1]
    paths = sorted((root / "docs" / "v0.4-engineering").glob("*.md"))
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    for marker in (
        "TestEffectivenessContext",
        "MutationTraceLink",
        "observation_status",
        "max_report_bytes",
        "report schema 1",
        "incomplete",
        "unverified",
        "allow_dirty",
    ):
        assert marker in text


def test_v03_pack_mentions_explicit_legacy_import() -> None:
    root = Path(__file__).parents[1]
    text = "\n".join(
        (root / "docs" / "v0.3-engineering" / name).read_text(encoding="utf-8")
        for name in ("README.md", "DOMAIN_MODEL.md")
    )
    assert "v0.4" in text
    assert "legacy" in text
    assert "Business Oracle" in text


def test_v04_markdown_fences_are_balanced() -> None:
    root = Path(__file__).parents[1]
    for path in (root / "docs" / "v0.4-engineering").glob("*.md"):
        assert path.read_text(encoding="utf-8").count("```") % 2 == 0
