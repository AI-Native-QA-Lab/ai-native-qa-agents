"""Deterministic, bounded v0.4 Test Effectiveness service loop."""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import subprocess
import time
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from .effectiveness import (
    FakeTestSignal,
    MutationResult,
    MutationRun,
    MutationTraceLink,
    TestEffectivenessAssessment,
    TestEffectivenessContext,
    artifact_hash,
    evaluate_mutation_gate,
    score_results,
    _validate_evidence,
)
from .mutation_adapters import OfflineMutationReportAdapter
from .mutation_backends import (
    MutationBackend,
    MutationBackendResult,
    MutationConfigurationError,
    MutationError,
    MutationExecutionError,
    MutationInputError,
    MutationRequest,
    MutationUnavailableError,
    MutationUnsupportedError,
)
from .review import Evidence
from .runtime import ExecutionBudget, LoopTrace, PermissionContext, PermissionResult
from .trace_store import SQLiteTraceStore
from .model_runtime import ModelResponse


TERMINATION_REASONS = {
    "EVIDENCE_SUFFICIENT",
    "INSUFFICIENT_EVIDENCE",
    "BUDGET_EXHAUSTED",
    "TIMEOUT",
    "HUMAN_APPROVAL_REQUIRED",
    "ERROR",
}

MODEL_TASK_TYPE = "effectiveness-survivor-mapping"
MODEL_LINK_KEYS = (
    "mutant_id",
    "requirement_id",
    "intent_id",
    "scenario_id",
    "oracle",
    "rationale",
)
MODEL_LINK_KEY_SET = set(MODEL_LINK_KEYS)


def validate_model_mapping(
    payload: dict[str, Any], known_ids: dict[str, set[str]]
) -> list[dict[str, str | None]]:
    """Accept only the bounded, exact survivor-link response shape."""

    if not isinstance(payload, dict) or set(payload) != {"links"}:
        return []
    raw_links = payload.get("links")
    if not isinstance(raw_links, list):
        return []

    id_fields = {
        "mutant_id": "mutant_ids",
        "requirement_id": "requirement_ids",
        "intent_id": "intent_ids",
        "scenario_id": "scenario_ids",
    }
    accepted: list[dict[str, str | None]] = []
    seen_mutants: set[str] = set()
    for raw_link in raw_links:
        if not isinstance(raw_link, dict) or set(raw_link) != MODEL_LINK_KEY_SET:
            return []
        normalized: dict[str, str | None] = {}
        for key in MODEL_LINK_KEYS:
            value = raw_link.get(key)
            if key == "rationale":
                if not isinstance(value, str) or not value.strip():
                    return []
                normalized[key] = value.strip()
                continue
            if value is not None and (not isinstance(value, str) or not value.strip()):
                return []
            normalized[key] = value.strip() if isinstance(value, str) else None

        mutant_id = normalized["mutant_id"]
        if mutant_id is None or mutant_id in seen_mutants:
            return []
        seen_mutants.add(mutant_id)
        for field_name, id_group in id_fields.items():
            value = normalized[field_name]
            if value is not None and value not in known_ids.get(id_group, set()):
                return []
        accepted.append(normalized)
    return accepted


@dataclass(frozen=True)
class TestEffectivenessRequest:
    requirement_id: str
    repository: Path
    context: TestEffectivenessContext | None
    mutation_report: Path | None
    backend: MutationBackend | None
    min_score: float | None
    budget: ExecutionBudget


def resolve_repository_revision(repository: Path) -> str:
    root = repository.resolve()
    if not root.is_dir():
        raise ValueError("repository must be a directory")
    if (root / ".git").exists():
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        revision = completed.stdout.strip()
        if completed.returncode == 0 and revision:
            return "git:" + revision
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return "tree:" + digest.hexdigest()


def _agent_evidence(evidence_id: str, subject: str, message: str, iteration: int) -> Evidence:
    content_hash = "sha256:" + hashlib.sha256(message.encode("utf-8")).hexdigest()
    return Evidence(
        evidence_id,
        "backend_capability" if subject.startswith("backend") else "test_context",
        subject,
        1,
        1,
        content_hash,
        provider="agent-runtime",
        extractor="v0.4-service",
        subject=subject,
        source_ref=subject + "#L1",
        metadata={
            "redaction": {"applied": False, "policy": "bounded-redacted-v1", "max_bytes": 4096},
            "limits": {"context_bytes": 1_000_000, "report_bytes": 2_000_000},
        },
        loop_iteration=iteration,
    )


