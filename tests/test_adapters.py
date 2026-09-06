from pathlib import Path
from qa_agent.adapters import PlaywrightAdapter, PytestAdapter, default_registry

def test_pytest_adapter_discovers_test_entity(tmp_path: Path) -> None:
    path = tmp_path / "test_example.py"; path.write_text("def test_ok():\n    assert True\n")
    assert PytestAdapter().discover_tests(path)[0].framework == "pytest"

def test_playwright_adapter_discovers_test_entity(tmp_path: Path) -> None:
    path = tmp_path / "page.spec.ts"; path.write_text("test('ok', async () => {});\n")
    assert PlaywrightAdapter().discover_tests(path)[0].framework == "Playwright"

def test_default_registry_has_v01_frameworks() -> None:
    assert set(default_registry().frameworks) == {"pytest", "Playwright"}


def test_default_registry_has_v01_language_adapters(tmp_path: Path) -> None:
    path = tmp_path / "service.py"; path.write_text("from app import thing\ndef run():\n    return thing()\n")
    language = default_registry().languages["python"]
    parsed = language.parse_file(path)
    assert [item.name for item in language.find_functions(parsed)] == ["run"]
    assert {item.name for item in language.find_imports(parsed)} == {"thing"}


def test_framework_contract_extracts_metadata(tmp_path: Path) -> None:
    path = tmp_path / "test_example.py"; path.write_text("from unittest.mock import Mock\ndef test_ok():\n    Mock()\n    assert True\n")
    adapter = PytestAdapter(); test = adapter.discover_tests(path)[0]
    assert adapter.extract_metadata(test) == {"skipped": False, "assertions": 1, "mocks": 1}
