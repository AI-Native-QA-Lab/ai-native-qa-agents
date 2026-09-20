from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path

from .effectiveness import TestEffectivenessContext
from .effectiveness_service import TestEffectivenessRequest, TestEffectivenessService
from .mutation_adapters import MutmutMutationBackend, PitMutationBackend, StrykerMutationBackend
from .runtime import ExecutionBudget
from .review import ReviewRequest, ReviewService
from .reporting import render_human, render_requirement_human
from .config import load_config
from .rules import RuleRegistry
from .evals import run_metrics, run_v02_evals, run_v03_evals, run_v04_evals, v01_cases
from .requirement_adapters import GitHubIssueAdapter, MarkdownRequirementAdapter
from .requirement_analysis import RequirementAnalysisService, RequirementRequest
from .requirement_mapping import map_requirement
from .trace_store import SQLiteTraceStore
from .requirements import RequirementResult
from .test_generation import JsonTestGenerator
from .test_engineering_service import TestEngineeringRequest, TestEngineeringService


def _render_requirement(result: RequirementResult, output_format: str) -> None:
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True) if output_format == "json" else render_requirement_human(result))


def _effectiveness_incomplete(missing_inputs: list[str], *, invalid_inputs: list[str] | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "v0.4",
        "assessment_id": None,
        "requirement_id": None,
        "decision": "incomplete",
        "termination_reason": "INSUFFICIENT_EVIDENCE",
        "missing_inputs": missing_inputs,
        "score": None,
        "score_status": "not_computable",
        "evidence_ids": [],
        "loop_trace": [],
        "budget": None,
        "gate": {"decision": "incomplete", "reasons": ["missing input"]},
    }
    if invalid_inputs:
        payload["invalid_inputs"] = invalid_inputs
        payload["gate"] = {"decision": "incomplete", "reasons": ["invalid input"]}
    return payload


def _render_effectiveness(assessment, output_format: str, artifacts: dict[str, object] | None = None) -> None:
    if output_format == "json":
        payload = assessment.to_dict()
        if artifacts is not None:
            payload["artifacts"] = artifacts
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    score = assessment.score
    print(f"Decision: {assessment.decision}")
    print(f"Termination: {assessment.termination_reason}")
    print(f"Score status: {score.score_status}")
    print(f"Score: {score.score}")
    print(f"Eligible/Killed/Survived/Timeout/Error/Not run: {score.eligible_mutants}/{score.killed_mutants}/{score.survived_mutants}/{score.timeout_mutants}/{score.error_mutants}/{score.not_run_mutants}")
    print("Survivor mapping:")
    for link in assessment.survivor_links:
        print(f"- {link.mutant_id}: {link.mapping_status} ({link.intent_id or 'unmapped'})")
    print("Signals:")
    for signal in assessment.signals:
        print(f"- {signal.signal_kind} [{signal.severity}] {signal.message}")
    print("Evidence IDs: " + ", ".join(assessment.evidence_ids))
    print(f"Gate: {assessment.gate.decision if assessment.gate else 'incomplete'}")


