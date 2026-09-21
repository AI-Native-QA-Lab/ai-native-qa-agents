"""Provider-neutral mutation backend contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from .effectiveness import (
    OBSERVATION_STATUSES,
    PROCESS_STATUSES,
    Mutant,
    MutationResult,
    _relative_path,
    _unique,
)
from .review import Evidence
from .runtime import PermissionContext


CAPABILITY_STATUSES = {"available", "unavailable", "unsupported"}


@dataclass(frozen=True)
class BackendCapability:
    backend: str
    status: str
    tool_version: str | None
    languages: tuple[str, ...]
    frameworks: tuple[str, ...]
    reason: str | None
    limits: dict[str, Any]
    evidence: tuple[Evidence, ...]

    def __post_init__(self) -> None:
        if not self.backend.strip():
            raise ValueError("backend is required")
        if self.status not in CAPABILITY_STATUSES:
            raise ValueError("invalid backend capability status")
        if not isinstance(self.limits, dict):
            raise ValueError("backend capability limits must be an object")


@dataclass(frozen=True)
class MutationRequest:
    repository: Path
    repository_revision: str
    target_paths: tuple[str, ...]
    selected_test_ids: tuple[str, ...]
    selected_test_paths: tuple[str, ...]
    timeout_seconds: int
    max_mutants: int
    permission_context: PermissionContext

    def __post_init__(self) -> None:
        if not isinstance(self.repository, Path) or not self.repository.is_absolute():
            raise ValueError("repository must be an absolute Path")
        if not self.repository_revision.strip():
            raise ValueError("repository revision is required")
        if not self.target_paths or not self.selected_test_paths or not self.selected_test_ids:
            raise ValueError("mutation request paths and test identities are required")
        for path in self.target_paths:
            _relative_path(path, "target path")
        for path in self.selected_test_paths:
            _relative_path(path, "selected test path")
        _unique(self.selected_test_ids, "selected test ids", required=True)
        if self.timeout_seconds <= 0 or self.max_mutants <= 0:
            raise ValueError("mutation timeout and max_mutants must be positive")


@dataclass(frozen=True)
class MutationBackendResult:
    backend: str
    tool_version: str | None
    process_status: str
    observation_status: str
    mutants: tuple[Mutant, ...]
    results: tuple[MutationResult, ...]
    evidence: tuple[Evidence, ...]
    raw_report_hash: str | None
    target_paths: tuple[str, ...] = ()
    selected_test_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.backend.strip():
            raise ValueError("backend is required")
        if self.process_status not in PROCESS_STATUSES:
            raise ValueError("invalid backend process status")
        if self.observation_status not in OBSERVATION_STATUSES:
            raise ValueError("invalid backend observation status")
        mutant_ids = {item.mutant_id for item in self.mutants}
        result_ids = {item.mutant_id for item in self.results}
        if not result_ids <= mutant_ids:
            raise ValueError("mutation result references unknown mutant")


class MutationError(Exception):
    """Base class for typed provider failures."""


class MutationInputError(MutationError):
    pass


class MutationUnavailableError(MutationError):
    pass


class MutationUnsupportedError(MutationError):
    pass


class MutationConfigurationError(MutationError):
    pass


class MutationExecutionError(MutationError):
    pass


@runtime_checkable
class MutationBackend(Protocol):
    def detect(self, repository: Path) -> BackendCapability: ...

    def run(self, request: MutationRequest) -> MutationBackendResult: ...
