"""Strict offline mutation report parser and bounded tool adapters."""

from __future__ import annotations

import hashlib
from importlib import metadata as importlib_metadata
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from .effectiveness import (
    OUTCOMES,
    _hash,
    _relative_path,
    _unique,
    canonical_json_bytes,
    Mutant,
    MutationResult,
)
from .mutation_backends import (
    BackendCapability,
    MutationBackend,
    MutationBackendResult,
    MutationConfigurationError,
    MutationExecutionError,
    MutationInputError,
    MutationRequest,
    MutationUnavailableError,
    MutationUnsupportedError,
)
from .review import Evidence
from .runtime import ExecutionBudget


ADAPTER_BACKENDS = {"offline", "mutmut", "pit", "stryker"}
MAX_STRING_BYTES = 100_000
MAX_ARRAY_ITEMS = 10_000


def _metadata(limits: ExecutionBudget) -> dict[str, Any]:
    return {
        "redaction": {"applied": False, "policy": "bounded-redacted-v1", "max_bytes": 4096},
        "limits": {
            "context_bytes": limits.max_context_bytes or 1_000_000,
            "report_bytes": limits.max_report_bytes or 2_000_000,
        },
    }


def _evidence(
    evidence_id: str,
    evidence_type: str,
    subject: str,
    path: str,
    line: int,
    content_hash: str,
    backend: str,
    limits: ExecutionBudget,
) -> Evidence:
    return Evidence(
        evidence_id,
        evidence_type,
        path,
        line,
        line,
        content_hash,
        provider=backend,
        extractor="offline-report-v1",
        subject=subject,
        source_ref=f"{path}#L{line}",
        metadata=_metadata(limits),
    )


def _stable_evidence_id(prefix: str, value: str) -> str:
    return f"{prefix}-{hashlib.sha256(value.encode('utf-8')).hexdigest()[:16]}"


def _capability(
    backend: str,
    repository: Path,
    status: str,
    tool_version: str | None,
    languages: tuple[str, ...],
    frameworks: tuple[str, ...],
    reason: str | None,
    limits: dict[str, Any],
) -> BackendCapability:
    payload = {
        "backend": backend,
        "status": status,
        "tool_version": tool_version,
        "languages": list(languages),
        "frameworks": list(frameworks),
        "reason": reason,
        "limits": limits,
    }
    content_hash = "sha256:" + hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    evidence = Evidence(
        _stable_evidence_id("EV-CAPABILITY", backend + ":" + str(repository)),
        "backend_capability",
        str(repository),
        1,
        1,
        content_hash,
        provider="agent-runtime",
        extractor="mutation-capability-v1",
        subject="backend:" + backend,
        source_ref=str(repository) + "#capability",
        metadata={
            **_metadata(ExecutionBudget.v04_defaults()),
            "capability": {
                "backend": backend,
                "status": status,
                "tool_version": tool_version,
                "languages": list(languages),
                "frameworks": list(frameworks),
                "reason": reason,
                "limits": limits,
            },
        },
    )
    return BackendCapability(backend, status, tool_version, languages, frameworks, reason, limits, (evidence,))


def _string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > MAX_STRING_BYTES:
        raise MutationInputError(f"{name} must be a bounded non-empty string")
    return value


def _string_list(value: Any, name: str, *, required: bool = True) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) > MAX_ARRAY_ITEMS:
        raise MutationInputError(f"{name} must be a bounded array")
    if required and not value:
        raise MutationInputError(f"{name} is required")
    try:
        return _unique(tuple(_string(item, name) for item in value), name, required=required)
    except ValueError as exc:
        raise MutationInputError(str(exc)) from exc


