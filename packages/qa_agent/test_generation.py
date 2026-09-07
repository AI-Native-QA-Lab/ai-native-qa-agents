"""Offline fixture-backed generator used by the v0.3 CLI and tests."""

from __future__ import annotations

import json
from pathlib import Path

from .test_engineering import GeneratedPatch, PatchFile, TestPlan


class JsonTestGenerator:
    def __init__(self, fixture: Path, max_bytes: int = 1_000_000) -> None:
        if not fixture.is_file() or fixture.stat().st_size > max_bytes:
            raise ValueError("invalid generator fixture")
        try:
            payload = json.loads(fixture.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("malformed generator fixture") from error
        if not isinstance(payload, dict) or not isinstance(payload.get("files"), list):
            raise ValueError("generator fixture requires files")
        self.payload = payload

    def generate(self, plan: TestPlan, previous: GeneratedPatch | None = None) -> GeneratedPatch:
        try:
            files = tuple(PatchFile(item["path"], item["content"]) for item in self.payload["files"] if isinstance(item, dict))
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("invalid generator patch file") from error
        return GeneratedPatch("GP-" + plan.id, files, ("EV-GEN-001",))
