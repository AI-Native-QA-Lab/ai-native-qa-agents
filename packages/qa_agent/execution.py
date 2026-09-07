"""Test-only patch validation and isolated execution backends."""

from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
import time

from .test_engineering import ExecutionResult, GeneratedPatch


class PatchSafetyError(ValueError):
    pass


def validate_patch(patch: GeneratedPatch, test_roots: tuple[str, ...] = ("tests",)) -> None:
    for file in patch.files:
        path = PurePosixPath(file.path)
        if path.is_absolute() or ".." in path.parts or not any(path.parts[:1] == (root,) for root in test_roots):
            raise PatchSafetyError(f"unsafe test patch path: {file.path}")


def _digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode()).hexdigest()


def _ignore(path: str, names: list[str]) -> set[str]:
    return {name for name in names if name in {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"}}


class PytestExecutionBackend:
    def execute(self, repository: Path, patch: GeneratedPatch, timeout_seconds: int, test_roots: tuple[str, ...] = ("tests",)) -> ExecutionResult:
        validate_patch(patch, test_roots)
        started = time.monotonic()
        with tempfile.TemporaryDirectory() as directory:
            sandbox = Path(directory) / "repository"
            shutil.copytree(repository, sandbox, ignore=_ignore)
            for file in patch.files:
                target = sandbox / file.path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(file.content, encoding="utf-8")
            command = (sys.executable, "-m", "pytest", *[file.path for file in patch.files])
            try:
                completed = subprocess.run(command, cwd=sandbox, text=True, capture_output=True, timeout=timeout_seconds, check=False)
            except subprocess.TimeoutExpired as error:
                output = (error.stdout or "") + (error.stderr or "")
                return ExecutionResult("pytest", command, None, False, "TIMEOUT", _digest(output), None, round((time.monotonic() - started) * 1000), ("EV-EXEC-001",))
        output = completed.stdout + completed.stderr
        return ExecutionResult("pytest", command, completed.returncode, completed.returncode == 0, "EVIDENCE_SUFFICIENT", _digest(completed.stdout), _digest(completed.stderr), round((time.monotonic() - started) * 1000), ("EV-EXEC-001",))