def _render_effectiveness_missing(payload: dict[str, object], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("Decision: incomplete")
        print("Termination: INSUFFICIENT_EVIDENCE")
        print("Missing inputs: " + ", ".join(payload.get("missing_inputs", [])))


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_effectiveness_args(args) -> tuple[list[str], list[str]]:
    missing: list[str] = []
    invalid: list[str] = []
    for name, value in (
        ("--requirement", args.requirement),
        ("--repository", args.repository),
        ("--trace-db", args.trace_db),
        ("--test-context", args.test_context),
    ):
        if value is None:
            missing.append(name)
    if args.mutation_report is None and args.backend is None:
        missing.append("--mutation-report or --backend")
    if args.min_score is None:
        missing.append("--min-score")
    if args.mutation_report is not None and args.backend is not None:
        invalid.append("--mutation-report and --backend are mutually exclusive")
    if args.min_score is not None and (not math.isfinite(args.min_score) or not 0 <= args.min_score <= 1):
        invalid.append("--min-score must be finite and between 0 and 1")
    if args.repository is not None:
        repository = args.repository.resolve()
        if not repository.is_dir():
            invalid.append("--repository must be an existing directory")
    if args.test_context is not None and not args.test_context.is_file():
        invalid.append("--test-context must be an existing file")
    if args.mutation_report is not None and not args.mutation_report.is_file():
        invalid.append("--mutation-report must be an existing file")
    if args.trace_db is not None:
        trace_db = args.trace_db.resolve()
        parent = trace_db.parent
        if args.repository is not None:
            repository = args.repository.resolve()
            try:
                trace_db.relative_to(repository)
            except ValueError:
                pass
            else:
                invalid.append("--trace-db must be outside --repository")
        if not parent.is_dir() or not os.access(parent, os.W_OK):
            invalid.append("--trace-db parent must be an existing writable directory")
    return missing, invalid


def _run_assess_effectiveness(args, parser: argparse.ArgumentParser) -> int:
    missing, invalid = _validate_effectiveness_args(args)
    if args.mutation_report is not None and args.backend is not None:
        parser.error("--mutation-report and --backend are mutually exclusive")
    if missing or invalid:
        _render_effectiveness_missing(_effectiveness_incomplete(missing, invalid_inputs=invalid), args.format)
        return 2

    budget = ExecutionBudget.v04_defaults()
    try:
        context = TestEffectivenessContext.from_dict(
            json.loads(args.test_context.read_text(encoding="utf-8")),
            budget.max_context_bytes or 1_000_000,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        _render_effectiveness_missing(_effectiveness_incomplete([], invalid_inputs=[f"--test-context: {exc}"]), args.format)
        return 2
    if context.requirement_id != args.requirement:
        _render_effectiveness_missing(_effectiveness_incomplete([], invalid_inputs=["--requirement does not match test context"]), args.format)
        return 2

    backend = None
    if args.backend == "mutmut":
        backend = MutmutMutationBackend()
    elif args.backend == "pit":
        backend = PitMutationBackend()
    elif args.backend == "stryker":
        backend = StrykerMutationBackend()
    try:
        store = SQLiteTraceStore(args.trace_db)
        assessment = TestEffectivenessService(store).assess(
            TestEffectivenessRequest(
                args.requirement,
                args.repository.resolve(),
                context,
                args.mutation_report.resolve() if args.mutation_report is not None else None,
                backend,
                args.min_score,
                budget,
            )
        )
        repository_revision = None
        try:
            from .effectiveness_service import resolve_repository_revision

            repository_revision = resolve_repository_revision(args.repository)
        except (OSError, ValueError):
            pass
        artifacts = {
            "context": {"path": str(args.test_context), "sha256": _sha256_file(args.test_context)},
            "report": {"path": str(args.mutation_report), "sha256": _sha256_file(args.mutation_report)} if args.mutation_report else None,
            "repository": {"path": str(args.repository), "revision": repository_revision},
        }
        _render_effectiveness(assessment, args.format, artifacts)
        return {"pass": 0, "warn": 0, "fail": 1, "incomplete": 2}.get(assessment.decision, 3)
    except (OSError, ValueError, RuntimeError) as exc:
        _render_effectiveness_missing(_effectiveness_incomplete([], invalid_inputs=[str(exc)]), args.format)
        return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qa-agent", description="Evidence-driven QA review")
    commands = parser.add_subparsers(dest="command", required=True)
    detect = commands.add_parser("detect", help="Detect project languages and test frameworks")
    detect.add_argument("repository", type=Path, nargs="?", default=Path("."))
    review = commands.add_parser("review", help="Review tests with deterministic rules")
    review.add_argument("repository", type=Path, nargs="?", default=Path("."))
    review.add_argument("--base")
    review.add_argument("--format", choices=("human", "json", "sarif"), default="human")
    review.add_argument("--fail-on", action="append", choices=("critical", "high", "medium", "low"))
    review.add_argument("--config", type=Path, help="JSON configuration with rule severity or ignore paths")
    rules = commands.add_parser("rules", help="Inspect deterministic rules")
    rules_subcommands = rules.add_subparsers(dest="rules_command", required=True)
    rules_subcommands.add_parser("list", help="List enabled v0.1 rules")
    eval_command = commands.add_parser("eval", help="Run deterministic eval metrics")
    eval_command.add_argument("--version", choices=("v0.1", "v0.2", "v0.3", "v0.4"), default="v0.1")
    effectiveness = commands.add_parser("assess-effectiveness", help="Assess test effectiveness with mutation evidence")
    effectiveness.add_argument("--requirement", type=str)
    effectiveness.add_argument("--repository", type=Path)
    effectiveness.add_argument("--trace-db", type=Path)
    effectiveness.add_argument("--test-context", type=Path)
    effectiveness.add_argument("--mutation-report", type=Path)
    effectiveness.add_argument("--backend", choices=("mutmut", "pit", "stryker"))
    effectiveness.add_argument("--min-score", type=float)
    effectiveness.add_argument("--format", choices=("human", "json"), default="human")
    config = commands.add_parser("config", help="Show v0.1 runtime defaults")
    config_subcommands = config.add_subparsers(dest="config_command", required=True)
    config_subcommands.add_parser("show", help="Print the effective default configuration")
    analyze = commands.add_parser("analyze-requirement", help="Analyze a Markdown requirement")
    analyze.add_argument("requirement", type=Path)
    analyze.add_argument("--trace-db", type=Path, required=True)
    analyze.add_argument("--format", choices=("human", "json"), default="human")
    mapping = commands.add_parser("map-coverage", help="Map a persisted requirement to repository files")
    mapping.add_argument("--requirement", required=True)
    mapping.add_argument("--repository", type=Path, required=True)
    mapping.add_argument("--trace-db", type=Path, required=True)
    mapping.add_argument("--format", choices=("human", "json"), default="human")
    review_pr = commands.add_parser("review-pr", help="Review a repository against a requirement")
    review_pr.add_argument("repository", type=Path)
    review_pr.add_argument("--requirement", required=True)
    review_pr.add_argument("--trace-db", type=Path, required=True)
    review_pr.add_argument("--github-issue-file", type=Path)
    review_pr.add_argument("--base")
    review_pr.add_argument("--format", choices=("human", "json"), default="human")
    engineer = commands.add_parser("engineer-test", help="Generate and validate a test candidate")
    engineer.add_argument("--requirement", required=True)
    engineer.add_argument("--repository", type=Path, required=True)
    engineer.add_argument("--trace-db", type=Path, required=True)
    engineer.add_argument("--generator-file", type=Path, required=True)
    engineer.add_argument("--framework", choices=("pytest", "playwright"), default="pytest")
    engineer.add_argument("--execution-backend", choices=("local", "docker"), default="local")
    engineer.add_argument("--format", choices=("human", "json"), default="human")
    args = parser.parse_args(argv)
    service = ReviewService()
    if args.command == "assess-effectiveness":
        return _run_assess_effectiveness(args, parser)
    if args.command == "analyze-requirement":
        source = MarkdownRequirementAdapter().fetch(args.requirement)
        result = RequirementAnalysisService().analyze(RequirementRequest(source))
        SQLiteTraceStore(args.trace_db).save_requirement(result.requirement, result.evidence)
        _render_requirement(result, args.format)
        return {"pass": 0, "warn": 0, "fail": 1}.get(result.decision, 2)
    if args.command == "map-coverage":
        store = SQLiteTraceStore(args.trace_db)
        requirement = store.get_requirement(args.requirement)
        if requirement is None:
            print(json.dumps({"decision": "incomplete", "termination_reason": "INSUFFICIENT_EVIDENCE"}))
            return 2
        evidence = store.get_evidence(args.requirement)
        links = map_requirement(requirement, tuple(item.id for item in evidence), args.repository, 500, 1_000_000)
        store.replace_links(args.requirement, links)
        result = RequirementResult(requirement=requirement, trace_links=links, evidence=evidence, decision="warn" if links else "incomplete", termination_reason="EVIDENCE_SUFFICIENT" if links else "INSUFFICIENT_EVIDENCE")
        _render_requirement(result, args.format)
        return 0 if links else 2
    if args.command == "review-pr":
        store = SQLiteTraceStore(args.trace_db)
        if args.github_issue_file:
            source = GitHubIssueAdapter().fetch(args.requirement, args.github_issue_file)
            analyzed = RequirementAnalysisService().analyze(RequirementRequest(source))
            store.save_requirement(analyzed.requirement, analyzed.evidence)
            requirement, evidence = analyzed.requirement, analyzed.evidence
        else:
            requirement, evidence = store.get_requirement(args.requirement), store.get_evidence(args.requirement)
        result = RequirementAnalysisService().review_pr(requirement, evidence, args.repository, args.base) if requirement else None
        if result is None:
            print(json.dumps({"decision": "incomplete", "termination_reason": "INSUFFICIENT_EVIDENCE"}))
            return 2
        _render_requirement(result, args.format)
        return {"pass": 0, "warn": 0, "fail": 1}.get(result.decision, 2)
    if args.command == "engineer-test":
        from .execution import DockerPytestExecutionBackend, PlaywrightExecutionBackend, PytestExecutionBackend

        store = SQLiteTraceStore(args.trace_db)
        requirement = store.get_requirement(args.requirement)
        evidence = store.get_evidence(args.requirement)
        if requirement is None:
            print(json.dumps({"decision": "incomplete", "termination_reason": "INSUFFICIENT_EVIDENCE"}))
            return 2
        if args.framework == "playwright":
            backend = PlaywrightExecutionBackend()
        elif args.execution_backend == "docker":
            backend = DockerPytestExecutionBackend()
        else:
            backend = PytestExecutionBackend()
        result = TestEngineeringService(JsonTestGenerator(args.generator_file), backend).run(
            TestEngineeringRequest(
                requirement.id,
                args.repository,
                tuple(item.id for item in evidence),
                framework=args.framework,
            )
        )
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True) if args.format == "json" else f"Decision: {result.status.decision}\nTermination: {result.status.termination_reason}")
        return 0 if result.status.decision == "accepted" else 2 if result.status.decision == "incomplete" else 1
    if args.command == "detect":
        languages, frameworks = service.detect(args.repository)
        print("Languages:\n" + "\n".join(f"- {item}" for item in languages))
        print("Frameworks:\n" + "\n".join(f"- {item}" for item in frameworks))
        return 0
    if args.command == "config":
        print(json.dumps({"max_actions": 6, "max_files": 500, "max_file_bytes": 1_000_000, "fail_on": ["critical"], "semantic_review": "disabled"}, indent=2, sort_keys=True))
        return 0
    if args.command == "rules":
        print("\n".join(RuleRegistry.default().ids()))
        return 0
    if args.command == "eval":
        if args.version == "v0.2":
            total, failures = run_v02_evals()
            print(json.dumps({"cases": total, "failures": failures}, indent=2, sort_keys=True))
            return 1 if failures else 0
        if args.version == "v0.3":
            total, failures = run_v03_evals()
            print(json.dumps({"cases": total, "failures": failures}, indent=2, sort_keys=True))
            return 1 if failures else 0
        if args.version == "v0.4":
            total, failures = run_v04_evals()
            print(json.dumps({"cases": total, "failures": failures}, indent=2, sort_keys=True))
            return 1 if failures else 0
        metrics = run_metrics(v01_cases())
        print(json.dumps({"cases": metrics.cases, "precision": metrics.precision, "recall": metrics.recall}, indent=2, sort_keys=True))
        return 0
    project_config = args.config
    if project_config is None:
        project_config = next((args.repository / name for name in (".qa-agent.yaml", ".qa-agent.yml", ".qa-agent.json") if (args.repository / name).exists()), None)
    config = load_config(project_config)
    config_data = json.loads(args.config.read_text()) if args.config and args.config.suffix == ".json" else {}
    rule_severity = config.rule_severity
    if config_data:
        rule_severity = {rule: values["severity"] for rule, values in config_data.get("rules", {}).items() if "severity" in values}
    invalid = set(rule_severity.values()) - {"critical", "high", "medium", "low"}
    if invalid:
        parser.error("invalid rule severity: " + ", ".join(sorted(invalid)))
    result = service.review(ReviewRequest(args.repository, base=args.base, fail_on=tuple(args.fail_on or config.fail_on), max_actions=config.max_actions, max_files=config.max_files, max_file_bytes=config.max_file_bytes, max_tool_calls=config.max_tool_calls, max_model_calls=config.max_model_calls, timeout_seconds=config.timeout_seconds, rule_severity=rule_severity, suppressed_rules=config.suppressed_rules))
    if args.format == "json":
        print(result.to_json())
    elif args.format == "sarif":
        print(json.dumps(result.to_sarif(), indent=2))
    else:
        print(render_human(result))
        print(f"Termination: {result.termination_reason}")
        for finding in result.findings:
            print(f"{finding.severity.upper()} {finding.rule_id} {finding.path}:{finding.line} {finding.message}")
    return 1 if result.decision == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
