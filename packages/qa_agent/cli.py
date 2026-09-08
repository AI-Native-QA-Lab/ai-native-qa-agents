from __future__ import annotations

import argparse
import json
from pathlib import Path

from .review import ReviewRequest, ReviewService
from .reporting import render_human, render_requirement_human
from .config import load_config
from .rules import RuleRegistry
from .evals import run_metrics, run_v02_evals, run_v03_evals, v01_cases
from .requirement_adapters import GitHubIssueAdapter, MarkdownRequirementAdapter
from .requirement_analysis import RequirementAnalysisService, RequirementRequest
from .requirement_mapping import map_requirement
from .trace_store import SQLiteTraceStore
from .requirements import RequirementResult
from .test_generation import JsonTestGenerator
from .test_engineering_service import TestEngineeringRequest, TestEngineeringService


def _render_requirement(result: RequirementResult, output_format: str) -> None:
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True) if output_format == "json" else render_requirement_human(result))


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
    eval_command.add_argument("--version", choices=("v0.1", "v0.2", "v0.3"), default="v0.1")
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
