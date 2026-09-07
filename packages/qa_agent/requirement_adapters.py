"""Bounded, offline requirement-source adapters."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Callable


class RequirementBackendError(RuntimeError):
    pass


class RequirementNotFound(RequirementBackendError):
    pass


class RequirementAccessDenied(RequirementBackendError):
    pass


@dataclass(frozen=True)
class RequirementSource:
    id: str
    title: str
    body: str
    source_kind: str
    source_ref: str
    criterion_lines: tuple[tuple[int, str], ...] = ()


def _safe_text(path: Path, max_file_bytes: int) -> str:
    if path.name == ".env" or path.name.startswith((".env.", "credentials", "secrets")):
        raise RequirementAccessDenied(str(path))
    if not path.is_file():
        raise RequirementNotFound(str(path))
    if path.stat().st_size > max_file_bytes:
        raise RequirementBackendError("requirement input exceeds size limit")
    raw = path.read_bytes()
    if b"\x00" in raw[:4096]:
        raise RequirementBackendError("binary requirement input")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RequirementBackendError("requirement input is not UTF-8") from error


def _criteria(body: str) -> tuple[tuple[int, str], ...]:
    active, values = False, []
    for line_number, line in enumerate(body.splitlines(), 1):
        if re.match(r"^##\s+acceptance criteria\s*$", line, re.I):
            active = True
        elif active and re.match(r"^#{1,6}\s+", line):
            break
        elif active:
            match = re.match(r"^\s*[-*]\s+(.+?)\s*$", line)
            if match:
                values.append((line_number, match.group(1)))
    return tuple(values)


def _source(identifier: str, title: str, body: str, source_kind: str, source_ref: str) -> RequirementSource:
    if not title.strip() or not isinstance(body, str):
        raise RequirementBackendError("requirement title and body are required")
    return RequirementSource(identifier, title.strip(), body, source_kind, source_ref, _criteria(body))


class MarkdownRequirementAdapter:
    def __init__(self, max_file_bytes: int = 1_000_000) -> None:
        self.max_file_bytes = max_file_bytes

    def fetch(self, path: Path) -> RequirementSource:
        body = _safe_text(path, self.max_file_bytes)
        title = next((line[2:].strip() for line in body.splitlines() if line.startswith("# ") and line[2:].strip()), path.stem)
        return _source(path.stem, title, body, "markdown", str(path))


class GitHubIssueAdapter:
    def __init__(self, fetcher: Callable[[str], dict[str, object]] | None = None, max_file_bytes: int = 1_000_000) -> None:
        self.fetcher, self.max_file_bytes = fetcher, max_file_bytes

    def fetch(self, identifier: str, issue_file: Path | None = None) -> RequirementSource:
        try:
            if issue_file is not None:
                payload = json.loads(_safe_text(issue_file, self.max_file_bytes))
            elif self.fetcher is not None:
                payload = self.fetcher(identifier)
            else:
                raise RequirementNotFound(identifier)
        except PermissionError as error:
            raise RequirementAccessDenied(identifier) from error
        except json.JSONDecodeError as error:
            raise RequirementBackendError("malformed issue JSON") from error
        if not isinstance(payload, dict):
            raise RequirementBackendError("issue payload must be an object")
        title, body = payload.get("title"), payload.get("body")
        if not isinstance(title, str) or not isinstance(body, str):
            raise RequirementBackendError("issue title and body are required")
        return _source(identifier, title, body, "github_issue", str(payload.get("html_url", identifier)))
