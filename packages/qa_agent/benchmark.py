"""Reproducible v0.4 real-project benchmark manifest and fixed runner."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time
from typing import Any, Sequence

from .effectiveness import TestEffectivenessContext
from .effectiveness_service import TestEffectivenessRequest, TestEffectivenessService, resolve_repository_revision
from .mutation_adapters import MutmutMutationBackend, PitMutationBackend, StrykerMutationBackend
from .runtime import ExecutionBudget


HASH_PREFIX = "sha256:"
VALID_ADJUDICATION_STATUSES = {"resolved", "unresolved", "not_applicable"}
VALID_WORKING_TREE_STATUSES = {"clean", "dirty"}
VALID_BACKEND_NAMES = {"mutmut", "pit", "stryker"}
FIXED_FLAGS = {
    "--requirement",
    "--repository",
    "--trace-db",
    "--test-context",
    "--mutation-report",
    "--backend",
    "--min-score",
    "--format",
}


def _hash_bytes(value: bytes) -> str:
    return HASH_PREFIX + hashlib.sha256(value).hexdigest()


def _hash_file(path: Path) -> str:
    return _hash_bytes(path.read_bytes())


def _tree_snapshot(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if not item.is_file() or ".git" in item.parts:
            continue
        relative = item.relative_to(path).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return HASH_PREFIX + digest.hexdigest()


def _valid_hash(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(HASH_PREFIX) and len(value) == len(HASH_PREFIX) + 64 and all(character in "0123456789abcdefABCDEF" for character in value[len(HASH_PREFIX) :])


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


@dataclass(frozen=True)
class BenchmarkArtifact:
    path: Path
    sha256: str


@dataclass(frozen=True)
class WorkingTreeObservation:
    status: str
    snapshot_hash: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class BenchmarkManifest:
    schema_version: int
    case_id: str
    repository: Path
    repository_revision: str
    framework: str
    artifacts: dict[str, BenchmarkArtifact]
    argv: tuple[str, ...]
    allow_dirty: bool
    working_tree: WorkingTreeObservation
    ground_truth: dict[str, Any]
    adjudication: dict[str, Any]
    manifest_dir: Path = Path(".")


@dataclass(frozen=True)
class BenchmarkValidationResult:
    decision: str
    manifest: BenchmarkManifest | None = None
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class BenchmarkCaseResult:
    case_id: str
    decision: str
    termination_reason: str
    adjudication_status: str = "unresolved"
    reasons: tuple[str, ...] = ()
    true_positive: int | None = None
    false_positive: int | None = None
    false_negative: int | None = None
    true_negative: int | None = None
    useful_findings: int | None = None
    reported_findings: int | None = None
    correctly_explained: int | None = None
    eligible_survivors: int | None = None
    cost: float | None = None
    latency_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "decision": self.decision,
            "termination_reason": self.termination_reason,
            "adjudication_status": self.adjudication_status,
            "reasons": list(self.reasons),
            "true_positive": self.true_positive,
            "false_positive": self.false_positive,
            "false_negative": self.false_negative,
            "true_negative": self.true_negative,
            "useful_findings": self.useful_findings,
            "reported_findings": self.reported_findings,
            "correctly_explained": self.correctly_explained,
            "eligible_survivors": self.eligible_survivors,
            "cost": self.cost,
            "latency_ms": self.latency_ms,
        }


def _artifact_path(base: Path, value: Any) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def _parse_labels(payload: Any, reasons: list[str]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        reasons.append("ground_truth")
        return {"survivor_labels": [], "signal_labels": []}
    for field in ("survivor_labels", "signal_labels"):
        if not isinstance(payload.get(field), list):
            reasons.append(field)
    survivor_labels = payload.get("survivor_labels", [])
    if isinstance(survivor_labels, list):
        required = {"object_id", "expected_outcome", "expected_classification", "evidence_ref", "reviewer_decision"}
        for index, label in enumerate(survivor_labels):
            if not isinstance(label, dict) or not required <= set(label):
                reasons.append(f"ground_truth.survivor_labels[{index}]")
                continue
            if any(not _non_empty_string(label.get(field)) for field in required):
                reasons.append(f"ground_truth.survivor_labels[{index}]")
    return payload


def load_manifest(path: Path) -> BenchmarkValidationResult:
    reasons: list[str] = []
    manifest_path = path.resolve()
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return BenchmarkValidationResult("incomplete", None, ("manifest JSON is invalid",))
    if not isinstance(payload, dict):
        return BenchmarkValidationResult("incomplete", None, ("manifest must be an object",))
    if payload.get("schema_version") != 1:
        reasons.append("schema_version")
    if not _non_empty_string(payload.get("case_id")):
        reasons.append("case_id")

    repository_payload = payload.get("repository")
    if not isinstance(repository_payload, dict):
        reasons.append("repository")
        repository_path = manifest_path.parent
        repository_revision = ""
    else:
        repository_path = _artifact_path(manifest_path.parent, repository_payload.get("path", "")) if _non_empty_string(repository_payload.get("path")) else manifest_path.parent
        repository_revision = repository_payload.get("revision", "")
        if not _non_empty_string(repository_payload.get("path")):
            reasons.append("repository.path")
        if not _non_empty_string(repository_revision):
            reasons.append("repository.revision")
    if not _non_empty_string(payload.get("framework")):
        reasons.append("framework")

    artifact_payload = payload.get("artifacts")
    artifacts: dict[str, BenchmarkArtifact] = {}
    if not isinstance(artifact_payload, dict):
        reasons.append("artifacts")
    else:
        for name in ("requirement", "test_context", "mutation_report"):
            record = artifact_payload.get(name)
            if not isinstance(record, dict):
                reasons.append(f"artifacts.{name}")
                continue
            if not _non_empty_string(record.get("path")):
                reasons.append(f"artifacts.{name}.path")
            if not _valid_hash(record.get("sha256")):
                reasons.append(f"artifacts.{name}.sha256")
            if _non_empty_string(record.get("path")) and _valid_hash(record.get("sha256")):
                artifacts[name] = BenchmarkArtifact(_artifact_path(manifest_path.parent, record["path"]), record["sha256"])

    argv_payload = payload.get("argv")
    argv = tuple(argv_payload) if isinstance(argv_payload, list) and all(isinstance(item, str) for item in argv_payload) else ()
    if not argv:
        reasons.append("argv")
    elif len(argv) < 2 or argv[0] != "qa-agent" or argv[1] != "assess-effectiveness":
        reasons.append("argv fixed runner")
    else:
        for token in argv[2:]:
            if token.startswith("--") and token not in FIXED_FLAGS:
                reasons.append(f"argv unsupported flag: {token}")

    allow_dirty = payload.get("allow_dirty")
    if not isinstance(allow_dirty, bool):
        reasons.append("allow_dirty")
        allow_dirty = False
    working_payload = payload.get("working_tree")
    if not isinstance(working_payload, dict) or working_payload.get("status") not in VALID_WORKING_TREE_STATUSES:
        reasons.append("working_tree.status")
        working_tree = WorkingTreeObservation("clean")
    else:
        status = working_payload["status"]
        snapshot_hash = working_payload.get("snapshot_hash")
        reason = working_payload.get("reason")
        if status == "dirty" and not allow_dirty:
            reasons.append("dirty tree requires allow_dirty")
        if status == "dirty" and allow_dirty and not _valid_hash(snapshot_hash):
            reasons.append("snapshot_hash")
        if status == "dirty" and allow_dirty and not _non_empty_string(reason):
            reasons.append("reason")
        working_tree = WorkingTreeObservation(status, snapshot_hash if isinstance(snapshot_hash, str) else None, reason if isinstance(reason, str) else None)

    ground_truth = _parse_labels(payload.get("ground_truth"), reasons)
    adjudication = payload.get("adjudication")
    if not isinstance(adjudication, dict) or adjudication.get("status") not in VALID_ADJUDICATION_STATUSES:
        reasons.append("adjudication.status")
        adjudication = {"status": "unresolved"}
    elif adjudication["status"] == "resolved":
        record = adjudication.get("record")
        if not isinstance(record, dict) or not _non_empty_string(record.get("path")) or not _valid_hash(record.get("sha256")):
            reasons.append("adjudication.record")
        elif isinstance(record, dict):
            adjudication = dict(adjudication)
            adjudication["record"] = dict(record)
            adjudication["record"]["path"] = str(_artifact_path(manifest_path.parent, record["path"]))

    if reasons:
        return BenchmarkValidationResult("incomplete", None, tuple(dict.fromkeys(reasons)))
    manifest = BenchmarkManifest(
        1,
        payload["case_id"],
        repository_path,
        repository_revision,
        payload["framework"],
        artifacts,
        argv,
        allow_dirty,
        working_tree,
        ground_truth,
        adjudication,
        manifest_path.parent,
    )
    return BenchmarkValidationResult("pass", manifest, ())


def validate_case(manifest: BenchmarkManifest) -> BenchmarkValidationResult:
    reasons: list[str] = []
    if not manifest.repository.is_dir():
        reasons.append("repository does not exist")
    else:
        try:
            if resolve_repository_revision(manifest.repository) != manifest.repository_revision:
                reasons.append("repository revision mismatch")
            current_snapshot = _tree_snapshot(manifest.repository)
            if (manifest.repository / ".git").exists():
                status = subprocess.run(
                    ["git", "status", "--porcelain", "--untracked-files=all"],
                    cwd=manifest.repository,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=10,
                )
                if status.returncode != 0:
                    reasons.append("working tree observation failed")
                elif status.stdout.strip() and not manifest.allow_dirty:
                    reasons.append("dirty tree requires allow_dirty")
            if manifest.working_tree.status == "dirty" and manifest.working_tree.snapshot_hash != current_snapshot:
                reasons.append("working tree snapshot mismatch")
            if manifest.working_tree.status == "clean" and manifest.working_tree.snapshot_hash and manifest.working_tree.snapshot_hash != current_snapshot:
                reasons.append("working tree snapshot mismatch")
        except (OSError, ValueError):
            reasons.append("repository observation failed")
    for name, artifact in manifest.artifacts.items():
        try:
            if not artifact.path.is_file():
                reasons.append(f"artifact missing: {name}")
            elif _hash_file(artifact.path) != artifact.sha256:
                reasons.append(f"artifact hash mismatch: {name}")
        except OSError:
            reasons.append(f"artifact unreadable: {name}")
    if manifest.adjudication.get("status") == "resolved":
        record = manifest.adjudication.get("record", {})
        record_path = Path(record.get("path", ""))
        try:
            if not record_path.is_file():
                reasons.append("adjudication record missing")
            elif _hash_file(record_path) != record.get("sha256"):
                reasons.append("adjudication record hash mismatch")
        except OSError:
            reasons.append("adjudication record unreadable")
    if manifest.working_tree.status == "dirty" and not manifest.allow_dirty:
        reasons.append("dirty tree requires allow_dirty")
    if reasons:
        return BenchmarkValidationResult("incomplete", None, tuple(dict.fromkeys(reasons)))
    return BenchmarkValidationResult("pass", manifest, ())


def _parse_fixed_argv(manifest: BenchmarkManifest) -> tuple[dict[str, str], tuple[str, ...]]:
    values: dict[str, str] = {}
    tokens = manifest.argv[2:]
    index = 0
    while index < len(tokens):
        flag = tokens[index]
        if flag not in FIXED_FLAGS or index + 1 >= len(tokens) or tokens[index + 1].startswith("--"):
            raise ValueError("argv is not a fixed assess-effectiveness record")
        values[flag] = tokens[index + 1]
        index += 2
    if not values.get("--requirement") or not values.get("--min-score"):
        raise ValueError("argv is missing requirement or min-score")
    try:
        score = float(values["--min-score"])
    except ValueError as exc:
        raise ValueError("argv min-score is invalid") from exc
    if not math.isfinite(score) or not 0 <= score <= 1:
        raise ValueError("argv min-score is outside [0, 1]")
    if ("--mutation-report" in values) == ("--backend" in values):
        raise ValueError("argv must select exactly one mutation report or backend")
    if values.get("--backend") not in (None, *VALID_BACKEND_NAMES):
        raise ValueError("argv backend is unsupported")
    return values, tuple(tokens)


def _fixed_backend(name: str):
    return {
        "mutmut": MutmutMutationBackend,
        "pit": PitMutationBackend,
        "stryker": StrykerMutationBackend,
    }[name]()


def _case_metrics(manifest: BenchmarkManifest, assessment, elapsed_ms: float) -> BenchmarkCaseResult:
    adjudication_status = manifest.adjudication.get("status", "unresolved")
    if adjudication_status != "resolved":
        return BenchmarkCaseResult(manifest.case_id, assessment.decision, assessment.termination_reason, adjudication_status, latency_ms=elapsed_ms)
    labels = manifest.ground_truth.get("survivor_labels", [])
    expected = {label["object_id"] for label in labels if label.get("expected_outcome") == "survived" and label.get("reviewer_decision") == "accepted"}
    reported = {link.mutant_id for link in assessment.survivor_links}
    true_positive = len(expected & reported)
    false_positive = len(reported - expected)
    false_negative = len(expected - reported)
    correctly_explained = sum(1 for link in assessment.survivor_links if link.mutant_id in expected and link.mapping_status == "verified")
    return BenchmarkCaseResult(
        manifest.case_id,
        assessment.decision,
        assessment.termination_reason,
        adjudication_status,
        (),
        true_positive,
        false_positive,
        false_negative,
        None,
        true_positive,
        len(reported),
        correctly_explained,
        len(expected),
        None,
        elapsed_ms,
    )


def run_case(manifest: BenchmarkManifest) -> BenchmarkCaseResult:
    validation = validate_case(manifest)
    if validation.decision != "pass":
        return BenchmarkCaseResult(manifest.case_id, "incomplete", "INSUFFICIENT_EVIDENCE", manifest.adjudication.get("status", "unresolved"), validation.reasons)
    try:
        values, _ = _parse_fixed_argv(manifest)
        repository_arg = Path(values.get("--repository", str(manifest.repository))).resolve()
        if repository_arg != manifest.repository:
            raise ValueError("argv repository does not match manifest repository")
        context_artifact = manifest.artifacts["test_context"]
        if values.get("--test-context") and _artifact_path(manifest.manifest_dir, values["--test-context"]) != context_artifact.path:
            raise ValueError("argv test-context does not match manifest artifact")
        report_artifact = manifest.artifacts["mutation_report"]
        if values.get("--mutation-report") and _artifact_path(manifest.manifest_dir, values["--mutation-report"]) != report_artifact.path:
            raise ValueError("argv mutation-report does not match manifest artifact")
        context = TestEffectivenessContext.from_dict(json.loads(context_artifact.path.read_text(encoding="utf-8")), 1_000_000)
        if context.requirement_id != values["--requirement"]:
            raise ValueError("argv requirement does not match test context")
        report_path = report_artifact.path if "--mutation-report" in values else None
        backend = _fixed_backend(values["--backend"]) if "--backend" in values else None
        before = _tree_snapshot(manifest.repository)
        started = time.monotonic()
        assessment = TestEffectivenessService().assess(
            TestEffectivenessRequest(
                context.requirement_id,
                manifest.repository,
                context,
                report_path,
                backend,
                float(values["--min-score"]),
                ExecutionBudget.v04_defaults(),
            )
        )
        elapsed_ms = (time.monotonic() - started) * 1000
        after = _tree_snapshot(manifest.repository)
        if before != after:
            return BenchmarkCaseResult(manifest.case_id, "incomplete", "INSUFFICIENT_EVIDENCE", manifest.adjudication.get("status", "unresolved"), ("repository changed during benchmark",))
        return _case_metrics(manifest, assessment, elapsed_ms)
    except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        return BenchmarkCaseResult(manifest.case_id, "incomplete", "INSUFFICIENT_EVIDENCE", manifest.adjudication.get("status", "unresolved"), (str(exc),))


def _ratio(numerator: int | float | None, denominator: int | float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def _sum_metric(results: Sequence[BenchmarkCaseResult], field: str) -> int | float | None:
    values = [getattr(result, field) for result in results]
    if not values or any(value is None for value in values):
        return None
    return sum(values)


def aggregate_metrics(results: Sequence[BenchmarkCaseResult]) -> dict[str, float | None]:
    adjudicated = [result for result in results if result.adjudication_status == "resolved"]
    true_positive = _sum_metric(adjudicated, "true_positive")
    false_positive = _sum_metric(adjudicated, "false_positive")
    false_negative = _sum_metric(adjudicated, "false_negative")
    true_negative = _sum_metric(adjudicated, "true_negative")
    useful = _sum_metric(adjudicated, "useful_findings")
    reported = _sum_metric(adjudicated, "reported_findings")
    explained = _sum_metric(adjudicated, "correctly_explained")
    eligible = _sum_metric(adjudicated, "eligible_survivors")
    costs = [result.cost for result in results if result.cost is not None]
    latencies = [result.latency_ms for result in results if result.latency_ms is not None]
    return {
        "precision": _ratio(true_positive, true_positive + false_positive if true_positive is not None and false_positive is not None else None),
        "recall": _ratio(true_positive, true_positive + false_negative if true_positive is not None and false_negative is not None else None),
        "false_positive_rate": _ratio(false_positive, false_positive + true_negative if false_positive is not None and true_negative is not None else None),
        "useful_finding_rate": _ratio(useful, reported),
        "survivor_explanation_accuracy": _ratio(explained, eligible),
        "cost_per_report": (sum(costs) / len(costs)) if costs else None,
        "latency_per_report": (sum(latencies) / len(latencies)) if latencies else None,
    }
