import pytest


def test_v04_budget_has_fixed_defaults() -> None:
    from qa_agent.runtime import ExecutionBudget

    budget = ExecutionBudget.v04_defaults()
    assert budget.max_iterations == 8
    assert budget.max_tool_calls == 8
    assert budget.max_model_calls == 1
    assert budget.timeout_seconds == 120
    assert budget.max_replans == 1
    assert budget.max_mutants == 500
    assert budget.max_report_bytes == 2_000_000
    assert budget.max_context_bytes == 1_000_000


def test_termination_policy_checks_permission_timeout_budget_in_order() -> None:
    from qa_agent.runtime import ExecutionBudget, PermissionResult, TerminationPolicy

    budget = ExecutionBudget.v04_defaults()
    permission = PermissionResult("WRITE", False, "policy denied", "EV-PERM-1", False)
    reason = TerminationPolicy().evaluate(
        budget=budget,
        iteration=1,
        tool_calls=0,
        model_calls=0,
        replans=0,
        elapsed_seconds=0,
        permission=permission,
        process_observation_complete=False,
        evidence_sufficient=False,
    )
    assert reason == "INSUFFICIENT_EVIDENCE"


def test_v04_budget_rejects_non_positive_timeout_and_byte_limits() -> None:
    from qa_agent.runtime import ExecutionBudget

    budget = ExecutionBudget.v04_defaults()
    invalid = budget.__class__(
        budget.max_iterations,
        budget.max_tool_calls,
        budget.max_model_calls,
        budget.timeout_seconds,
        budget.max_replans,
        budget.max_mutants,
        0,
        budget.max_context_bytes,
    )
    with pytest.raises(ValueError):
        invalid.validate(v04=True)


def test_legacy_budget_and_loop_trace_serialization_omit_v04_fields() -> None:
    from qa_agent.runtime import ExecutionBudget, LoopTrace, budget_to_dict, loop_trace_to_dict

    assert set(budget_to_dict(ExecutionBudget())) == {
        "max_iterations",
        "max_tool_calls",
        "max_model_calls",
        "timeout_seconds",
    }
    trace = LoopTrace(1, "detect", "completed", "OBS-1")
    assert set(loop_trace_to_dict(trace)) == {"iteration", "action_id", "status", "observation_id"}
    trace.assessment_id = "ASSESS-1"
    assert loop_trace_to_dict(trace, include_v04=True)["assessment_id"] == "ASSESS-1"
