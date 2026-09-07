"""Test-only patch validation and isolated execution backends."""

from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
import shutil
import subprocess
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
        docker = shutil.which("docker")
        if docker is None:
            return ExecutionResult("pytest", (), None, False, "INSUFFICIENT_EVIDENCE", None, None, 0, ("EV-EXEC-UNAVAILABLE",))
        with tempfile.TemporaryDirectory() as directory:
            patch_root = Path(directory) / "patch"
            for file in patch.files:
                target = patch_root / file.path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(file.content, encoding="utf-8")
            command = (docker, "run", "--rm", "--network", "none", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "64", "--memory", "256m", "--cpus", "1", "--tmpfs", "/work:rw,noexec,nosuid,size=64m,uid=10001,gid=10001", "-v", f"{repository.resolve()}:/source:ro", "-v", f"{patch_root}:/patch:ro", "ai-native-qa-pytest:3.11", "/bin/sh", "-c", "cp -R /source/. /work && cp -R /patch/. /work && cd /work && pytest " + " ".join(file.path for file in patch.files))
            try:
                completed = subprocess.run(command, text=True, capture_output=True, timeout=timeout_seconds, check=False)
            except subprocess.TimeoutExpired as error:
                output = (error.stdout or "") + (error.stderr or "")
                return ExecutionResult("pytest", command, None, False, "TIMEOUT", _digest(output), None, round((time.monotonic() - started) * 1000), ("EV-EXEC-001",))
        output = completed.stdout + completed.stderr
        return ExecutionResult("pytest", command, completed.returncode, completed.returncode == 0, "EVIDENCE_SUFFICIENT", _digest(completed.stdout), _digest(completed.stderr), round((time.monotonic() - started) * 1000), ("EV-EXEC-001",))


class PlaywrightExecutionBackend:
    """Capability detector; it never installs a runner or browser binary."""

    def __init__(self, executable: str = "playwright") -> None:
        self.executable = executable

    def execute(self, repository: Path, patch: GeneratedPatch, timeout_seconds: int, test_roots: tuple[str, ...] = ("tests",)) -> ExecutionResult:
        validate_patch(patch, test_roots)
        if shutil.which(self.executable) is None:
            return ExecutionResult("playwright", (), None, False, "INSUFFICIENT_EVIDENCE", None, None, 0, ("EV-EXEC-UNAVAILABLE",))
        return ExecutionResult("playwright", (self.executable,), None, False, "ERROR", None, None, 0, ("EV-EXEC-UNSUPPORTED",))
