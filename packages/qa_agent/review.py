"""The v0.1 deterministic review loop and its public API."""

from __future__ import annotations

import ast
import contextvars
import io
import tokenize
import hashlib
import json
import fnmatch
import re
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .runtime import AgentState, ExecutionBudget, LoopTrace, Observation, TerminationPolicy
from .runtime_services import ActionExecutor, Evaluator, EvidenceVerifier, Observer, ReviewPlanner
from .adapters import default_registry
from .context import build_semantic_context
from .semantic import SemanticReviewer
from .rules import RuleContext, RuleRegistry, RuleRunner
from .relevance import CodeChange, RelevanceScore, related_tests


SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
ACTIVE_REQUEST: contextvars.ContextVar["ReviewRequest | None"] = contextvars.ContextVar("active_request", default=None)


@dataclass
class Evidence:
    id: str
    type: str
    path: str
    line_start: int
    line_end: int
    content_hash: str
    status: str = "verified"
    provider: str = "repository"
    extractor: str = "static-rule"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    loop_iteration: int = 0


@dataclass
class Finding:
    id: str
    rule_id: str
    severity: str
    title: str
    message: str
    path: str
    line: int
    evidence_ids: list[str]
    verification_status: str = "verified"
    source: str = "static-rule"
    confidence: float = 1.0

@dataclass
class GateResult:
    decision: str
    fail_on: list[str]
    finding_count: int
    evidence_completeness: float
    risk: str


@dataclass
class ReviewRequest:
    repository: Path
    base: str | None = None
    fail_on: tuple[str, ...] = ("critical",)
    max_actions: int = 6
    max_files: int = 500
    max_file_bytes: int = 1_000_000
    max_tool_calls: int = 32
    max_model_calls: int = 0
    timeout_seconds: int = 60
    rule_severity: dict[str, str] = field(default_factory=dict)
    suppressed_rules: dict[str, tuple[str, ...]] = field(default_factory=dict)
    semantic_reviewer: SemanticReviewer | None = None


@dataclass
class ReviewResult:
    findings: list[Finding] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    coverage_gaps: list[dict[str, Any]] = field(default_factory=list)
    changes: list[RelevanceScore] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)
    decision: str = "pass"
    termination_reason: str = "COMPLETED"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    gate: GateResult | None = None
    observations: list[dict[str, Any]] = field(default_factory=list)
    loop_trace: list[LoopTrace] = field(default_factory=list)
    budget: ExecutionBudget = field(default_factory=ExecutionBudget)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1",
            "findings": [asdict(item) for item in self.findings],
            "evidence": [asdict(item) for item in self.evidence],
            "languages": self.languages,
            "frameworks": self.frameworks,
            "coverage_gaps": self.coverage_gaps,
            "changes": [asdict(item) for item in self.changes],
            "trace": self.trace,
            "decision": self.decision,
            "termination_reason": self.termination_reason,
            "created_at": self.created_at,
            "gate": asdict(self.gate) if self.gate else None,
            "observations": self.observations,
            "loop_trace": [asdict(item) for item in self.loop_trace],
            "budget": asdict(self.budget),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_sarif(self) -> dict[str, Any]:
        rules = {}
        results = []
        for finding in self.findings:
            rules.setdefault(finding.rule_id, {"id": finding.rule_id, "name": finding.title})
            results.append({
                "ruleId": finding.rule_id,
                "level": {"critical": "error", "high": "error", "medium": "warning", "low": "note"}[finding.severity],
                "message": {"text": finding.message},
                "locations": [{"physicalLocation": {"artifactLocation": {"uri": finding.path}, "region": {"startLine": finding.line}}}],
            })
        return {"version": "2.1.0", "$schema": "https://json.schemastore.org/sarif-2.1.0.json", "runs": [{"tool": {"driver": {"name": "qa-agent", "rules": list(rules.values())}}, "results": results}]}


