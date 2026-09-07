"""Conservative requirement-to-file trace proposals."""
from __future__ import annotations

from pathlib import Path
import re

from .requirements import Requirement, TraceLink

_IGNORED = {".git", ".venv", "node_modules", "dist", "build", "__pycache__", "evals"}


def _is_test(path: Path) -> bool:
    return path.name.startswith("test_") or path.name.endswith(("_test.py", ".spec.ts", ".test.ts", ".spec.js", ".test.js"))


def map_requirement(requirement: Requirement, evidence_ids: tuple[str, ...], repository: Path, max_files: int, max_file_bytes: int) -> list[TraceLink]:
    if not repository.is_dir() or not evidence_ids:
        return []
    tokens = set(re.findall(r"[a-z][a-z0-9_]{2,}", (requirement.title + " " + requirement.body).lower()))
    links: list[TraceLink] = []
    for path in sorted(repository.rglob("*")):
        if len(links) >= max_files or not path.is_file() or any(part in _IGNORED for part in path.parts):
            continue
        if path.name == ".env" or path.name.startswith((".env.", "credentials", "secrets")) or path.stat().st_size > max_file_bytes:
            continue
        try:
            if b"\x00" in path.read_bytes()[:4096]:
                continue
        except OSError:
            continue
        stem_tokens = set(re.findall(r"[a-z][a-z0-9]{2,}", path.stem.lower().replace("_", " ")))
        if tokens & stem_tokens:
            links.append(TraceLink(requirement.id, "test" if _is_test(path) else "code", str(path.relative_to(repository)), path.stem, evidence_ids, "unverified", 0.2))
    return links
