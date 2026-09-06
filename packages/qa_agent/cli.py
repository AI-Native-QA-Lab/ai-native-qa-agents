from __future__ import annotations

import argparse
import json
from pathlib import Path

from .review import ReviewRequest, ReviewService
from .reporting import render_human
from .config import load_config
from .rules import RuleRegistry
from .evals import run_metrics, v01_cases


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
    commands.add_parser("eval", help="Run v0.1 deterministic eval metrics")
    config = commands.add_parser("config", help="Show v0.1 runtime defaults")
    config_subcommands = config.add_subparsers(dest="config_command", required=True)
    config_subcommands.add_parser("show", help="Print the effective default configuration")
    args = parser.parse_args(argv)
    service = ReviewService()
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
