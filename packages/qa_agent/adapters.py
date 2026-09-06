"""Small v0.1 language and test-framework adapters."""
from __future__ import annotations

import ast
from dataclasses import dataclass, replace
from pathlib import Path
import re
from typing import Protocol


@dataclass(frozen=True)
class ParsedFile:
    path: Path
    source: str
    tree: ast.AST | None = None


@dataclass(frozen=True)
class Reference:
    name: str
    line: int


@dataclass(frozen=True)
class CodeEntity:
    name: str
    line: int


@dataclass(frozen=True)
class TestEntity:
    id: str
    path: str
    name: str
    framework: str
    language: str
    line: int
    end_line: int
    assertions: int = 0
    mocks: int = 0
    actions: tuple[str, ...] = ()
    skipped: bool = False


class LanguageAdapter(Protocol):
    name: str
    def parse_file(self, path: Path) -> ParsedFile: ...
    def find_functions(self, parsed: ParsedFile) -> list[CodeEntity]: ...
    def find_calls(self, parsed: ParsedFile) -> list[Reference]: ...
    def find_imports(self, parsed: ParsedFile) -> list[Reference]: ...


class TestFrameworkAdapter(Protocol):
    name: str
    def discover_tests(self, path: Path) -> list[TestEntity]: ...
    def parse_test(self, path: Path) -> ParsedFile: ...
    def extract_assertions(self, test: TestEntity) -> list[Reference]: ...
    def extract_mocks(self, test: TestEntity) -> list[Reference]: ...
    def extract_metadata(self, test: TestEntity) -> dict[str, object]: ...


class PythonLanguageAdapter:
    name = "python"

    def parse_file(self, path: Path) -> ParsedFile:
        source = path.read_text(encoding="utf-8", errors="replace")
        try:
            return ParsedFile(path, source, ast.parse(source))
        except SyntaxError:
            return ParsedFile(path, source)

    def find_functions(self, parsed: ParsedFile) -> list[CodeEntity]:
        return [CodeEntity(n.name, n.lineno) for n in ast.walk(parsed.tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))] if parsed.tree else []

    def find_calls(self, parsed: ParsedFile) -> list[Reference]:
        if not parsed.tree: return []
        return [Reference(n.func.id if isinstance(n.func, ast.Name) else n.func.attr, n.lineno) for n in ast.walk(parsed.tree) if isinstance(n, ast.Call) and isinstance(n.func, (ast.Name, ast.Attribute))]

    def find_imports(self, parsed: ParsedFile) -> list[Reference]:
        if not parsed.tree: return []
        refs: list[Reference] = []
        for node in ast.walk(parsed.tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)): refs.extend(Reference(alias.name, node.lineno) for alias in node.names)
        return refs


class TypeScriptLanguageAdapter:
    name = "typescript"

    def parse_file(self, path: Path) -> ParsedFile:
        return ParsedFile(path, path.read_text(encoding="utf-8", errors="replace"))

    def _refs(self, parsed: ParsedFile, pattern: str) -> list[Reference]:
        return [Reference(m.group(1), parsed.source[:m.start()].count("\n") + 1) for m in re.finditer(pattern, parsed.source)]

    def find_functions(self, parsed: ParsedFile) -> list[CodeEntity]:
        return [CodeEntity(item.name, item.line) for item in self._refs(parsed, r"(?:function|const|let)\s+([A-Za-z_$][\w$]*)\s*(?:=\s*)?(?:\(|=>)")]

    def find_calls(self, parsed: ParsedFile) -> list[Reference]: return self._refs(parsed, r"\b([A-Za-z_$][\w$]*)\s*\(")
    def find_imports(self, parsed: ParsedFile) -> list[Reference]: return self._refs(parsed, r"from\s+['\"]([^'\"]+)")


def _entity(path: Path, name: str, line: int, end_line: int) -> TestEntity:
    framework, language = ("pytest", "python") if path.suffix == ".py" else ("Playwright", "typescript")
    return TestEntity(f"{path}:{line}:{name}", str(path), name, framework, language, line, end_line)


def _source(test: TestEntity) -> str:
    return "\n".join(Path(test.path).read_text(encoding="utf-8", errors="replace").splitlines()[test.line - 1:test.end_line])


def _references(test: TestEntity, pattern: str) -> list[Reference]:
    source = _source(test)
    return [Reference(m.group(1) if m.groups() else "assertion", test.line + source[:m.start()].count("\n")) for m in re.finditer(pattern, source)]


