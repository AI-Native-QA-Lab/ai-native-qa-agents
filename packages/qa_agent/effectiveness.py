"""Versioned Test Effectiveness domain contracts and deterministic Gate rules."""

from __future__ import annotations

import hashlib
import json
import posixpath
import re
from dataclasses import asdict, dataclass, field, is_dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import PurePosixPath
from typing import Any, Sequence

from .review import Evidence
from .runtime import ExecutionBudget, LoopTrace, budget_to_dict, loop_trace_to_dict
from .test_engineering import TestIntent, TestScenario


PROCESS_STATUSES = {"completed", "partial", "unavailable", "error", "not_run"}
OBSERVATION_STATUSES = {"complete", "partial", "unknown"}
OUTCOMES = {"killed", "survived", "timeout", "error", "not_run"}
MUTANT_STATUSES = {"active", "invalid", "not_run"}
MAPPING_STATUSES = {"verified", "unverified", "unmapped"}
SIGNAL_KINDS = {
    "static_assertion",
    "execution",
    "requirement_relevance",
    "oracle_missing",
    "mutation_survivor",
    "semantic",
}
SEVERITIES = {"critical", "high", "medium", "low"}
HASH_PATTERN = re.compile(r"^sha256:[0-9a-fA-F]{64}$")


def _json_ready(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if is_dataclass(value):
        return {key: _json_ready(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    return value


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        _json_ready(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def artifact_hash(value: object, omit_field: str | None = None) -> str:
    ready = _json_ready(value)
    if omit_field is not None and isinstance(ready, dict):
        ready = dict(ready)
        ready.pop(omit_field, None)
    return "sha256:" + hashlib.sha256(canonical_json_bytes(ready)).hexdigest()


def _required(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")


def _unique(values: Sequence[str], name: str, *, required: bool = False) -> tuple[str, ...]:
    result = tuple(values)
    if required and not result:
        raise ValueError(f"{name} is required")
    if any(not isinstance(value, str) or not value.strip() for value in result):
        raise ValueError(f"{name} contains an empty value")
    if len(set(result)) != len(result):
        raise ValueError(f"{name} must be unique")
    return result


def _relative_path(value: str, name: str) -> str:
    _required(value, name)
    if value.startswith("/") or "\\" in value:
        raise ValueError(f"{name} must be repository-relative")
    parts = PurePosixPath(value).parts
    if not parts or ".." in parts or value in {".", ""} or posixpath.normpath(value) != value:
        raise ValueError(f"{name} must be normalized and cannot escape repository")
    return value


def _hash(value: str, name: str) -> None:
    if not HASH_PATTERN.fullmatch(value):
        raise ValueError(f"{name} must be a SHA-256 hash")


def _parse_intent(payload: dict[str, Any]) -> TestIntent:
    return TestIntent(
        payload["id"],
        payload["requirement_id"],
        payload["subject"],
        tuple(payload.get("evidence_ids", ())),
        tuple(payload.get("acceptance_criterion_ids", ())),
        tuple(payload.get("risk_ids", ())),
        payload.get("observable_behavior"),
        payload.get("business_oracle"),
    )


def _parse_scenario(payload: dict[str, Any]) -> TestScenario:
    return TestScenario(
        payload["id"],
        payload["intent_id"],
        payload["name"],
        tuple(payload.get("steps", ())),
        payload["expected_outcome"],
        tuple(payload.get("evidence_ids", ())),
        payload.get("business_oracle"),
        tuple(payload.get("acceptance_criterion_ids", ())),
        tuple(payload.get("test_ids", ())),
    )


def _validate_evidence(record: Evidence) -> None:
    if record.status not in {"verified", "unverified"}:
        raise ValueError("invalid Evidence status")
    if record.line_start < 1 or record.line_end < record.line_start:
        raise ValueError("invalid Evidence line range")
    _hash(record.content_hash, "Evidence content_hash")
    _required(record.subject or "", "Evidence subject")
    _required(record.source_ref or "", "Evidence source_ref")
    if record.redacted_excerpt is not None and len(record.redacted_excerpt.encode("utf-8")) > 4096:
        raise ValueError("Evidence excerpt is too large")
    if not isinstance(record.metadata, dict):
        raise ValueError("Evidence metadata is required")
    redaction = record.metadata.get("redaction")
    limits = record.metadata.get("limits")
    if not isinstance(redaction, dict) or not isinstance(limits, dict):
        raise ValueError("Evidence redaction and limits metadata are required")
    if redaction.get("policy") != "bounded-redacted-v1" or redaction.get("max_bytes") != 4096:
        raise ValueError("invalid Evidence redaction metadata")
    if limits.get("context_bytes") != 1_000_000 or limits.get("report_bytes") != 2_000_000:
        raise ValueError("invalid Evidence limits metadata")


@dataclass(frozen=True)
class TestEffectivenessContext:
    schema_version: str
    requirement_id: str
    intents: tuple[TestIntent, ...]
    scenarios: tuple[TestScenario, ...]
    test_ids: tuple[str, ...]
    target_paths: tuple[str, ...]
    test_paths: tuple[str, ...]
    execution_evidence_ids: tuple[str, ...]
    assertion_evidence_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    evidence: tuple[Evidence, ...]
    artifact_hash: str
    source_version: str = "v0.4"

    @classmethod
    def from_dict(cls, payload: dict[str, Any], max_bytes: int) -> "TestEffectivenessContext":
        if not isinstance(payload, dict):
            raise ValueError("context must be an object")
        if len(canonical_json_bytes(payload)) > max_bytes:
            raise ValueError("context exceeds max_context_bytes")
        if payload.get("schema_version") != "v0.4":
            raise ValueError("v0.4 context requires explicit schema_version v0.4")
        expected_hash = payload.get("artifact_hash")
        if not isinstance(expected_hash, str) or artifact_hash(payload, omit_field="artifact_hash") != expected_hash:
            raise ValueError("context artifact_hash does not match canonical payload")
        requirement_id = payload.get("requirement_id")
        _required(requirement_id, "context requirement_id")
        intents = tuple(_parse_intent(item) for item in payload.get("intents", ()))
        scenarios = tuple(_parse_scenario(item) for item in payload.get("scenarios", ()))
        if not intents or not scenarios:
            raise ValueError("context intents and scenarios are required")
        _unique(tuple(item.id for item in intents), "intent ids", required=True)
        _unique(tuple(item.id for item in scenarios), "scenario ids", required=True)
        if any(item.requirement_id != requirement_id for item in intents):
            raise ValueError("intent requirement does not match context")
        intent_ids = {item.id for item in intents}
        if any(item.intent_id not in intent_ids for item in scenarios):
            raise ValueError("scenario references unknown intent")
        test_ids = _unique(payload.get("test_ids", ()), "test_ids", required=True)
        target_paths = tuple(_relative_path(item, "target path") for item in payload.get("target_paths", ()))
        test_paths = tuple(_relative_path(item, "test path") for item in payload.get("test_paths", ()))
        if not target_paths or not test_paths:
            raise ValueError("target_paths and test_paths are required")
        scenario_test_ids = tuple(test_id for scenario in scenarios for test_id in scenario.test_ids)
        if any(test_id not in test_ids for test_id in scenario_test_ids) or set(test_ids) != set(scenario_test_ids):
            raise ValueError("test_ids must be declared by a scenario")
        evidence_records = tuple(Evidence(**item) for item in payload.get("evidence", ()))
        _unique(tuple(item.id for item in evidence_records), "Evidence ids", required=True)
        for record in evidence_records:
            _validate_evidence(record)
        evidence_by_id = {item.id: item for item in evidence_records}
        evidence_ids = _unique(payload.get("evidence_ids", ()), "context evidence_ids", required=True)
        if not set(evidence_ids) <= set(evidence_by_id):
            raise ValueError("context evidence reference is unresolved")
        all_references = set(evidence_ids)
        all_references.update(item for intent in intents for item in intent.evidence_ids)
        all_references.update(item for scenario in scenarios for item in scenario.evidence_ids)
        execution_ids = _unique(payload.get("execution_evidence_ids", ()), "execution evidence ids", required=True)
        assertion_ids = _unique(payload.get("assertion_evidence_ids", ()), "assertion evidence ids", required=True)
        all_references.update(execution_ids)
        all_references.update(assertion_ids)
        if not all_references <= set(evidence_by_id):
            raise ValueError("context contains an unresolved Evidence reference")
        subjects = {record.subject for record in evidence_records}
        criterion_ids = {criterion for intent in intents for criterion in intent.acceptance_criterion_ids}
        criterion_ids.update(criterion for scenario in scenarios for criterion in scenario.acceptance_criterion_ids)
        risk_ids = {risk for intent in intents for risk in intent.risk_ids}
        if not criterion_ids <= subjects and criterion_ids:
            raise ValueError("acceptance criterion Evidence is unresolved")
        if not risk_ids <= subjects and risk_ids:
            raise ValueError("risk Evidence is unresolved")
        return cls(
            "v0.4",
            requirement_id,
            intents,
            scenarios,
            test_ids,
            target_paths,
            test_paths,
            execution_ids,
            assertion_ids,
            evidence_ids,
            evidence_records,
            expected_hash,
            payload.get("source_version", "v0.4"),
        )

    @classmethod
    def import_v03(cls, payload: dict[str, Any], max_bytes: int) -> "TestEffectivenessContext":
        if payload.get("schema_version") != "v0.3":
            raise ValueError("import_v03 requires schema_version v0.3")
        raise ValueError("v0.3 import requires an explicit enriched context export")

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "schema_version": self.schema_version,
            "requirement_id": self.requirement_id,
            "intents": [
                {
                    "id": item.id,
                    "requirement_id": item.requirement_id,
                    "subject": item.subject,
                    "acceptance_criterion_ids": list(item.acceptance_criterion_ids),
                    "risk_ids": list(item.risk_ids),
                    "observable_behavior": item.observable_behavior,
                    "business_oracle": item.business_oracle,
                    "evidence_ids": list(item.evidence_ids),
                }
                for item in self.intents
            ],
            "scenarios": [
                {
                    "id": item.id,
                    "intent_id": item.intent_id,
                    "name": item.name,
                    "steps": list(item.steps),
                    "expected_outcome": item.expected_outcome,
                    "test_ids": list(item.test_ids),
                    "acceptance_criterion_ids": list(item.acceptance_criterion_ids),
                    "business_oracle": item.business_oracle,
                    "evidence_ids": list(item.evidence_ids),
                }
                for item in self.scenarios
            ],
            "test_ids": list(self.test_ids),
            "target_paths": list(self.target_paths),
            "test_paths": list(self.test_paths),
            "execution_evidence_ids": list(self.execution_evidence_ids),
            "assertion_evidence_ids": list(self.assertion_evidence_ids),
            "evidence_ids": list(self.evidence_ids),
            "evidence": [item.to_dict(include_empty_extensions=True) for item in self.evidence],
        }
        if self.source_version != "v0.4":
            payload["source_version"] = self.source_version
        payload["artifact_hash"] = artifact_hash(payload, omit_field="artifact_hash")
        return payload


@dataclass(frozen=True)
class Mutant:
    mutant_id: str
    path: str
    line: int
    operator: str
    original: str
    mutated: str
    normalized_status: str
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _required(self.mutant_id, "mutant id")
        _relative_path(self.path, "mutant path")
        if self.line < 1:
            raise ValueError("mutant line must be positive")
        _required(self.operator, "mutant operator")
        if self.normalized_status not in MUTANT_STATUSES:
            raise ValueError("invalid mutant status")
        _unique(self.evidence_ids, "mutant evidence", required=True)


@dataclass(frozen=True)
class MutationResult:
    run_id: str
    mutant_id: str
    outcome: str
    executed_test_ids: tuple[str, ...]
    killing_test_ids: tuple[str, ...]
    duration_ms: int
    stdout_hash: str | None
    stderr_hash: str | None
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.outcome not in OUTCOMES:
            raise ValueError("invalid mutation outcome")
        if self.duration_ms < 0:
            raise ValueError("mutation duration cannot be negative")
        _unique(self.executed_test_ids, "executed test ids")
        _unique(self.killing_test_ids, "killing test ids")
        if not set(self.killing_test_ids) <= set(self.executed_test_ids):
            raise ValueError("killing test ids must be executed")
        if self.outcome == "killed" and not self.killing_test_ids:
            raise ValueError("killed mutation requires a killing test")
        if self.outcome != "killed" and self.killing_test_ids:
            raise ValueError("only killed mutations have killing tests")
        if self.outcome == "not_run" and self.executed_test_ids:
            raise ValueError("not_run mutation cannot have executed tests")
        for value in (self.stdout_hash, self.stderr_hash):
            if value is not None:
                _hash(value, "mutation output hash")
        _unique(self.evidence_ids, "mutation result evidence", required=True)


@dataclass(frozen=True)
class MutationRun:
    run_id: str
    assessment_id: str
    backend: str
    repository_revision: str
    target_paths: tuple[str, ...]
    selected_test_paths: tuple[str, ...]
    selected_test_ids: tuple[str, ...]
    process_status: str
    observation_status: str
    mutant_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    tool_version: str | None = None
    report_hash: str | None = None

    def __post_init__(self) -> None:
        for value, name in ((self.run_id, "run id"), (self.assessment_id, "assessment id"), (self.backend, "backend"), (self.repository_revision, "repository revision")):
            _required(value, name)
        if self.process_status not in PROCESS_STATUSES:
            raise ValueError("invalid process status")
        if self.observation_status not in OBSERVATION_STATUSES:
            raise ValueError("invalid observation status")
        _unique(tuple(_relative_path(item, "target path") for item in self.target_paths), "target paths", required=True)
        _unique(tuple(_relative_path(item, "selected test path") for item in self.selected_test_paths), "selected test paths", required=True)
        _unique(self.selected_test_ids, "selected test ids", required=True)
        _unique(self.mutant_ids, "mutant ids")
        _unique(self.evidence_ids, "run evidence", required=True)
        if self.report_hash is not None:
            _hash(self.report_hash, "mutation report hash")


@dataclass(frozen=True)
class MutationTraceLink:
    run_id: str
    mutant_id: str
    requirement_id: str | None
    intent_id: str | None
    scenario_id: str | None
    business_oracle: str | None
    mapping_status: str
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _required(self.run_id, "trace run id")
        _required(self.mutant_id, "trace mutant id")
        if self.mapping_status not in MAPPING_STATUSES:
            raise ValueError("invalid mapping status")
        if self.mapping_status == "unmapped" and any(value is not None for value in (self.requirement_id, self.intent_id, self.scenario_id, self.business_oracle)):
            raise ValueError("unmapped trace link cannot contain semantic placeholders")
        _unique(self.evidence_ids, "trace link evidence", required=True)


@dataclass(frozen=True)
class EffectivenessScore:
    eligible_mutants: int
    killed_mutants: int
    survived_mutants: int
    timeout_mutants: int
    error_mutants: int
    not_run_mutants: int
    score: float | None
    score_status: str
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.eligible_mutants != self.killed_mutants + self.survived_mutants:
            raise ValueError("eligible score count invariant failed")
        if min(self.eligible_mutants, self.killed_mutants, self.survived_mutants, self.timeout_mutants, self.error_mutants, self.not_run_mutants) < 0:
            raise ValueError("score counts cannot be negative")
        if self.score_status not in {"computed", "not_computable", "incomplete"}:
            raise ValueError("invalid score status")
        if self.score is not None and not 0 <= self.score <= 1:
            raise ValueError("score must be between zero and one")
        _unique(self.evidence_ids, "score evidence")

    @property
    def eligible(self) -> int:
        return self.eligible_mutants


@dataclass(frozen=True)
class FakeTestSignal:
    signal_id: str
    signal_kind: str
    severity: str
    message: str
    source: str
    verification_status: str
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _required(self.signal_id, "signal id")
        if self.signal_kind not in SIGNAL_KINDS or self.severity not in SEVERITIES:
            raise ValueError("invalid signal kind or severity")
        _required(self.message, "signal message")
        _required(self.source, "signal source")
        if self.verification_status not in {"verified", "unverified"}:
            raise ValueError("invalid signal verification status")
        _unique(self.evidence_ids, "signal evidence", required=True)


@dataclass(frozen=True)
class MutationGateResult:
    decision: str
    reasons: tuple[str, ...]
    input_complete: bool
    assessable_run: bool
    quality_failure: bool
    clean_pass: bool


@dataclass
class TestEffectivenessAssessment:
    assessment_id: str
    requirement_id: str
    mutation_run: MutationRun | None
    score: EffectivenessScore
    survivor_links: tuple[MutationTraceLink, ...] = ()
    signals: tuple[FakeTestSignal, ...] = ()
    decision: str = "incomplete"
    termination_reason: str = "INSUFFICIENT_EVIDENCE"
    gate: MutationGateResult | None = None
    evidence_ids: tuple[str, ...] = ()
    loop_trace: tuple[LoopTrace, ...] = ()
    budget: ExecutionBudget = field(default_factory=ExecutionBudget.v04_defaults)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "v0.4",
            "assessment_id": self.assessment_id,
            "requirement_id": self.requirement_id,
            "mutation_run": _json_ready(self.mutation_run),
            "score": _json_ready(self.score),
            "survivor_links": _json_ready(self.survivor_links),
            "signals": _json_ready(self.signals),
            "decision": self.decision,
            "termination_reason": self.termination_reason,
            "gate": _json_ready(self.gate),
            "evidence_ids": list(self.evidence_ids),
            "loop_trace": [loop_trace_to_dict(item, include_v04=True) for item in self.loop_trace],
            "budget": budget_to_dict(self.budget, include_v04=True),
        }


def score_results(results: Sequence[MutationResult], evidence_ids: Sequence[str]) -> EffectivenessScore:
    counts = {outcome: 0 for outcome in OUTCOMES}
    for result in results:
        counts[result.outcome] += 1
    eligible = counts["killed"] + counts["survived"]
    if eligible == 0:
        value = None
        status = "not_computable"
    else:
        value = float((Decimal(counts["killed"]) / Decimal(eligible)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))
        status = "computed"
    return EffectivenessScore(
        eligible,
        counts["killed"],
        counts["survived"],
        counts["timeout"],
        counts["error"],
        counts["not_run"],
        value,
        status,
        tuple(evidence_ids),
    )


def _valid_gate_evidence(records: Sequence[Evidence]) -> bool:
    if not records:
        return False
    try:
        for record in records:
            _validate_evidence(record)
    except ValueError:
        return False
    return all(record.status == "verified" for record in records)


def evaluate_mutation_gate(
    context_valid: bool,
    run: MutationRun | None,
    score: EffectivenessScore,
    links: Sequence[MutationTraceLink],
    signals: Sequence[FakeTestSignal],
    threshold: float | None,
    execution_evidence: Sequence[Evidence],
    assertion_evidence: Sequence[Evidence],
    termination_reason: str,
) -> MutationGateResult:
    assessable_run = run is not None and (
        run.process_status == "completed"
        or (run.process_status == "partial" and run.observation_status == "complete")
    )
    missing_oracle = any(signal.signal_kind == "oracle_missing" for signal in signals)
    input_complete = bool(
        context_valid
        and run is not None
        and threshold is not None
        and score.eligible_mutants > 0
        and assessable_run
        and termination_reason == "EVIDENCE_SUFFICIENT"
        and not missing_oracle
        and _valid_gate_evidence(execution_evidence)
        and _valid_gate_evidence(assertion_evidence)
    )
    verified_quality_signals = [signal for signal in signals if signal.verification_status == "verified"]
    quality_failure = bool(
        input_complete
        and (
            (score.score is not None and threshold is not None and score.score < threshold)
            or any(signal.severity in {"high", "critical"} for signal in verified_quality_signals)
        )
    )
    clean_pass = bool(
        input_complete
        and run is not None
        and run.process_status == "completed"
        and score.score is not None
        and threshold is not None
        and score.score >= threshold
        and score.timeout_mutants == 0
        and score.error_mutants == 0
        and score.not_run_mutants == 0
        and not any(signal.severity in {"high", "critical"} for signal in verified_quality_signals)
        and all(link.mapping_status == "verified" for link in links)
    )
    if not input_complete:
        decision = "incomplete"
        reasons = ("inputs or observation are insufficient",)
    elif quality_failure:
        decision = "fail"
        reasons = ("effectiveness quality threshold or verified high-risk signal failed",)
    elif clean_pass:
        decision = "pass"
        reasons = ("completed clean run met the explicit threshold",)
    else:
        decision = "warn"
        reasons = ("assessable run has partial process or unresolved effectiveness limitations",)
    return MutationGateResult(decision, reasons, input_complete, bool(assessable_run), quality_failure, clean_pass)