def _unique_ids(*groups: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(item for group in groups for item in group))


class TestEffectivenessService:
    def __init__(self, store: SQLiteTraceStore | None = None, model_mapper: "SurvivorMappingProvider | None" = None) -> None:
        self.store = store
        self.model_mapper = model_mapper

    def assess(self, request: TestEffectivenessRequest) -> TestEffectivenessAssessment:
        started = time.monotonic()
        try:
            request.budget.validate(v04=True)
        except ValueError:
            assessment_id = self._assessment_id(request, None)
            return self._incomplete(assessment_id, request.requirement_id, request.budget, "ERROR")

        assessment_id = self._assessment_id(request, request.context)
        traces: list[LoopTrace] = []
        agent_evidence: list[Evidence] = []
        tool_calls = 0
        context_valid = self._context_valid(request)
        run: MutationRun | None = None
        result_values: tuple[MutationResult, ...] = ()
        survivor_links: tuple[MutationTraceLink, ...] = ()
        signals: tuple[FakeTestSignal, ...] = ()
        provider_evidence: tuple[Evidence, ...] = ()
        model_calls = 0
        termination_reason = "INSUFFICIENT_EVIDENCE"

        def record_phase(
            phase: str,
            *,
            status: str = "completed",
            permission_id: str | None = None,
            evidence_ids: tuple[str, ...] = (),
            termination: str | None = None,
        ) -> bool:
            if len(traces) >= request.budget.max_iterations:
                return False
            iteration = len(traces) + 1
            observation_id = f"OBS-{assessment_id}-{iteration:02d}"
            traces.append(
                LoopTrace(
                    iteration,
                    phase.lower(),
                    status,
                    observation_id,
                    assessment_id,
                    phase,
                    permission_id,
                    list(evidence_ids),
                    termination,
                )
            )
            return True

        def consume_tool() -> bool:
            nonlocal tool_calls
            if tool_calls >= request.budget.max_tool_calls:
                return False
            tool_calls += 1
            return True

        def timed_out() -> bool:
            return time.monotonic() - started >= request.budget.timeout_seconds

        if not record_phase("UNDERSTAND"):
            return self._incomplete(assessment_id, request.requirement_id, request.budget, "BUDGET_EXHAUSTED")
        if not context_valid or request.min_score is None or (request.mutation_report is None) == (request.backend is None):
            traces[-1] = replace(traces[-1], status="terminated", termination_reason="INSUFFICIENT_EVIDENCE")
            return self._finish(
                request,
                assessment_id,
                context_valid,
                None,
                score_results((), ()),
                (),
                (),
                traces,
                agent_evidence,
                provider_evidence,
                "INSUFFICIENT_EVIDENCE",
            )

        read_permission = PermissionResult("READ", True, "read-only context access allowed", f"EV-PERM-{assessment_id}-READ", False)
        agent_evidence.append(_agent_evidence(read_permission.evidence_id or "EV-PERM-READ", "permission:READ", read_permission.reason, 1))
        if not consume_tool() or not record_phase("SELECT", permission_id=read_permission.evidence_id, evidence_ids=(read_permission.evidence_id or "",)):
            return self._finish(request, assessment_id, context_valid, None, score_results((), ()), (), (), traces, agent_evidence, provider_evidence, "BUDGET_EXHAUSTED")
        if timed_out():
            return self._finish(request, assessment_id, context_valid, None, score_results((), ()), (), (), traces, agent_evidence, provider_evidence, "TIMEOUT")

        execute_permission = PermissionResult("EXECUTE_MUTATION", True, "controlled mutation observation allowed", f"EV-PERM-{assessment_id}-EXECUTE", False)
        agent_evidence.append(_agent_evidence(execute_permission.evidence_id or "EV-PERM-EXECUTE", "permission:EXECUTE_MUTATION", execute_permission.reason, 2))
        if not consume_tool() or not record_phase("MUTATE", permission_id=execute_permission.evidence_id, evidence_ids=(execute_permission.evidence_id or "",)):
            return self._finish(request, assessment_id, context_valid, None, score_results((), ()), (), (), traces, agent_evidence, provider_evidence, "BUDGET_EXHAUSTED")

        try:
            repository_revision = resolve_repository_revision(request.repository)
            if request.mutation_report is not None:
                if not consume_tool():
                    return self._finish(request, assessment_id, context_valid, None, score_results((), ()), (), (), traces, agent_evidence, provider_evidence, "BUDGET_EXHAUSTED")
                provider_result = OfflineMutationReportAdapter().parse(request.mutation_report, repository_revision, request.budget)
            else:
                capability = request.backend.detect(request.repository)  # type: ignore[union-attr]
                if capability.status != "available":
                    provider_evidence = tuple(capability.evidence)
                    return self._finish(request, assessment_id, context_valid, None, score_results((), ()), (), (), traces, agent_evidence, provider_evidence, "INSUFFICIENT_EVIDENCE")
                if not consume_tool():
                    return self._finish(request, assessment_id, context_valid, None, score_results((), ()), (), (), traces, agent_evidence, provider_evidence, "BUDGET_EXHAUSTED")
                permission_context = PermissionContext(request.repository.resolve(), None, ("READ", "EXECUTE_MUTATION", "MODEL_SURVIVOR_MAPPING"), (), 32, request.budget.max_context_bytes or 1_000_000)
                provider_result = request.backend.run(  # type: ignore[union-attr]
                    MutationRequest(
                        request.repository.resolve(),
                        repository_revision,
                        request.context.target_paths,
                        request.context.test_ids,
                        request.context.test_paths,
                        request.budget.timeout_seconds,
                        request.budget.max_mutants or 500,
                        permission_context,
                    )
                )
        except (MutationInputError, MutationUnavailableError, MutationUnsupportedError, MutationConfigurationError, MutationExecutionError, OSError, ValueError):
            traces[-1] = replace(traces[-1], status="terminated", termination_reason="INSUFFICIENT_EVIDENCE")
            return self._finish(request, assessment_id, context_valid, None, score_results((), ()), (), (), traces, agent_evidence, provider_evidence, "INSUFFICIENT_EVIDENCE")
        except Exception:
            traces[-1] = replace(traces[-1], status="terminated", termination_reason="ERROR")
            return self._finish(request, assessment_id, context_valid, None, score_results((), ()), (), (), traces, agent_evidence, provider_evidence, "ERROR")

        provider_evidence = tuple(provider_result.evidence)
        if not record_phase("OBSERVE", evidence_ids=tuple(item.id for item in provider_evidence)):
            return self._finish(request, assessment_id, context_valid, None, score_results((), ()), (), (), traces, agent_evidence, provider_evidence, "BUDGET_EXHAUSTED")
        if request.mutation_report is not None:
            report_target_paths = tuple(item.path for item in provider_result.mutants)
            report_targets = {item for item in report_target_paths if item}
            if not report_targets <= set(request.context.target_paths) or not set(request.context.test_ids) >= {test_id for result in provider_result.results for test_id in result.executed_test_ids}:
                return self._finish(request, assessment_id, context_valid, None, score_results((), ()), (), (), traces, agent_evidence, provider_evidence, "INSUFFICIENT_EVIDENCE")
        run_id = "RUN-" + artifact_hash({"assessment_id": assessment_id, "report": provider_result.raw_report_hash or "backend"})[7:23]
        run = MutationRun(
            run_id,
            assessment_id,
            provider_result.backend,
            repository_revision,
            request.context.target_paths,
            request.context.test_paths,
            request.context.test_ids,
            provider_result.process_status,
            provider_result.observation_status,
            tuple(item.mutant_id for item in provider_result.mutants),
            tuple(item.id for item in provider_evidence),
        )
        result_values = tuple(replace(item, run_id=run_id) for item in provider_result.results)
        if not record_phase("MAP", evidence_ids=tuple(item.id for item in provider_evidence)):
            return self._finish(request, assessment_id, context_valid, run, score_results(result_values, tuple(item.id for item in provider_evidence)), (), (), traces, agent_evidence, provider_evidence, "BUDGET_EXHAUSTED")
        survivor_links = self._map_survivors(request.context, run, result_values)
        survivor_links, model_calls = self._apply_optional_model_mapping(
            request,
            assessment_id,
            run,
            result_values,
            survivor_links,
            agent_evidence,
            traces,
            model_calls,
        )
        signals = self._signals(request.context, survivor_links)
        if not record_phase("EVALUATE", evidence_ids=tuple(item.id for item in provider_evidence)):
            return self._finish(request, assessment_id, context_valid, run, score_results(result_values, tuple(item.id for item in provider_evidence)), survivor_links, signals, traces, agent_evidence, provider_evidence, "BUDGET_EXHAUSTED")
        score = score_results(result_values, tuple(item.id for item in provider_evidence))
        if not record_phase("VERIFY", evidence_ids=_unique_ids(tuple(item.id for item in request.context.evidence), tuple(item.id for item in provider_evidence))):
            return self._finish(request, assessment_id, context_valid, run, score, survivor_links, signals, traces, agent_evidence, provider_evidence, "BUDGET_EXHAUSTED")
        execution_evidence = [item for item in request.context.evidence if item.id in request.context.execution_evidence_ids]
        assertion_evidence = [item for item in request.context.evidence if item.id in request.context.assertion_evidence_ids]
        verified_inputs = bool(execution_evidence and assertion_evidence) and all(
            item.status == "verified" for item in (*execution_evidence, *assertion_evidence)
        )
        termination_reason = "EVIDENCE_SUFFICIENT" if provider_result.observation_status == "complete" and provider_result.process_status in {"completed", "partial"} and verified_inputs else "INSUFFICIENT_EVIDENCE"
        if not record_phase("GATE", evidence_ids=_unique_ids(tuple(item.id for item in request.context.evidence), tuple(item.id for item in provider_evidence))):
            termination_reason = "BUDGET_EXHAUSTED"
        return self._finish(
            request,
            assessment_id,
            context_valid,
            run,
            score,
            survivor_links,
            signals,
            traces,
            agent_evidence,
            provider_evidence,
            termination_reason,
            execution_evidence,
            assertion_evidence,
            tuple(provider_result.mutants),
            result_values,
        )

    def _assessment_id(self, request: TestEffectivenessRequest, context: TestEffectivenessContext | None) -> str:
        report_hash = None
        if request.mutation_report is not None and request.mutation_report.exists():
            report_hash = hashlib.sha256(request.mutation_report.read_bytes()).hexdigest()
        value = {"requirement_id": request.requirement_id, "context": context.artifact_hash if context else None, "report": report_hash, "threshold": request.min_score}
        return "ASSESS-" + artifact_hash(value)[7:23]

    def _context_valid(self, request: TestEffectivenessRequest) -> bool:
        context = request.context
        if context is None or context.requirement_id != request.requirement_id:
            return False
        try:
            for item in context.evidence:
                _validate_evidence(item)
        except ValueError:
            return False
        return bool(context.execution_evidence_ids and context.assertion_evidence_ids)

    def _incomplete(self, assessment_id: str, requirement_id: str, budget: ExecutionBudget, reason: str) -> TestEffectivenessAssessment:
        score = score_results((), ())
        gate = evaluate_mutation_gate(False, None, score, (), (), None, (), (), reason)
        return TestEffectivenessAssessment(assessment_id, requirement_id, None, score, (), (), gate.decision, reason, gate, (), (), budget)

    def _finish(
        self,
        request: TestEffectivenessRequest,
        assessment_id: str,
        context_valid: bool,
        run: MutationRun | None,
        score,
        links: tuple[MutationTraceLink, ...],
        signals: tuple[FakeTestSignal, ...],
        traces: list[LoopTrace],
        agent_evidence: list[Evidence],
        provider_evidence: tuple[Evidence, ...],
        termination_reason: str,
        execution_evidence: list[Evidence] | None = None,
        assertion_evidence: list[Evidence] | None = None,
        mutants: tuple[Any, ...] = (),
        results: tuple[MutationResult, ...] = (),
    ) -> TestEffectivenessAssessment:
        context = request.context
        execution = execution_evidence or ([item for item in context.evidence if item.id in context.execution_evidence_ids] if context else [])
        assertion = assertion_evidence or ([item for item in context.evidence if item.id in context.assertion_evidence_ids] if context else [])
        gate = evaluate_mutation_gate(context_valid, run, score, links, signals, request.min_score, execution, assertion, termination_reason)
        evidence_ids = _unique_ids(
            tuple(item.id for item in context.evidence) if context else (),
            tuple(item.id for item in provider_evidence),
            tuple(item.id for item in agent_evidence),
            tuple(evidence_id for link in links for evidence_id in link.evidence_ids),
        )
        assessment = TestEffectivenessAssessment(assessment_id, request.requirement_id, run, score, links, signals, gate.decision, termination_reason, gate, evidence_ids, tuple(traces), request.budget)
        if self.store is not None:
            if context is not None:
                self.store.save_test_context(context)
            if agent_evidence:
                self.store.save_evidence(agent_evidence)
            if provider_evidence:
                self.store.save_evidence(provider_evidence)
            if run is not None:
                self.store.save_mutation(run, mutants, results, links)
            self.store.save_assessment(assessment)
        return assessment

    def _map_survivors(self, context: TestEffectivenessContext, run: MutationRun, results: tuple[MutationResult, ...]) -> tuple[MutationTraceLink, ...]:
        intent_by_id = {item.id: item for item in context.intents}
        evidence_by_id = {item.id: item for item in context.evidence}
        links: list[MutationTraceLink] = []
        for result in results:
            if result.outcome != "survived":
                continue
            executed_ids = set(result.executed_test_ids) or set(run.selected_test_ids)
            candidates = [scenario for scenario in context.scenarios if executed_ids.intersection(scenario.test_ids)]
            if len(candidates) != 1:
                links.append(MutationTraceLink(run.run_id, result.mutant_id, None, None, None, None, "unmapped", result.evidence_ids))
                continue
            scenario = candidates[0]
            intent = intent_by_id[scenario.intent_id]
            evidence_ids = _unique_ids(result.evidence_ids, scenario.evidence_ids, intent.evidence_ids)
            verified = bool(
                scenario.business_oracle
                and intent.business_oracle
                and all(evidence_by_id.get(identifier, None) is not None and evidence_by_id[identifier].status == "verified" for identifier in evidence_ids if identifier in evidence_by_id)
            )
            links.append(MutationTraceLink(run.run_id, result.mutant_id, context.requirement_id, intent.id, scenario.id, scenario.business_oracle or intent.business_oracle, "verified" if verified else "unverified", evidence_ids))
        return tuple(links)

    def _signals(self, context: TestEffectivenessContext, links: tuple[MutationTraceLink, ...]) -> tuple[FakeTestSignal, ...]:
        signals: list[FakeTestSignal] = []
        for intent in context.intents:
            if not intent.observable_behavior or not intent.business_oracle:
                signals.append(FakeTestSignal("SIG-ORACLE-" + intent.id, "oracle_missing", "high", "Business Oracle or observable behavior is missing", "deterministic-context", "verified", intent.evidence_ids))
        for link in links:
            signals.append(FakeTestSignal("SIG-SURVIVOR-" + link.mutant_id, "mutation_survivor", "medium", "Mutation survivor requires effectiveness review", "deterministic-mutation", "verified" if link.mapping_status == "verified" else "unverified", link.evidence_ids))
        return tuple(signals)

    def _apply_optional_model_mapping(
        self,
        request: TestEffectivenessRequest,
        assessment_id: str,
        run: MutationRun,
        results: tuple[MutationResult, ...],
        deterministic_links: tuple[MutationTraceLink, ...],
        agent_evidence: list[Evidence],
        traces: list[LoopTrace],
        model_calls: int,
    ) -> tuple[tuple[MutationTraceLink, ...], int]:
        """Use one explicitly injected mapper without changing runtime truth."""

        if self.model_mapper is None or model_calls >= request.budget.max_model_calls:
            return deterministic_links, model_calls
        survivor_ids = tuple(
            link.mutant_id
            for link in deterministic_links
            if link.mapping_status == "unmapped"
        )
        if not survivor_ids:
            return deterministic_links, model_calls
        try:
            bounded_context = self._bounded_model_context(request.context, survivor_ids, request.budget)
            permission = PermissionResult(
                "MODEL_SURVIVOR_MAPPING",
                True,
                "explicit optional survivor mapping is allowed",
                f"EV-PERM-{assessment_id}-MODEL",
                False,
            )
            agent_evidence.append(
                _agent_evidence(
                    permission.evidence_id or "EV-PERM-MODEL",
                    "permission:MODEL_SURVIVOR_MAPPING",
                    permission.reason,
                    len(traces),
                )
            )
            response = self.model_mapper.map(bounded_context, survivor_ids)
            model_calls += 1
            if not isinstance(response, ModelResponse) or not isinstance(response.structured_output, dict):
                return deterministic_links, model_calls
            known_ids = {
                "mutant_ids": set(survivor_ids),
                "requirement_ids": {request.context.requirement_id},
                "intent_ids": {item.id for item in request.context.intents},
                "scenario_ids": {item.id for item in request.context.scenarios},
            }
            mappings = validate_model_mapping(response.structured_output, known_ids)
            if not mappings:
                return deterministic_links, model_calls
            return self._merge_model_links(deterministic_links, results, run, mappings), model_calls
        except Exception:
            model_calls += 1
            return deterministic_links, model_calls

    def _bounded_model_context(
        self,
        context: TestEffectivenessContext,
        survivor_ids: tuple[str, ...],
        budget: ExecutionBudget,
    ) -> dict[str, Any]:
        def bounded(value: str | None, limit: int = 512) -> str | None:
            if value is None:
                return None
            return value[:limit]

        payload: dict[str, Any] = {
            "task_type": MODEL_TASK_TYPE,
            "requirement_id": context.requirement_id,
            "survivor_ids": list(survivor_ids),
            "intents": [
                {
                    "id": item.id,
                    "requirement_id": item.requirement_id,
                    "observable_behavior": bounded(item.observable_behavior),
                    "business_oracle": bounded(item.business_oracle),
                }
                for item in context.intents
            ],
            "scenarios": [
                {
                    "id": item.id,
                    "intent_id": item.intent_id,
                    "test_ids": list(item.test_ids),
                    "business_oracle": bounded(item.business_oracle),
                }
                for item in context.scenarios
            ],
            "evidence": [
                {
                    "id": item.id,
                    "status": item.status,
                    "redacted_excerpt": bounded(item.redacted_excerpt),
                }
                for item in context.evidence
                if item.redacted_excerpt is not None
            ],
        }
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        if budget.max_context_bytes is None or len(encoded) > budget.max_context_bytes:
            raise ValueError("bounded model context exceeds max_context_bytes")
        return payload

    def _merge_model_links(
        self,
        deterministic_links: tuple[MutationTraceLink, ...],
        results: tuple[MutationResult, ...],
        run: MutationRun,
        mappings: list[dict[str, str | None]],
    ) -> tuple[MutationTraceLink, ...]:
        result_by_mutant = {item.mutant_id: item for item in results}
        mapping_by_mutant = {item["mutant_id"]: item for item in mappings if item["mutant_id"]}
        merged: list[MutationTraceLink] = []
        for link in deterministic_links:
            mapping = mapping_by_mutant.get(link.mutant_id)
            if link.mapping_status != "unmapped" or mapping is None:
                merged.append(link)
                continue
            result = result_by_mutant.get(link.mutant_id)
            evidence_ids = _unique_ids(
                link.evidence_ids,
                result.evidence_ids if result is not None else (),
                run.evidence_ids,
            )
            merged.append(
                MutationTraceLink(
                    run.run_id,
                    link.mutant_id,
                    mapping["requirement_id"],
                    mapping["intent_id"],
                    mapping["scenario_id"],
                    mapping["oracle"],
                    "unverified",
                    evidence_ids,
                )
            )
        return tuple(merged)


@runtime_checkable
class SurvivorMappingProvider(Protocol):
    def map(self, context: dict[str, Any], survivor_ids: tuple[str, ...]) -> ModelResponse: ...