class OfflineMutationReportAdapter:
    def parse(self, report_path: Path, repository_revision: str, limits: ExecutionBudget) -> MutationBackendResult:
        try:
            raw = report_path.read_bytes()
        except OSError as exc:
            raise MutationInputError(f"cannot read mutation report: {exc}") from exc
        max_report_bytes = limits.max_report_bytes or 2_000_000
        if len(raw) > max_report_bytes:
            raise MutationInputError("mutation report exceeds max_report_bytes")
        raw_hash = "sha256:" + hashlib.sha256(raw).hexdigest()
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MutationInputError("mutation report is not valid UTF-8 JSON") from exc
        if not isinstance(payload, dict):
            raise MutationInputError("mutation report must be a JSON object")
        if type(payload.get("schema_version")) is not int or payload.get("schema_version") != 1:
            raise MutationInputError("unsupported mutation report schema")
        backend = payload.get("backend")
        if backend not in ADAPTER_BACKENDS:
            raise MutationInputError("unsupported mutation report backend")
        if payload.get("repository_revision") != repository_revision:
            raise MutationInputError("mutation report repository revision does not match")
        observation_status = payload.get("observation_status")
        if observation_status not in {"complete", "partial"}:
            raise MutationInputError("invalid mutation observation_status")
        target_paths = _string_list(payload.get("target_paths"), "target_paths")
        selected_test_ids = _string_list(payload.get("selected_test_ids"), "selected_test_ids")
        try:
            target_paths = tuple(_relative_path(path, "target path") for path in target_paths)
        except ValueError as exc:
            raise MutationInputError(str(exc)) from exc
        mutants_payload = payload.get("mutants")
        max_mutants = limits.max_mutants or 500
        if not isinstance(mutants_payload, list) or not mutants_payload or len(mutants_payload) > max_mutants:
            raise MutationInputError("mutants must be a bounded non-empty array")
        seen_ids: set[str] = set()
        mutants: list[Mutant] = []
        results: list[MutationResult] = []
        evidence: list[Evidence] = [
            _evidence(
                _stable_evidence_id("EV-REPORT", raw_hash),
                "mutation_report",
                report_path.name,
                str(report_path),
                1,
                raw_hash,
                backend,
                limits,
            )
        ]
        for item in mutants_payload:
            try:
                if not isinstance(item, dict):
                    raise MutationInputError("mutant must be an object")
                required = {"id", "path", "line", "operator", "original", "mutated", "outcome", "executed_test_ids", "killing_test_ids"}
                if not required <= item.keys():
                    raise MutationInputError("mutant is missing a required field")
                mutant_id = _string(item["id"], "mutant id")
                if mutant_id in seen_ids:
                    raise MutationInputError("duplicate mutant id")
                seen_ids.add(mutant_id)
                path = _relative_path(_string(item["path"], "mutant path"), "mutant path")
                line = item["line"]
                if type(line) is not int or line < 1:
                    raise MutationInputError("mutant line must be positive")
                operator = _string(item["operator"], "mutant operator")
                original = _string(item["original"], "mutant original")
                mutated = _string(item["mutated"], "mutant mutated")
                outcome = item["outcome"]
                if outcome not in OUTCOMES:
                    raise MutationInputError("unknown mutation outcome")
                executed = _string_list(item["executed_test_ids"], "executed_test_ids", required=False)
                killing = _string_list(item["killing_test_ids"], "killing_test_ids", required=False)
                if not set(executed) <= set(selected_test_ids) or not set(killing) <= set(executed):
                    raise MutationInputError("mutation test identity is outside selected tests")
                if outcome == "killed" and not killing:
                    raise MutationInputError("killed mutation requires a killing test")
                if outcome != "killed" and killing:
                    raise MutationInputError("only killed mutation has killing tests")
                if outcome == "not_run" and executed:
                    raise MutationInputError("not_run mutation cannot have executed tests")
                duration = item.get("duration_ms", 0)
                if type(duration) is not int or duration < 0:
                    raise MutationInputError("duration_ms must be a non-negative integer")
                stdout_hash = item.get("stdout_hash")
                stderr_hash = item.get("stderr_hash")
                for output_hash in (stdout_hash, stderr_hash):
                    if output_hash is not None:
                        if not isinstance(output_hash, str):
                            raise MutationInputError("output hash must be a string or null")
                        try:
                            _hash(output_hash, "output hash")
                        except ValueError as exc:
                            raise MutationInputError(str(exc)) from exc
                source = json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                mutant_hash = "sha256:" + hashlib.sha256(source.encode("utf-8")).hexdigest()
                mutant_evidence_id = _stable_evidence_id("EV-MUTANT", mutant_id)
                result_evidence_id = _stable_evidence_id("EV-RESULT", mutant_id)
                evidence.append(_evidence(mutant_evidence_id, "mutant_survived" if outcome == "survived" else "mutant_killed" if outcome == "killed" else "mutation_unexecuted", mutant_id, path, line, mutant_hash, backend, limits))
                evidence.append(_evidence(result_evidence_id, "mutation_run", mutant_id, path, line, mutant_hash, backend, limits))
                mutants.append(Mutant(mutant_id, path, line, operator, original, mutated, "not_run" if outcome == "not_run" else "active", (mutant_evidence_id,)))
                results.append(MutationResult("PROVIDER-RUN", mutant_id, outcome, executed, killing, duration, stdout_hash, stderr_hash, (result_evidence_id,)))
            except MutationInputError:
                raise
            except (KeyError, TypeError, ValueError) as exc:
                raise MutationInputError(f"invalid mutant input: {exc}") from exc
        if observation_status == "partial":
            process_status = "partial"
        elif all(item.outcome in {"killed", "survived"} for item in results):
            process_status = "completed"
        elif any(item.outcome in {"killed", "survived"} for item in results):
            process_status = "partial"
        elif any(item.outcome == "error" for item in results):
            process_status = "error"
        else:
            process_status = "not_run"
        return MutationBackendResult(
            backend,
            payload.get("tool_version"),
            process_status,
            observation_status,
            tuple(mutants),
            tuple(results),
            tuple(evidence),
            raw_hash,
            target_paths,
            selected_test_ids,
        )


