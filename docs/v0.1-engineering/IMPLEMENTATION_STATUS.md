# v0.1 Implementation Status

## Delivered baseline

The executable v0.1 implementation is available in `packages/qa_agent/`.

- Bounded deterministic runtime: `detect → inspect-diff → discover-tests → run-rules → verify-and-gate`.
- Repository detection for Python/pytest and TypeScript/Playwright.
- Python AST and Playwright source discovery.
- Evidence-backed static findings with content hashes.
- All fifteen initial deterministic rules: `TQ001` through `TQ015`.
- Critical-by-default Quality Gate, JSON and SARIF reports, plus `detect`, `review`, and `config show` CLI commands.
- `rules list` and `eval` CLI commands for rule inventory and regression metrics.
- JSON rule severity overrides and path-based rule suppression.
- Git Diff candidate-test gap reporting with explicitly `unverified` low-confidence output.
- An opt-in semantic-review provider protocol; without an explicit provider it performs no model call.
- A registry-backed deterministic rule runner, dependency-free 155-case Eval catalog and regression runner.
- YAML/JSON configuration, `rules list`, structured relevance records, loop trace and budget metadata, and provider-neutral model request/response contracts.
- A GitHub Actions workflow that emits SARIF for pull requests.

## Security and scope boundary

- Model review stays disabled without an explicitly injected provider; provider credentials are never read by the CLI.
- The reviewer excludes secret-named files, certificates, key files, binary-equivalent build directories, and files over its configured size limit.
- The workflow does not execute repository tests, generate patches, or make release decisions.

## Verification record

The repository test suite verifies the public `ReviewService` and CLI seams, adapter metadata, rule registry, configuration loading, model response validation, evidence provenance, budget exhaustion, Playwright timeout/screenshot detection, SARIF, and loop metadata.

Run locally with a Python 3.11+ environment:

```bash
python -m pip install .
pytest -q
qa-agent review . --format sarif > qa-agent.sarif
```

The local verification record is `pytest -q` (45 tests) plus the 155-case eval runner. A review command may exit `1` when a configured quality gate fails; the SARIF report remains valid.
