"""Deterministic v0.1 rule contracts and registry-backed rule runner."""

from __future__ import annotations

from dataclasses import dataclass
import re
from collections.abc import Callable


@dataclass(frozen=True)
class RuleContext:
    path: str
    code: str
    language: str
    framework: str
    assertion: bool = False


@dataclass(frozen=True)
class RuleMatch:
    rule_id: str
    severity: str
    title: str
    message: str


Predicate = Callable[[RuleContext], bool]


class Rule:
    def __init__(self, rule_id: str, severity: str, title: str, message: str, predicate: Predicate) -> None:
        self.id, self.severity, self.title, self.message, self._predicate = rule_id, severity, title, message, predicate

    def evaluate(self, context: RuleContext) -> RuleMatch | None:
        return RuleMatch(self.id, self.severity, self.title, self.message) if self._predicate(context) else None


def _python(context: RuleContext) -> bool:
    return context.language == "python"


def _has(pattern: str, language: str | None = None, flags: int = 0) -> Predicate:
    return lambda context: (language is None or context.language == language) and bool(re.search(pattern, context.code, flags))


def _no_assertion(context: RuleContext) -> bool:
    return not context.assertion if _python(context) else not bool(re.search(r"\bexpect\s*\(", context.code))


def _empty(context: RuleContext) -> bool:
    if _python(context):
        return bool(re.search(r"^\s*(pass|\.\.\.)\s*$", "\n".join(context.code.splitlines()[1:]), re.MULTILINE))
    return not bool(re.search(r"=>\s*\{\s*[^}]*\S", context.code, re.DOTALL))


def _always_pass(context: RuleContext) -> bool:
    pattern = r"^\s*assert\s+(?:True|1\s*==\s*1)\s*$" if _python(context) else r"^\s*expect\s*\(\s*true\s*\)\.toBe\s*\(\s*true\s*\)\s*;?\s*$"
    return bool(re.search(pattern, context.code, re.MULTILINE))


def _swallowed_exception(context: RuleContext) -> bool:
    if _python(context):
        return bool(re.search(r"try:[\s\S]*?except\s+", context.code)) and not bool(re.search(r"except[\s\S]*(?:assert|raise|fail)", context.code))
    return bool(re.search(r"catch\s*\([^)]*\)\s*\{\s*\}", context.code, re.DOTALL))


def _excessive_mocks(context: RuleContext) -> bool:
    if _python(context):
        mocks = len(re.findall(r"\b(?:Mock|MagicMock|patch)\s*\(", context.code))
        return mocks >= 3 and mocks >= len(re.findall(r"\bassert\b", context.code))
    return len(re.findall(r"\b(?:jest\.mock|vi\.mock)\s*\(", context.code)) >= 3


def _duplicate_assertion(context: RuleContext) -> bool:
    pattern = r"^\s*(assert\s+.+)$" if _python(context) else r"^\s*(expect\s*\(.+)$"
    values = re.findall(pattern, context.code, re.MULTILINE)
    return len(values) != len(set(values))


def _unreachable_assertion(context: RuleContext) -> bool:
    return bool(re.search(r"\b(?:return|raise)\b[^\n]*\n\s*assert\b" if _python(context) else r"\breturn\b[^\n]*;[\s\S]*\bexpect\s*\(", context.code))


def _status_only(context: RuleContext) -> bool:
    if _python(context):
        return bool(re.search(r"assert\s+\w+\.status_code", context.code)) and len(re.findall(r"\bassert\b", context.code)) == 1
    return bool(re.search(r"expect\s*\([^\n]*status\s*\(\s*\)\s*\)\s*\.toBe", context.code)) and len(re.findall(r"\bexpect\s*\(", context.code)) == 1


def _hardcoded_success(context: RuleContext) -> bool:
    if _python(context):
        return bool(re.search(r"=\s*\{[^\n]*['\"](?:success|ok)['\"][^\n]*\}\s*\n\s*assert\s+.+==\s*['\"](?:success|ok)['\"]", context.code))
    return bool(re.search(r"const\s+\w+\s*=\s*['\"](?:success|ok)['\"]", context.code) and re.search(r"expect\([^\n]+\)\.to(?:Be|Equal)\(['\"](?:success|ok)['\"]", context.code))


def _no_observable_outcome(context: RuleContext) -> bool:
    return _no_assertion(context) or _always_pass(context)


def _rules() -> tuple[Rule, ...]:
    return (
        Rule("TQ001", "high", "No assertion", "Test has no explicit or framework assertion.", _no_assertion),
        Rule("TQ002", "medium", "Skipped test", "Test is marked skip or xfail.", _has(r"@(?:pytest\.)?mark\.(?:skip|xfail)\b|\b(?:test|it)\.skip\b")),
        Rule("TQ003", "high", "Empty test", "Test body is only a placeholder.", _empty),
        Rule("TQ004", "medium", "Todo test", "Test contains an unfinished placeholder.", _has(r"\b(?:TODO|FIXME|NotImplemented)\b")),
        Rule("TQ005", "critical", "Always-pass assertion", "Assertion is constant and cannot verify behavior.", _always_pass),
        Rule("TQ006", "high", "Swallowed exception", "Test catches an exception without making failure observable.", _swallowed_exception),
        Rule("TQ007", "medium", "Excessive mocking", "Mock count is high relative to behavior assertions.", _excessive_mocks),
        Rule("TQ008", "high", "Unreachable assertion", "Assertion follows return or raise in the same block.", _unreachable_assertion),
        Rule("TQ009", "low", "Duplicated assertion", "Repeated assertion adds no verification value.", _duplicate_assertion),
        Rule("TQ010", "medium", "Status-only API assertion", "Test only asserts the response status.", _status_only),
        Rule("TQ011", "medium", "Screenshot-only E2E test", "Screenshot is not a business assertion.", lambda c: c.language == "typescript" and "page.screenshot" in c.code and not bool(re.search(r"\bexpect\s*\(", c.code))),
        Rule("TQ012", "medium", "Sleep-based test", "Fixed sleep is used instead of a condition.", lambda c: bool(re.search(r"\btime\.sleep\s*\(", c.code)) if _python(c) else "page.waitForTimeout" in c.code),
        Rule("TQ013", "low", "Hardcoded success path", "Test constructs its own successful result instead of observing behavior.", _hardcoded_success),
        Rule("TQ014", "high", "No observable outcome", "Test has no meaningful observable outcome.", _no_observable_outcome),
        Rule("TQ015", "high", "Broad exception catch", "Test catches a broad exception type.", lambda c: bool(re.search(r"except\s+(?:Exception|BaseException)\b", c.code)) if _python(c) else bool(re.search(r"catch\s*\([^)]*(?:error|e|err)[^)]*\)\s*\{\s*\}", c.code, re.DOTALL))),
    )


class RuleRegistry:
    def __init__(self, rules: tuple[Rule, ...]) -> None:
        self.rules = rules

    def ids(self) -> tuple[str, ...]:
        return tuple(rule.id for rule in self.rules)

    @classmethod
    def default(cls) -> "RuleRegistry":
        return cls(_rules())


class RuleRunner:
    def __init__(self, registry: RuleRegistry) -> None:
        self.registry = registry

    def run(self, context: RuleContext) -> list[RuleMatch]:
        return [match for rule in self.registry.rules if (match := rule.evaluate(context)) is not None]
