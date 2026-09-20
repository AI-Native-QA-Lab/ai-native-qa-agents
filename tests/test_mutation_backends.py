from pathlib import Path

import pytest


def test_backend_result_has_process_not_agent_termination() -> None:
    from qa_agent.mutation_backends import BackendCapability, MutationBackendResult

    capability = BackendCapability("offline", "available", None, ("Python",), ("pytest",), None, {}, ())
    result = MutationBackendResult("offline", None, "partial", "complete", (), (), (), "sha256:" + "1" * 64)
    assert capability.status == "available"
    assert result.process_status == "partial"
    assert not hasattr(result, "termination_reason")


def test_typed_backend_errors_are_distinct() -> None:
    from qa_agent.mutation_backends import MutationInputError, MutationUnavailableError

    assert not issubclass(MutationInputError, MutationUnavailableError)
    assert str(MutationInputError("bad report")) == "bad report"


def test_mutation_request_rejects_path_escape_and_invalid_mutant_limit() -> None:
    from qa_agent.mutation_backends import MutationRequest
    from qa_agent.runtime import PermissionContext

    permission = PermissionContext(Path("/repo"), Path("/tmp/copy"), ("READ",), (), 8, 1024)
    with pytest.raises(ValueError):
        MutationRequest(Path("/repo"), "REV-1", ("../src/cart.py",), ("T-1",), ("tests",), 30, 10, permission)
    with pytest.raises(ValueError):
        MutationRequest(Path("/repo"), "REV-1", ("src/cart.py",), ("T-1",), ("tests",), 30, 0, permission)
