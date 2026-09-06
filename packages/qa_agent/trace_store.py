"""Explicit SQLite persistence for requirement provenance and trace links."""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sqlite3

from .requirements import AcceptanceCriterion, Requirement, TraceLink
from .review import Evidence


class SQLiteTraceStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        with self._connect() as connection:
            connection.executescript("""
            CREATE TABLE IF NOT EXISTS requirements (id TEXT PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL, source_kind TEXT NOT NULL, source_ref TEXT NOT NULL, criteria_json TEXT NOT NULL, evidence_json TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS trace_links (requirement_id TEXT NOT NULL, target_kind TEXT NOT NULL, target_path TEXT NOT NULL, target_symbol TEXT NOT NULL, evidence_ids_json TEXT NOT NULL, status TEXT NOT NULL, confidence REAL NOT NULL, PRIMARY KEY(requirement_id, target_kind, target_path, target_symbol));
            """)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def save_requirement(self, requirement: Requirement, evidence: list[Evidence]) -> None:
        with self._connect() as connection:
            connection.execute("INSERT OR REPLACE INTO requirements VALUES (?, ?, ?, ?, ?, ?, ?)", (requirement.id, requirement.title, requirement.body, requirement.source_kind, requirement.source_ref, json.dumps([asdict(x) for x in requirement.acceptance_criteria]), json.dumps([asdict(x) for x in evidence])))

    def get_requirement(self, identifier: str) -> Requirement | None:
        with self._connect() as connection:
            row = connection.execute("SELECT title, body, source_kind, source_ref, criteria_json FROM requirements WHERE id = ?", (identifier,)).fetchone()
        if not row:
            return None
        return Requirement(identifier, row[0], row[1], row[2], row[3], tuple(AcceptanceCriterion(**item) for item in json.loads(row[4])))

    def get_evidence(self, identifier: str) -> list[Evidence]:
        with self._connect() as connection:
            row = connection.execute("SELECT evidence_json FROM requirements WHERE id = ?", (identifier,)).fetchone()
        return [Evidence(**item) for item in json.loads(row[0])] if row else []

    def replace_links(self, identifier: str, links: list[TraceLink]) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM trace_links WHERE requirement_id = ?", (identifier,))
            connection.executemany("INSERT INTO trace_links VALUES (?, ?, ?, ?, ?, ?, ?)", [(link.requirement_id, link.target_kind, link.target_path, link.target_symbol, json.dumps(link.evidence_ids), link.status, link.confidence) for link in links])

    def get_links(self, identifier: str) -> list[TraceLink]:
        with self._connect() as connection:
            rows = connection.execute("SELECT target_kind, target_path, target_symbol, evidence_ids_json, status, confidence FROM trace_links WHERE requirement_id = ? ORDER BY target_kind, target_path", (identifier,)).fetchall()
        return [TraceLink(identifier, row[0], row[1], row[2], tuple(json.loads(row[3])), row[4], row[5]) for row in rows]
