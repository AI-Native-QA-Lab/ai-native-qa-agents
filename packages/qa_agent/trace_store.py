"""Explicit SQLite persistence for legacy and v0.4 provenance records."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sqlite3
from typing import Sequence

from .effectiveness import (
    EffectivenessScore,
    FakeTestSignal,
    MutationResult,
    MutationRun,
    MutationTraceLink,
    Mutant,
    MutationGateResult,
    TestEffectivenessAssessment,
    TestEffectivenessContext,
)
from .requirements import AcceptanceCriterion, Requirement, TraceLink
from .review import Evidence
from .runtime import ExecutionBudget, LoopTrace, budget_to_dict, loop_trace_to_dict


SCHEMA_VERSION = 2


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class SQLiteTraceStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        with self._connect() as connection:
            self._migrate(connection)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _migrate(self, connection: sqlite3.Connection) -> None:
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version > SCHEMA_VERSION:
            raise RuntimeError(f"unsupported trace schema version: {version}")
        with connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS requirements (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    source_kind TEXT NOT NULL,
                    source_ref TEXT NOT NULL,
                    criteria_json TEXT NOT NULL,
                    evidence_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS trace_links (
                    requirement_id TEXT NOT NULL,
                    target_kind TEXT NOT NULL,
                    target_path TEXT NOT NULL,
                    target_symbol TEXT NOT NULL,
                    evidence_ids_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    PRIMARY KEY(requirement_id, target_kind, target_path, target_symbol)
                );
                CREATE TABLE IF NOT EXISTS evidence_records (
                    evidence_id TEXT PRIMARY KEY,
                    requirement_id TEXT,
                    subject TEXT,
                    type TEXT NOT NULL,
                    path TEXT NOT NULL,
                    source_ref TEXT,
                    line_start INTEGER NOT NULL,
                    line_end INTEGER NOT NULL,
                    content_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    extractor TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    loop_iteration INTEGER NOT NULL,
                    metadata_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS test_contexts (
                    context_id TEXT PRIMARY KEY,
                    requirement_id TEXT NOT NULL,
                    schema_version TEXT NOT NULL,
                    repository_revision TEXT NOT NULL,
                    artifact_hash TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    evidence_ids_json TEXT NOT NULL,
                    source_version TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS assessments (
                    assessment_id TEXT PRIMARY KEY,
                    requirement_id TEXT NOT NULL,
                    context_id TEXT,
                    run_id TEXT,
                    score_json TEXT NOT NULL,
                    gate_json TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    termination_reason TEXT NOT NULL,
                    evidence_ids_json TEXT NOT NULL,
                    loop_trace_json TEXT NOT NULL,
                    budget_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS mutation_runs (
                    run_id TEXT PRIMARY KEY,
                    assessment_id TEXT NOT NULL,
                    backend TEXT NOT NULL,
                    tool_version TEXT,
                    repository_revision TEXT NOT NULL,
                    process_status TEXT NOT NULL,
                    observation_status TEXT NOT NULL,
                    target_paths_json TEXT NOT NULL,
                    selected_test_ids_json TEXT NOT NULL,
                    selected_test_paths_json TEXT NOT NULL,
                    mutant_ids_json TEXT NOT NULL,
                    report_hash TEXT,
                    evidence_ids_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS mutants (
                    run_id TEXT NOT NULL,
                    mutant_id TEXT NOT NULL,
                    path TEXT NOT NULL,
                    line INTEGER NOT NULL,
                    operator TEXT NOT NULL,
                    original TEXT NOT NULL,
                    mutated TEXT NOT NULL,
                    normalized_status TEXT NOT NULL,
                    evidence_ids_json TEXT NOT NULL,
                    PRIMARY KEY(run_id, mutant_id),
                    FOREIGN KEY(run_id) REFERENCES mutation_runs(run_id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS mutation_results (
                    run_id TEXT NOT NULL,
                    mutant_id TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    executed_test_ids_json TEXT NOT NULL,
                    killing_test_ids_json TEXT NOT NULL,
                    duration_ms INTEGER NOT NULL,
                    stdout_hash TEXT,
                    stderr_hash TEXT,
                    evidence_ids_json TEXT NOT NULL,
                    PRIMARY KEY(run_id, mutant_id),
                    FOREIGN KEY(run_id) REFERENCES mutation_runs(run_id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS mutation_trace_links (
                    run_id TEXT NOT NULL,
                    mutant_id TEXT NOT NULL,
                    requirement_id TEXT,
                    intent_id TEXT,
                    scenario_id TEXT,
                    business_oracle TEXT,
                    mapping_status TEXT NOT NULL,
                    evidence_ids_json TEXT NOT NULL,
                    PRIMARY KEY(run_id, mutant_id),
                    FOREIGN KEY(run_id) REFERENCES mutation_runs(run_id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS observations (
                    observation_id TEXT PRIMARY KEY,
                    assessment_id TEXT NOT NULL,
                    action_id TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    structured_data_json TEXT NOT NULL,
                    evidence_ids_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(assessment_id) REFERENCES assessments(assessment_id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS loop_traces (
                    assessment_id TEXT NOT NULL,
                    iteration INTEGER NOT NULL,
                    action_id TEXT NOT NULL,
                    phase TEXT,
                    status TEXT NOT NULL,
                    observation_id TEXT,
                    permission_evidence_id TEXT,
                    evidence_ids_json TEXT NOT NULL,
                    termination_reason TEXT,
                    PRIMARY KEY(assessment_id, iteration, action_id),
                    FOREIGN KEY(assessment_id) REFERENCES assessments(assessment_id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_evidence_requirement ON evidence_records(requirement_id);
                CREATE INDEX IF NOT EXISTS idx_evidence_subject ON evidence_records(subject);
                CREATE INDEX IF NOT EXISTS idx_mutation_results_run ON mutation_results(run_id);
                """
            )
            connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    def save_requirement(self, requirement: Requirement, evidence: list[Evidence]) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO requirements VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    requirement.id,
                    requirement.title,
                    requirement.body,
                    requirement.source_kind,
                    requirement.source_ref,
                    _json([asdict(x) for x in requirement.acceptance_criteria]),
                    _json([item.to_dict() for item in evidence]),
                ),
            )

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
            connection.executemany(
                "INSERT INTO trace_links VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    (link.requirement_id, link.target_kind, link.target_path, link.target_symbol, _json(link.evidence_ids), link.status, link.confidence)
                    for link in links
                ],
            )

    def get_links(self, identifier: str) -> list[TraceLink]:
        with self._connect() as connection:
            rows = connection.execute("SELECT target_kind, target_path, target_symbol, evidence_ids_json, status, confidence FROM trace_links WHERE requirement_id = ? ORDER BY target_kind, target_path", (identifier,)).fetchall()
        return [TraceLink(identifier, row[0], row[1], row[2], tuple(json.loads(row[3])), row[4], row[5]) for row in rows]

    def save_evidence(self, records: Sequence[Evidence]) -> None:
        with self._connect() as connection:
            connection.executemany(
                "INSERT OR REPLACE INTO evidence_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        item.id,
                        None,
                        item.subject,
                        item.type,
                        item.path,
                        item.source_ref,
                        item.line_start,
                        item.line_end,
                        item.content_hash,
                        item.status,
                        item.provider,
                        item.extractor,
                        item.created_at,
                        item.loop_iteration,
                        _json(item.metadata),
                    )
                    for item in records
                ],
            )

    def get_evidence_by_ids(self, ids: Sequence[str], limit: int) -> list[Evidence]:
        if limit <= 0 or not ids:
            return []
        unique_ids = tuple(sorted(set(ids)))
        placeholders = ",".join("?" for _ in unique_ids)
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT evidence_id, subject, type, path, source_ref, line_start, line_end, content_hash, status, provider, extractor, created_at, loop_iteration, metadata_json FROM evidence_records WHERE evidence_id IN ({placeholders}) ORDER BY evidence_id LIMIT ?",
                (*unique_ids, limit),
            ).fetchall()
        return [
            Evidence(
                row[0],
                row[2],
                row[3],
                row[5],
                row[6],
                row[7],
                status=row[8],
                provider=row[9],
                extractor=row[10],
                created_at=row[11],
                loop_iteration=row[12],
                subject=row[1],
                source_ref=row[4],
                metadata=json.loads(row[13]),
            )
            for row in rows
        ]

    def context_id_for(self, context: TestEffectivenessContext) -> str:
        return "CTX-" + context.artifact_hash.split(":", 1)[1][:16]

    def save_test_context(self, context: TestEffectivenessContext) -> None:
        context_id = self.context_id_for(context)
        payload = context.to_dict()
        self.save_evidence(context.evidence)
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO test_contexts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    context_id,
                    context.requirement_id,
                    context.schema_version,
                    "",
                    context.artifact_hash,
                    _json(payload),
                    _json(context.evidence_ids),
                    context.source_version,
                ),
            )

    def get_test_context(self, context_id: str) -> TestEffectivenessContext | None:
        with self._connect() as connection:
            row = connection.execute("SELECT payload_json FROM test_contexts WHERE context_id = ?", (context_id,)).fetchone()
        if not row:
            return None
        return TestEffectivenessContext.from_dict(json.loads(row[0]), 1_000_000)

    def save_mutation(self, run: MutationRun, mutants: Sequence[Mutant], results: Sequence[MutationResult], links: Sequence[MutationTraceLink]) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO mutation_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run.run_id,
                    run.assessment_id,
                    run.backend,
                    None,
                    run.repository_revision,
                    run.process_status,
                    run.observation_status,
                    _json(run.target_paths),
                    _json(run.selected_test_ids),
                    _json(run.selected_test_paths),
                    _json(run.mutant_ids),
                    None,
                    _json(run.evidence_ids),
                ),
            )
            for table in ("mutants", "mutation_results", "mutation_trace_links"):
                connection.execute(f"DELETE FROM {table} WHERE run_id = ?", (run.run_id,))
            connection.executemany(
                "INSERT INTO mutants VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [(run.run_id, item.mutant_id, item.path, item.line, item.operator, item.original, item.mutated, item.normalized_status, _json(item.evidence_ids)) for item in mutants],
            )
            connection.executemany(
                "INSERT INTO mutation_results VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [(run.run_id, item.mutant_id, item.outcome, _json(item.executed_test_ids), _json(item.killing_test_ids), item.duration_ms, item.stdout_hash, item.stderr_hash, _json(item.evidence_ids)) for item in results],
            )
            connection.executemany(
                "INSERT INTO mutation_trace_links VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [(run.run_id, item.mutant_id, item.requirement_id, item.intent_id, item.scenario_id, item.business_oracle, item.mapping_status, _json(item.evidence_ids)) for item in links],
            )

    def save_assessment(self, assessment: TestEffectivenessAssessment) -> None:
        score_payload = {
            "score": asdict(assessment.score),
            "survivor_links": [asdict(item) for item in assessment.survivor_links],
            "signals": [asdict(item) for item in assessment.signals],
        }
        gate_payload = asdict(assessment.gate) if assessment.gate else None
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO assessments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    assessment.assessment_id,
                    assessment.requirement_id,
                    None,
                    assessment.mutation_run.run_id if assessment.mutation_run else None,
                    _json(score_payload),
                    _json(gate_payload),
                    assessment.decision,
                    assessment.termination_reason,
                    _json(assessment.evidence_ids),
                    _json([loop_trace_to_dict(item, include_v04=True) for item in assessment.loop_trace]),
                    _json(budget_to_dict(assessment.budget, include_v04=True)),
                ),
            )
            connection.execute("DELETE FROM loop_traces WHERE assessment_id = ?", (assessment.assessment_id,))
            for item in assessment.loop_trace:
                connection.execute(
                    "INSERT INTO loop_traces VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        assessment.assessment_id,
                        item.iteration,
                        item.action_id,
                        item.phase,
                        item.status,
                        item.observation_id,
                        item.permission_evidence_id,
                        _json(item.evidence_ids),
                        item.termination_reason,
                    ),
                )

    def get_assessment(self, assessment_id: str) -> TestEffectivenessAssessment | None:
        with self._connect() as connection:
            row = connection.execute("SELECT requirement_id, run_id, score_json, gate_json, decision, termination_reason, evidence_ids_json, loop_trace_json, budget_json FROM assessments WHERE assessment_id = ?", (assessment_id,)).fetchone()
        if not row:
            return None
        score_payload = json.loads(row[2])
        score = EffectivenessScore(**score_payload["score"])
        links = tuple(MutationTraceLink(**item) for item in score_payload.get("survivor_links", ()))
        signals = tuple(FakeTestSignal(**item) for item in score_payload.get("signals", ()))
        gate_payload = json.loads(row[3])
        gate = MutationGateResult(**gate_payload) if gate_payload else None
        traces = tuple(LoopTrace(**item) for item in json.loads(row[7]))
        budget = ExecutionBudget(**json.loads(row[8]))
        run = self._get_mutation_run(row[1]) if row[1] else None
        return TestEffectivenessAssessment(
            assessment_id,
            row[0],
            run,
            score,
            links,
            signals,
            row[4],
            row[5],
            gate,
            tuple(json.loads(row[6])),
            traces,
            budget,
        )

    def _get_mutation_run(self, run_id: str) -> MutationRun | None:
        with self._connect() as connection:
            row = connection.execute("SELECT run_id, assessment_id, backend, repository_revision, process_status, observation_status, target_paths_json, selected_test_paths_json, selected_test_ids_json, mutant_ids_json, evidence_ids_json FROM mutation_runs WHERE run_id = ?", (run_id,)).fetchone()
        if not row:
            return None
        return MutationRun(row[0], row[1], row[2], row[3], tuple(json.loads(row[6])), tuple(json.loads(row[7])), tuple(json.loads(row[8])), row[4], row[5], tuple(json.loads(row[9])), tuple(json.loads(row[10])))
