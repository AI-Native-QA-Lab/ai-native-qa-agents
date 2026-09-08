# Changelog

## 0.3.1 - 2026-09-08

### Fixes

- Restore the approved default local temp-directory pytest sandbox; Docker isolation is optional via `--execution-backend docker`.
- Resolve the pytest runner against the current interpreter first, then fall back to `PATH`, so CLI evals work across Homebrew Python layouts.
- Complete the v0.3 loop with explicit failure analysis, repair attempts, and a deterministic Reviewer gate after execution.
- Align root README entries and the v0.3 engineering pack with the implemented local-first execution contract.

### Tests

- Cover local sandbox isolation, optional Docker unavailability, and `analyze_failure` repair traces.

## 0.3.0 - 2026-09-08

### Features

- Add bounded test-engineering contracts, test generation, repair attempts, structured quality gates, and CLI output.
- Add an isolated Docker-based pytest execution backend with a read-only source mount, no network, dropped capabilities, and resource limits.
- Complete the v0.2 requirement-analysis closeout with trace context, deterministic conflict handling, and bounded evidence collection.

### Tests

- Expand v0.2 and v0.3 evaluation coverage for accepted, rejected, and unsafe patch flows.

### Documentation

- Add Chinese v0.2 and v0.3 engineering entry guides and the approved v0.2-closeout/v0.3 execution plan.

## 0.2.0 - 2026-09-07

### Features

- Add the Requirement Intelligence baseline.