class ReviewService:
    """Runs only predefined actions; no model or tool call is implicit."""

    def review(self, request: ReviewRequest) -> ReviewResult:
        token = ACTIVE_REQUEST.set(request)
        try:
            return self._review(request)
        finally:
            ACTIVE_REQUEST.reset(token)

    def _review(self, request: ReviewRequest) -> ReviewResult:
        root = request.repository.resolve()
        result = ReviewResult()
        if not root.is_dir():
            result.decision = "incomplete"
            result.termination_reason = "INSUFFICIENT_EVIDENCE"
            result.gate = GateResult("incomplete", list(request.fail_on), 0, 0.0, "unknown")
            return result
        state = AgentState(task_id=f"review-{id(result)}", goal="review test quality")
        budget = ExecutionBudget(max_iterations=request.max_actions, max_tool_calls=request.max_tool_calls, max_model_calls=request.max_model_calls, timeout_seconds=request.timeout_seconds)
        result.budget = budget
        state.budget = budget
        termination = TerminationPolicy()
        executor, observer, evaluator, verifier = ActionExecutor(), Observer(), Evaluator(), EvidenceVerifier()
        started = time.monotonic()
        tool_calls = 0
        model_calls = 0
        files: list[Path] = []
        diff_context = ""
        registry = default_registry()
        actions = list(ReviewPlanner().plan())
        if request.semantic_reviewer and request.semantic_reviewer.provider:
            actions.insert(-1, "semantic-review")
        state.plan = actions.copy()
        state.pending_actions = actions.copy()
        for index, action in enumerate(actions, 1):
            if time.monotonic() - started > budget.timeout_seconds:
                result.termination_reason, result.decision = "TIMEOUT", "incomplete"
                return result
            state.iteration = index
            reason = termination.should_stop(state, budget)
            if reason:
                result.termination_reason = reason
                result.decision = "incomplete"
                return result
            result.trace.append(action)
            state.pending_actions.remove(action)
            state.completed_actions.append(action)
            if action in {"inspect-diff", "discover-tests", "run-rules"}:
                tool_calls += 1
                if tool_calls > budget.max_tool_calls:
                    result.termination_reason, result.decision = "BUDGET_EXHAUSTED", "incomplete"
                    return result
            observation = executor.execute(index, action)
            observer.record(state, observation)
            state.traces.append(LoopTrace(index, action, "running", observation.id))
            result.loop_trace.append(state.traces[-1])
            result.observations.append(asdict(observation))
            if action == "detect":
                result.languages, result.frameworks = self.detect(root)
            elif action == "inspect-diff":
                diff_context = self._diff_evidence(root, request.base, result)
            elif action == "discover-tests":
                files = self._test_files(root, request)
            elif action == "run-rules":
                for path in files:
                    framework = "pytest" if path.suffix == ".py" else "Playwright"
                    for test in registry.frameworks[framework].discover_tests(path):
                        self._review_test(root, path, test.line, test.end_line, test.language, result, request)
                if result.observations:
                    result.observations[-1]["evidence_ids"] = [item.id for item in result.evidence]
                    state.observations[-1].evidence_ids = [item.id for item in result.evidence]
            elif action == "semantic-review":
                for path in files:
                    if model_calls >= budget.max_model_calls:
                        result.termination_reason, result.decision = "BUDGET_EXHAUSTED", "incomplete"
                        return result
                    model_calls += 1
                    source = path.read_text(encoding="utf-8", errors="replace")[:20_000]
                    relative = str(path.relative_to(root))
                    signals = [finding.rule_id for finding in result.findings if finding.path == relative]
                    semantic = request.semantic_reviewer.review(build_semantic_context(source, signals, diff_context, self._nearby_production_symbol(root, path)))
                    if semantic and semantic.issues:
                        evidence = self._evidence(result, "ai_semantic_review", Path(path.relative_to(root)), 1, 1, source, status="unverified")
                        for issue in semantic.issues:
                            result.findings.append(Finding(f"F-{len(result.findings)+1:03d}", "SEM001", "medium", "Semantic review", issue, str(path.relative_to(root)), 1, [evidence.id], semantic.verification_status, "semantic-reviewer"))
            elif action == "verify-and-gate":
                self._find_related_test_gaps(root, request.base, files, result)
                evidence_ids = {item.id for item in result.evidence}
                for finding in result.findings:
                    if finding.source == "static-rule":
                        finding.verification_status = verifier.verify(finding.evidence_ids, evidence_ids)
                result.findings.sort(key=lambda item: (SEVERITY_RANK[item.severity], item.rule_id, item.path, item.line))
                completeness = sum(bool(f.evidence_ids) for f in result.findings) / len(result.findings) if result.findings else 1.0
                if not evaluator.sufficient(len(result.evidence), len(result.findings)):
                    result.termination_reason, result.decision = "INSUFFICIENT_EVIDENCE", "incomplete"
                    return result
                result.decision = "fail" if any(item.severity in request.fail_on for item in result.findings) else "pass"
                result.gate = GateResult(result.decision, list(request.fail_on), len(result.findings), completeness, "high" if result.decision == "fail" else "low")
            if result.termination_reason != "COMPLETED":
                return result
        return result

    def detect(self, root: Path) -> tuple[list[str], list[str]]:
        ignored = {".git", ".venv", "node_modules", "dist", "build", "__pycache__"}
        names = [item.name for item in root.rglob("*") if item.is_file() and not any(part in ignored for part in item.parts)]
        python = any(name.endswith(".py") for name in names)
        typescript = any(name.endswith((".ts", ".tsx", ".js", ".jsx")) for name in names)
        pytest = any(name.startswith("test_") and name.endswith(".py") for name in names) or (root / "pytest.ini").exists()
        package = (root / "package.json").read_text(encoding="utf-8", errors="replace") if (root / "package.json").exists() else ""
        playwright = any(name.endswith((".spec.ts", ".spec.js", ".test.ts", ".test.js")) for name in names) or any(name.startswith("playwright.config.") for name in names) or "@playwright/test" in package
        return ([name for name, enabled in (("Python", python), ("TypeScript", typescript)) if enabled], [name for name, enabled in (("pytest", pytest), ("Playwright", playwright)) if enabled])

    def _test_files(self, root: Path, request: ReviewRequest) -> list[Path]:
        candidates = []
        ignored = {".git", ".venv", "node_modules", "dist", "build", "__pycache__"}
        secret_names = {"credentials", "secrets"}
        for path in root.rglob("*"):
            if any(part in ignored for part in path.parts) or path.name == ".env" or path.name.startswith(".env.") or path.name in secret_names or path.name.startswith(("credentials", "secrets")) or path.suffix in {".pem", ".key"} or not path.is_file() or path.stat().st_size > request.max_file_bytes:
                continue
            try:
                if b"\x00" in path.read_bytes()[:4096]:
                    continue
            except OSError:
                continue
            name = path.name
            if name.startswith("test_") and name.endswith(".py") or name.endswith("_test.py") or name.endswith((".spec.ts", ".spec.js", ".test.ts", ".test.js")):
                candidates.append(path)
        return sorted(candidates)[:request.max_files]

    def _diff_evidence(self, root: Path, base: str | None, result: ReviewResult) -> str:
        if not base or not (root / ".git").exists():
            return ""
        try:
            completed = subprocess.run(["git", "diff", "--no-ext-diff", "--no-textconv", "--unified=0", f"{base}...HEAD"], cwd=root, text=True, capture_output=True, check=False, timeout=10)
            working = subprocess.run(["git", "diff", "--no-ext-diff", "--no-textconv", "--unified=0", "HEAD"], cwd=root, text=True, capture_output=True, check=False, timeout=10)
        except subprocess.TimeoutExpired:
            result.termination_reason = "TIMEOUT"
            result.decision = "incomplete"
            return ""
        completed.stdout += working.stdout
        if completed.returncode == 0 and completed.stdout:
            self._evidence(result, "git_diff", Path("."), 1, 1, completed.stdout)
        return completed.stdout[:20_000]

    def _nearby_production_symbol(self, root: Path, test_path: Path) -> str:
        """Return only a same-stem production file; never send a repository dump."""
        stem = test_path.stem.replace("test_", "").replace(".spec", "").replace(".test", "")
        for path in root.rglob("*"):
            if path.is_file() and path.stem == stem and path != test_path and path.suffix in {".py", ".ts", ".tsx", ".js"}:
                return path.read_text(encoding="utf-8", errors="replace")[:8_000]
        return ""

    def _find_related_test_gaps(self, root: Path, base: str | None, tests: list[Path], result: ReviewResult) -> None:
        """Report candidate gaps only; this heuristic never becomes a blocking finding."""
        if not base or not (root / ".git").exists():
            return
        try:
            changed = subprocess.run(["git", "diff", "--no-ext-diff", "--no-textconv", "--name-only", f"{base}...HEAD"], cwd=root, text=True, capture_output=True, check=False, timeout=10)
            working = subprocess.run(["git", "diff", "--no-ext-diff", "--no-textconv", "--name-only", "HEAD"], cwd=root, text=True, capture_output=True, check=False, timeout=10)
        except subprocess.TimeoutExpired:
            result.termination_reason = "TIMEOUT"
            result.decision = "incomplete"
            return
        changed.stdout += working.stdout
        if changed.returncode:
            return
        for name in sorted(set(filter(None, changed.stdout.splitlines()))):
            path = Path(name)
            if path.name.startswith("test_") or path.name.endswith(("_test.py", ".spec.ts", ".test.ts", ".spec.js", ".test.js")):
                continue
            score = related_tests(CodeChange(name), tests)
            if not score.candidates:
                result.changes.append(score)
                result.coverage_gaps.append({"path": name, "confidence": score.confidence, "status": "unverified"})

    def _review_test(self, root: Path, path: Path, start: int, end: int, language: str, result: ReviewResult, request: ReviewRequest) -> None:
        source = path.read_text(encoding="utf-8", errors="replace")
        relative = str(path.relative_to(root))
        code = "\n".join(source.splitlines()[start - 1:end])
        if language == "python":
            try:
                tree = ast.parse(code)
            except SyntaxError:
                return
            clean = self._strip_python_comments(code)
            if re.search(r"\b(?:TODO|NotImplemented)\b", code):
                clean += "\nTODO"
            assertion = any(isinstance(item, ast.Assert) for item in ast.walk(tree)) or any(isinstance(item, ast.Call) and isinstance(item.func, ast.Attribute) and item.func.attr == "raises" for item in ast.walk(tree))
            self._python_rules(result, relative, start, end, clean, request, assertion)
        else:
            self._typescript_rules(result, relative, start, end, code, request)

    def _strip_python_comments(self, source: str) -> str:
        try:
            return tokenize.untokenize(token for token in tokenize.generate_tokens(io.StringIO(source).readline) if token.type != tokenize.COMMENT)
        except (IndentationError, tokenize.TokenError):
            return source

    def _python_rules(self, result: ReviewResult, path: str, start: int, end: int, code: str, request: ReviewRequest, assertion: bool) -> None:
        for match in RuleRunner(RuleRegistry.default()).run(RuleContext(path, code, "python", "pytest", assertion)):
            self._finding(result, match.rule_id, match.severity, match.title, match.message, path, start, end, code, request)
        return
        empty = bool(re.search(r"^\s*(pass|\.\.\.)\s*$", "\n".join(code.splitlines()[1:]), re.MULTILINE))
        if not assertion:
            self._finding(result, "TQ001", "high", "No assertion", "Test has no explicit or framework assertion.", path, start, end, code)
        if empty:
            self._finding(result, "TQ003", "high", "Empty test", "Test body is only a placeholder.", path, start, end, code)
        if re.search(r"@(?:pytest\.)?mark\.(?:skip|xfail)\b", code):
            self._finding(result, "TQ002", "medium", "Skipped test", "Test is marked skip or xfail.", path, start, end, code)
        if re.search(r"\b(?:TODO|NotImplemented)\b", code):
            self._finding(result, "TQ004", "medium", "Todo test", "Test contains an unfinished placeholder.", path, start, end, code)
        if re.search(r"assert\s+(?:True|1\s*==\s*1)\b", code):
            self._finding(result, "TQ005", "critical", "Always-pass assertion", "Assertion is constant and cannot verify behavior.", path, start, end, code)
        if re.search(r"except\s+(?:Exception|BaseException)\b", code):
            self._finding(result, "TQ015", "high", "Broad exception catch", "Test catches a broad exception type.", path, start, end, code)
        if re.search(r"try:\s*[\s\S]*?except\s+", code) and not re.search(r"except[\s\S]*(?:assert|raise|fail)", code):
            self._finding(result, "TQ006", "high", "Swallowed exception", "Test catches an exception without making failure observable.", path, start, end, code)
        if re.search(r"assert\s+\w+\.status_code", code) and len(re.findall(r"\bassert\b", code)) == 1:
            self._finding(result, "TQ010", "medium", "Status-only API assertion", "Test only asserts the HTTP status.", path, start, end, code)
        if re.search(r"\btime\.sleep\s*\(", code):
            self._finding(result, "TQ012", "medium", "Sleep-based test", "Fixed sleep is used instead of a condition.", path, start, end, code, request)
        mock_count = len(re.findall(r"\b(?:Mock|MagicMock|patch)\s*\(", code))
        if mock_count >= 3 and mock_count >= len(re.findall(r"\bassert\b", code)):
            self._finding(result, "TQ007", "medium", "Excessive mocking", "Mock count is high relative to behavior assertions.", path, start, end, code)
        assertions = re.findall(r"^\s*(assert\s+.+)$", code, re.MULTILINE)
        if len(assertions) != len(set(assertions)):
            self._finding(result, "TQ009", "low", "Duplicated assertion", "Repeated assertion adds no verification value.", path, start, end, code)
        if re.search(r"\b(?:return|raise)\b[^\n]*\n\s*assert\b", code):
            self._finding(result, "TQ008", "high", "Unreachable assertion", "Assertion follows return or raise in the same block.", path, start, end, code)
        if re.search(r"=\s*\{[^\n]*['\"](?:success|ok)['\"][^\n]*\}\s*\n\s*assert\s+.+==\s*['\"](?:success|ok)['\"]", code):
            self._finding(result, "TQ013", "low", "Hardcoded success path", "Test constructs its own successful result instead of observing behavior.", path, start, end, code)
        if not assertion or re.search(r"assert\s+(?:True|1\s*==\s*1)\b", code):
            self._finding(result, "TQ014", "high", "No observable outcome", "Test has no meaningful observable outcome.", path, start, end, code)

    def _typescript_rules(self, result: ReviewResult, path: str, start: int, end: int, code: str, request: ReviewRequest) -> None:
        for match in RuleRunner(RuleRegistry.default()).run(RuleContext(path, code, "typescript", "Playwright", bool(re.search(r"\bexpect\s*\(", code)))):
            self._finding(result, match.rule_id, match.severity, match.title, match.message, path, start, end, code, request)
        return
        assertion = bool(re.search(r"\bexpect\s*\(", code))
        if not assertion:
            self._finding(result, "TQ001", "high", "No assertion", "Test has no Playwright expectation.", path, start, end, code)
        if re.search(r"expect\s*\(\s*true\s*\)\.toBe\s*\(\s*true\s*\)", code):
            self._finding(result, "TQ005", "critical", "Always-pass assertion", "Expectation is constant and cannot verify behavior.", path, start, end, code)
        if "page.waitForTimeout" in code:
            self._finding(result, "TQ012", "medium", "Sleep-based test", "Fixed timeout is used instead of a condition.", path, start, end, code, request)
        if "page.screenshot" in code and not assertion:
            self._finding(result, "TQ011", "medium", "Screenshot-only E2E test", "Screenshot is not a business assertion.", path, start, end, code)
        if re.search(r"\btest\.skip\b|\bit\.skip\b", code):
            self._finding(result, "TQ002", "medium", "Skipped test", "Test is disabled with skip.", path, start, end, code)
        if re.search(r"\b(?:TODO|FIXME|NotImplemented)\b", code):
            self._finding(result, "TQ004", "medium", "Todo test", "Test contains an unfinished placeholder.", path, start, end, code)
        if re.search(r"expect\s*\([^\n]*status\s*\(\s*\)\s*\)\s*\.toBe", code) and len(re.findall(r"\bexpect\s*\(", code)) == 1:
            self._finding(result, "TQ010", "medium", "Status-only API assertion", "Test only asserts the response status.", path, start, end, code)
        if re.search(r"catch\s*\([^)]*(?:error|e|err)[^)]*\)\s*\{\s*\}", code, re.DOTALL):
            self._finding(result, "TQ015", "high", "Broad exception catch", "Test catches and swallows an error.", path, start, end, code)
        if not assertion or re.search(r"expect\s*\(\s*true\s*\)", code):
            self._finding(result, "TQ014", "high", "No observable outcome", "Test has no meaningful observable outcome.", path, start, end, code)

    def _finding(self, result: ReviewResult, rule_id: str, severity: str, title: str, message: str, path: str, start: int, end: int, code: str, request: ReviewRequest | None = None) -> None:
        request = request or ACTIVE_REQUEST.get()
        if request and any(fnmatch.fnmatch(path, pattern) for pattern in request.suppressed_rules.get(rule_id, ())):
            return
        if request:
            severity = request.rule_severity.get(rule_id, severity)
        evidence = self._evidence(result, "static_rule_match", Path(path), start, end, code)
        result.findings.append(Finding(f"F-{len(result.findings)+1:03d}", rule_id, severity, title, message, path, start, [evidence.id]))

    def _evidence(self, result: ReviewResult, kind: str, path: Path, start: int, end: int, content: str, status: str = "verified") -> Evidence:
        evidence = Evidence(f"EV-{len(result.evidence)+1:03d}", kind, str(path), start, end, "sha256:" + hashlib.sha256(content.encode()).hexdigest(), status=status, extractor=kind, loop_iteration=len(result.trace))
        result.evidence.append(evidence)
        return evidence