class PytestAdapter:
    name = "pytest"

    def discover_tests(self, path: Path) -> list[TestEntity]:
        parsed = self.parse_test(path)
        if not parsed.tree: return []
        tests = []
        for node in ast.walk(parsed.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                test = _entity(path, node.name, min([node.lineno] + [item.lineno for item in node.decorator_list]), node.end_lineno or node.lineno)
                tests.append(replace(test, assertions=len(self.extract_assertions(test)), mocks=len(self.extract_mocks(test)), skipped="pytest.mark.skip" in _source(test) or "pytest.mark.xfail" in _source(test)))
        return tests

    def parse_test(self, path: Path) -> ParsedFile: return PythonLanguageAdapter().parse_file(path)
    def extract_assertions(self, test: TestEntity) -> list[Reference]: return _references(test, r"(?m)^\s*(assert)\b")
    def extract_mocks(self, test: TestEntity) -> list[Reference]: return _references(test, r"\b(Mock|MagicMock|patch)\s*\(")
    def extract_metadata(self, test: TestEntity) -> dict[str, object]: return {"skipped": test.skipped, "assertions": test.assertions, "mocks": test.mocks}


class PlaywrightAdapter:
    name = "Playwright"

    def discover_tests(self, path: Path) -> list[TestEntity]:
        source, tests = path.read_text(encoding="utf-8", errors="replace"), []
        for index, match in enumerate(re.finditer(r"(?:test|it)(?:\.skip)?\s*\(", source), 1):
            arrow = source.find("=>", match.end()); brace = source.find("{", arrow) if arrow >= 0 else -1
            end = self._closing_brace(source, brace) if brace >= 0 else None
            if end is None: continue
            test = _entity(path, f"playwright-test-{index}", source[:match.start()].count("\n") + 1, source[:end].count("\n") + 1)
            code = _source(test)
            tests.append(replace(test, assertions=len(self.extract_assertions(test)), mocks=len(self.extract_mocks(test)), actions=tuple(sorted(set(re.findall(r"page\.([A-Za-z]+)", code))),), skipped=".skip" in code))
        return tests

    def parse_test(self, path: Path) -> ParsedFile: return TypeScriptLanguageAdapter().parse_file(path)
    def extract_assertions(self, test: TestEntity) -> list[Reference]: return _references(test, r"\b(expect)\s*\(")
    def extract_mocks(self, test: TestEntity) -> list[Reference]: return _references(test, r"\b(jest\.mock|vi\.mock)\s*\(")
    def extract_metadata(self, test: TestEntity) -> dict[str, object]: return {"skipped": test.skipped, "assertions": test.assertions, "mocks": test.mocks, "actions": test.actions}

    @staticmethod
    def _closing_brace(source: str, start: int) -> int | None:
        depth, quote, escaped, line_comment, block_comment = 0, None, False, False, False
        for index, char in enumerate(source[start:], start):
            next_char = source[index + 1] if index + 1 < len(source) else ""
            if line_comment: line_comment = char != "\n"
            elif block_comment: block_comment = not (char == "*" and next_char == "/")
            elif quote:
                if escaped: escaped = False
                elif char == "\\": escaped = True
                elif char == quote: quote = None
            elif char in "'\"`": quote = char
            elif char == "/" and next_char == "/": line_comment = True
            elif char == "/" and next_char == "*": block_comment = True
            elif char == "{": depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0: return index
        return None


class AdapterRegistry:
    def __init__(self) -> None:
        self.languages: dict[str, LanguageAdapter] = {}
        self.frameworks: dict[str, TestFrameworkAdapter] = {}
        self.providers: dict[str, object] = {}
    def register_language(self, name: str, adapter: LanguageAdapter) -> None: self.languages[name] = adapter
    def register_framework(self, name: str, adapter: TestFrameworkAdapter) -> None: self.frameworks[name] = adapter
    def register_model_provider(self, name: str, adapter: object) -> None: self.providers[name] = adapter


def default_registry() -> AdapterRegistry:
    registry = AdapterRegistry()
    registry.register_language("python", PythonLanguageAdapter()); registry.register_language("typescript", TypeScriptLanguageAdapter())
    registry.register_framework("pytest", PytestAdapter()); registry.register_framework("Playwright", PlaywrightAdapter())
    return registry
