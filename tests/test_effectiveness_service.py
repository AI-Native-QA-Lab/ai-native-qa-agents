import json
from dataclasses import replace
from pathlib import Path


def test_missing_context_stops_before_backend(tmp_path) -> None:
    from qa_agent.effectiveness_service import TestEffectivenessRequest, TestEffectivenessService
    from qa_agent.runtime import ExecutionBudget

    class Backend:
        called = False

        def detect(self, repository):
            self.called = True
            raise AssertionError("backend must not run")

        def run(self, request):
            self.called = True
            raise AssertionError("backend must not run")

    backend = Backend()
    assessment = TestEffectivenessService().assess(
        TestEffectivenessRequest("REQ-1", tmp_path, None, None, backend, 0.8, ExecutionBudget.v04_defaults())
    )
    assert assessment.decision == "incomplete"
    assert assessment.termination_reason == "INSUFFICIENT_EVIDENCE"
    assert backend.called is False


def test_exact_identity_creates_verified_survivor_link(tmp_path, valid_context, valid_report, monkeypatch) -> None:
    import qa_agent.effectiveness_service as effectiveness_service
    from qa_agent.effectiveness_service import TestEffectivenessRequest, TestEffectivenessService
    from qa_agent.runtime import ExecutionBudget

    monkeypatch.setattr(effectiveness_service, "resolve_repository_revision", lambda _: "REV-1")
    assessment = TestEffectivenessService().assess(
        TestEffectivenessRequest("REQ-1", tmp_path, valid_context, valid_report, None, 0.8, ExecutionBudget.v04_defaults())
    )
    assert assessment.termination_reason == "EVIDENCE_SUFFICIENT"
    assert assessment.decision == "fail"
    assert all(link.mapping_status == "verified" for link in assessment.survivor_links)


def test_service_preserves_fixed_phase_order(tmp_path, valid_context, valid_report, monkeypatch) -> None:
    import qa_agent.effectiveness_service as effectiveness_service
    from qa_agent.effectiveness_service import TestEffectivenessRequest, TestEffectivenessService
    from qa_agent.runtime import ExecutionBudget

    monkeypatch.setattr(effectiveness_service, "resolve_repository_revision", lambda _: "REV-1")
    assessment = TestEffectivenessService().assess(TestEffectivenessRequest("REQ-1", tmp_path, valid_context, valid_report, None, 0.8, ExecutionBudget.v04_defaults()))
    assert [item.phase for item in assessment.loop_trace] == [
        "UNDERSTAND",
        "SELECT",
        "MUTATE",
        "OBSERVE",
        "MAP",
        "EVALUATE",
        "VERIFY",
        "GATE",
    ]
    assert all(item.observation_id for item in assessment.loop_trace)


def test_revision_conflict_fails_closed(tmp_path, valid_context, valid_report, monkeypatch) -> None:
    import qa_agent.effectiveness_service as effectiveness_service
    from qa_agent.effectiveness_service import TestEffectivenessRequest, TestEffectivenessService
    from qa_agent.runtime import ExecutionBudget

    monkeypatch.setattr(effectiveness_service, "resolve_repository_revision", lambda _: "REV-2")
    assessment = TestEffectivenessService().assess(TestEffectivenessRequest("REQ-1", tmp_path, valid_context, valid_report, None, 0.8, ExecutionBudget.v04_defaults()))
    assert assessment.decision == "incomplete"
    assert assessment.termination_reason == "INSUFFICIENT_EVIDENCE"
    assert assessment.mutation_run is None


def test_budget_exhaustion_prevents_mutation(tmp_path, valid_context, valid_report, monkeypatch) -> None:
    import qa_agent.effectiveness_service as effectiveness_service
    from qa_agent.effectiveness_service import TestEffectivenessRequest, TestEffectivenessService
    from qa_agent.runtime import ExecutionBudget

    monkeypatch.setattr(effectiveness_service, "resolve_repository_revision", lambda _: "REV-1")
    budget = ExecutionBudget.v04_defaults()
    budget.max_iterations = 2
    assessment = TestEffectivenessService().assess(TestEffectivenessRequest("REQ-1", tmp_path, valid_context, valid_report, None, 0.8, budget))
    assert assessment.decision == "incomplete"
    assert assessment.termination_reason == "BUDGET_EXHAUSTED"
    assert assessment.mutation_run is None


def test_invalid_execution_evidence_does_not_pass(tmp_path, valid_context, valid_report, monkeypatch) -> None:
    import qa_agent.effectiveness_service as effectiveness_service
    from qa_agent.effectiveness_service import TestEffectivenessRequest, TestEffectivenessService
    from qa_agent.runtime import ExecutionBudget

    monkeypatch.setattr(effectiveness_service, "resolve_repository_revision", lambda _: "REV-1")
    invalid_records = tuple(replace(item, status="unverified") if item.id == "EV-EXEC-001" else item for item in valid_context.evidence)
    invalid_context = replace(valid_context, evidence=invalid_records)
    assessment = TestEffectivenessService().assess(TestEffectivenessRequest("REQ-1", tmp_path, invalid_context, valid_report, None, 0.8, ExecutionBudget.v04_defaults()))
    assert assessment.decision == "incomplete"
    assert assessment.termination_reason == "INSUFFICIENT_EVIDENCE"


def test_unverified_mutation_evidence_does_not_create_verified_mapping(tmp_path, valid_context, valid_report, monkeypatch) -> None:
    import qa_agent.effectiveness_service as effectiveness_service
    from qa_agent.mutation_adapters import OfflineMutationReportAdapter
    from qa_agent.mutation_backends import MutationBackendResult
    from qa_agent.effectiveness_service import TestEffectivenessRequest, TestEffectivenessService
    from qa_agent.runtime import ExecutionBudget

    monkeypatch.setattr(effectiveness_service, "resolve_repository_revision", lambda _: "REV-1")
    parsed = OfflineMutationReportAdapter().parse(valid_report, "REV-1", ExecutionBudget.v04_defaults())
    unverified = MutationBackendResult(
        parsed.backend,
        parsed.tool_version,
        parsed.process_status,
        parsed.observation_status,
        parsed.mutants,
        parsed.results,
        tuple(replace(item, status="unverified") for item in parsed.evidence),
        parsed.raw_report_hash,
        parsed.target_paths,
        parsed.selected_test_ids,
    )
    monkeypatch.setattr(effectiveness_service.OfflineMutationReportAdapter, "parse", lambda *args: unverified)

    assessment = TestEffectivenessService().assess(
        TestEffectivenessRequest("REQ-1", tmp_path, valid_context, valid_report, None, 0.8, ExecutionBudget.v04_defaults())
    )

    assert assessment.survivor_links
    assert all(link.mapping_status == "unverified" for link in assessment.survivor_links)