class MutmutMutationBackend:
    _STATUS_BY_EXIT_CODE = {
        0: "survived",
        1: "killed",
        2: "interrupted",
        3: "killed",
        5: "no tests",
        24: "timeout",
        33: "no tests",
        34: "skipped",
        35: "suspicious",
        36: "timeout",
        37: "caught by type check",
        152: "timeout",
        255: "timeout",
        -9: "segfault",
        -11: "segfault",
        -24: "timeout",
    }

    def detect(self, repository: Path) -> BackendCapability:
        executable = shutil.which("mutmut")
        if executable is None:
            return _capability("mutmut", repository, "unavailable", None, ("Python",), ("pytest",), "mutmut executable is unavailable", {})
        try:
            tool_version = importlib_metadata.version("mutmut")
        except importlib_metadata.PackageNotFoundError:
            tool_version = None
        return _capability(
            "mutmut",
            repository,
            "available",
            tool_version,
            ("Python",),
            ("pytest",),
            None,
            {"executable": executable, "controlled_copy": True, "report_format": "mutants/*.meta"},
        )

    def _line_for_mutant(self, controlled: Path, source_path: str, mutant_id: str) -> int:
        spans_path = controlled / "mutants" / (source_path + ".spans")
        try:
            payload = json.loads(spans_path.read_text(encoding="utf-8"))
            function_name = mutant_id.rsplit(".", 1)[-1].split("__mutmut_", 1)[0]
            span = payload.get("spans", {}).get(function_name)
            if isinstance(span, list) and span and type(span[0]) is int and span[0] > 0:
                return span[0]
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            pass
        return 1

    def _tests_for_mutant(
        self,
        executable: str,
        controlled: Path,
        mutant_id: str,
        selected_test_ids: tuple[str, ...],
        deadline: float,
    ) -> tuple[str, ...] | None:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise MutationExecutionError("mutmut report collection timed out")
        try:
            completed = subprocess.run(
                [executable, "tests-for-mutant", mutant_id],
                cwd=controlled,
                capture_output=True,
                text=True,
                shell=False,
                timeout=remaining,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise MutationExecutionError("mutmut report collection timed out") from exc
        if completed.returncode != 0:
            return None
        selected = set(selected_test_ids)
        observed = tuple(dict.fromkeys(line.strip() for line in completed.stdout.splitlines() if line.strip() and line.strip() in selected))
        return observed

    def run(self, request: MutationRequest) -> MutationBackendResult:
        capability = self.detect(request.repository if request is not None else Path("."))
        if capability.status == "unavailable":
            raise MutationUnavailableError(capability.reason or "mutmut is unavailable")
        if request is None:
            raise MutationConfigurationError("mutmut requires a mutation request")
        if "EXECUTE_MUTATION" not in request.permission_context.allowed_actions:
            raise MutationConfigurationError("mutation execution permission is not granted")
        executable = str(capability.limits.get("executable", "mutmut"))
        deadline = time.monotonic() + request.timeout_seconds
        with tempfile.TemporaryDirectory(prefix="qa-agent-mutmut-") as directory:
            controlled = Path(directory) / "repository"
            shutil.copytree(request.repository, controlled)
            argv = [executable, "run", "--paths-to-mutate", ",".join(request.target_paths)]
            try:
                completed = subprocess.run(
                    argv,
                    cwd=controlled,
                    capture_output=True,
                    text=True,
                    shell=False,
                    timeout=max(0.001, deadline - time.monotonic()),
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise MutationExecutionError("mutmut execution timed out") from exc
            report_root = controlled / "mutants"
            meta_records: list[tuple[str, bytes, dict[str, Any]]] = []
            if report_root.is_dir():
                for meta_path in sorted(report_root.rglob("*.meta")):
                    relative = meta_path.relative_to(report_root).as_posix()
                    source_path = relative.removesuffix(".meta")
                    if source_path not in request.target_paths:
                        continue
                    try:
                        raw = meta_path.read_bytes()
                        if len(raw) > request.permission_context.max_file_bytes:
                            raise MutationExecutionError("mutmut metadata exceeds max_file_bytes")
                        payload = json.loads(raw.decode("utf-8"))
                    except MutationExecutionError:
                        raise
                    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                        raise MutationExecutionError(f"invalid mutmut metadata for {source_path}") from exc
                    if not isinstance(payload, dict) or not isinstance(payload.get("exit_code_by_key"), dict):
                        raise MutationExecutionError(f"mutmut metadata is missing exit_code_by_key for {source_path}")
                    meta_records.append((source_path, raw, payload))
            if not meta_records:
                if completed.returncode != 0:
                    raise MutationExecutionError("mutmut execution failed without a normalized report")
                raise MutationExecutionError("mutmut did not produce a normalized report")

            raw_report = bytearray()
            raw_report.extend(completed.stdout.encode("utf-8"))
            raw_report.extend(b"\0")
            raw_report.extend(completed.stderr.encode("utf-8"))
            for source_path, raw, _ in meta_records:
                raw_report.extend(source_path.encode("utf-8"))
                raw_report.extend(b"\0")
                raw_report.extend(raw)
            raw_report_hash = "sha256:" + hashlib.sha256(bytes(raw_report)).hexdigest()
            report_evidence_id = _stable_evidence_id("EV-REPORT", raw_report_hash)
            evidence: list[Evidence] = [
                _evidence(
                    report_evidence_id,
                    "mutation_report",
                    "mutmut",
                    "mutants",
                    1,
                    raw_report_hash,
                    "mutmut",
                    ExecutionBudget(max_report_bytes=request.permission_context.max_file_bytes),
                )
            ]
            mutants: list[Mutant] = []
            results: list[MutationResult] = []
            observed_complete = completed.returncode == 0
            seen_ids: set[str] = set()
            for source_path, raw, payload in meta_records:
                exit_codes = payload["exit_code_by_key"]
                durations = payload.get("durations_by_key", {})
                if not isinstance(durations, dict):
                    durations = {}
                meta_hash = "sha256:" + hashlib.sha256(raw).hexdigest()
                for mutant_id, exit_code in exit_codes.items():
                    if not isinstance(mutant_id, str) or not mutant_id or mutant_id in seen_ids:
                        raise MutationExecutionError("mutmut report contains an invalid or duplicate mutant id")
                    seen_ids.add(mutant_id)
                    status = self._STATUS_BY_EXIT_CODE.get(exit_code, "suspicious")
                    if exit_code is None:
                        observed_complete = False
                    tests: tuple[str, ...] = ()
                    if status in {"killed", "survived", "timeout", "suspicious", "segfault", "interrupted"}:
                        tests = self._tests_for_mutant(executable, controlled, mutant_id, request.selected_test_ids, deadline) or ()
                        if not tests and status in {"killed", "survived"}:
                            observed_complete = False
                    if status == "killed" and tests:
                        outcome = "killed"
                        killing = tests
                    elif status == "survived" and tests:
                        outcome = "survived"
                        killing = ()
                    elif status == "timeout":
                        outcome = "timeout"
                        killing = ()
                    elif status in {"no tests", "skipped", "not checked", "caught by type check"}:
                        outcome = "not_run"
                        tests = ()
                        killing = ()
                        observed_complete = False
                    else:
                        outcome = "error"
                        killing = ()
                        observed_complete = False
                    line = self._line_for_mutant(controlled, source_path, mutant_id)
                    mutant_hash = "sha256:" + hashlib.sha256((source_path + "\0" + mutant_id + "\0" + meta_hash).encode("utf-8")).hexdigest()
                    mutant_evidence_id = _stable_evidence_id("EV-MUTANT", mutant_id)
                    result_evidence_id = _stable_evidence_id("EV-RESULT", mutant_id)
                    evidence.append(_evidence(mutant_evidence_id, "mutant_observation", mutant_id, source_path, line, mutant_hash, "mutmut", ExecutionBudget(max_report_bytes=request.permission_context.max_file_bytes)))
                    evidence.append(_evidence(result_evidence_id, "mutation_run", mutant_id, source_path, line, mutant_hash, "mutmut", ExecutionBudget(max_report_bytes=request.permission_context.max_file_bytes)))
                    mutants.append(Mutant(mutant_id, source_path, line, "mutmut", "<unavailable>", "<unavailable>", "not_run" if outcome == "not_run" else "active", (mutant_evidence_id,)))
                    raw_duration = durations.get(mutant_id, 0)
                    duration_ms = int(round(raw_duration * 1000)) if isinstance(raw_duration, (int, float)) and raw_duration >= 0 else 0
                    results.append(MutationResult("PROVIDER-RUN", mutant_id, outcome, tests, killing, duration_ms, None, None, (result_evidence_id,)))
            if len(mutants) > request.max_mutants:
                raise MutationExecutionError("mutmut report exceeds max_mutants")
            if not mutants:
                raise MutationExecutionError("mutmut report contains no mutants")
            if observed_complete and all(item.outcome in {"killed", "survived"} for item in results):
                process_status = "completed"
                observation_status = "complete"
            elif any(item.outcome in {"killed", "survived", "timeout"} for item in results):
                process_status = "partial" if completed.returncode == 0 else "error"
                observation_status = "partial"
            else:
                process_status = "error" if completed.returncode != 0 else "not_run"
                observation_status = "partial"
            return MutationBackendResult(
                "mutmut",
                capability.tool_version,
                process_status,
                observation_status,
                tuple(mutants),
                tuple(results),
                tuple(evidence),
                raw_report_hash,
                request.target_paths,
                request.selected_test_ids,
            )


class PitMutationBackend:
    def detect(self, repository: Path) -> BackendCapability:
        return _capability("pit", repository, "unsupported", None, ("Java",), ("JUnit",), "PIT execution is deferred to a reproducible adapter slice", {})

    def run(self, request: MutationRequest) -> MutationBackendResult:
        raise MutationUnsupportedError("PIT execution is unsupported in this slice")


class StrykerMutationBackend:
    def detect(self, repository: Path) -> BackendCapability:
        return _capability("stryker", repository, "unsupported", None, ("TypeScript", "JavaScript"), ("Playwright",), "Stryker execution is deferred to a reproducible adapter slice", {})

    def run(self, request: MutationRequest) -> MutationBackendResult:
        raise MutationUnsupportedError("Stryker execution is unsupported in this slice")


def adapter_capability(backend: str, repository: Path) -> BackendCapability:
    adapters: dict[str, MutationBackend] = {
        "mutmut": MutmutMutationBackend(),
        "pit": PitMutationBackend(),
        "stryker": StrykerMutationBackend(),
    }
    if backend not in adapters:
        raise MutationInputError("unknown mutation backend")
    return adapters[backend].detect(repository)
