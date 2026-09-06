# v0.2 Requirement Intelligence Design

## Purpose and scope

v0.2 extends the v0.1 evidence-driven PR reviewer from `Code <-> Test` to
`Requirement <-> Code <-> Test`. It implements the approved v0.2 engineering
pack without changing the v0.1 review contracts.

The delivered workflow accepts a Markdown requirement or a GitHub Issue-shaped
payload, extracts deterministic requirement evidence, analyses acceptance
criteria for testability and risk, stores trace links in SQLite, and produces
evidence-backed JSON or human-readable results. It provides these CLI commands:

```bash
qa-agent analyze-requirement requirement.md
qa-agent map-coverage
qa-agent review-pr --requirement GH-123
```

GitHub Issue support uses an injected read-only fetcher. The shipped CLI has no
credential discovery and makes no network request unless a caller explicitly
provides an adapter implementation.

## Architecture

The Agent Runtime remains the control plane. It owns budgets, permission
checks, loop trace, evidence verification, gate decisions, and terminal
states. The v0.2 requirement loop is:

```text
UNDERSTAND -> PLAN -> ACT -> OBSERVE -> EVALUATE
                 ^                    |
                 +------ RE-PLAN -----+
                                      v
                                   VERIFY -> GATE -> DECIDE / STOP
```

`RequirementAnalysisService` executes the deterministic path in this order:

1. Read through a `RequirementBackend` and create source evidence.
2. Parse title, body, and acceptance criteria into a versioned `Requirement`.
3. Detect ambiguity, conflicting criteria, missing error paths, and criteria
   that lack an observable outcome.
4. Derive deterministic risk and test-scope findings.
5. Store or resolve requirement-to-code/test `TraceLink` records in SQLite.
6. Verify evidence references, evaluate the requirement gate, and emit a
   decision or an explicit insufficient-evidence terminal state.

An optional semantic task may receive bounded, redacted requirement context
only after deterministic analysis is insufficient. It consumes the existing
provider-neutral model contracts and cannot mutate runtime state, stored trace
truth, permissions, or termination.

## Domain contracts

All v0.2 models are frozen dataclasses with `schema_version = "v0.2"` and
stable identifiers.

- `Requirement`: id, title, body, source metadata, and acceptance criteria.
- `AcceptanceCriterion`: id, text, source location, and parse status.
- `TestabilityFinding`: id, category, severity, message, criterion id,
  evidence ids, verification status, and confidence.
- `RiskItem`: id, category, severity, message, related criterion ids,
  evidence ids, verification status, and confidence.
- `TraceLink`: requirement id, target kind (`code` or `test`), target path,
  target symbol, source/evidence ids, status, and confidence.
- `RequirementContext`: bounded input, observations, findings, risks, trace
  links, budget, loop trace, and termination reason.

Confidence expresses the strength of a heuristic; it never upgrades an
unverified statement into verified evidence. Every finding and decision refers
to evidence IDs. Missing required evidence results in `INSUFFICIENT_EVIDENCE`.

## Adapters and persistence

`RequirementBackend` defines `fetch(identifier) -> RequirementSource` and
returns typed `RequirementNotFound`, `RequirementAccessDenied`, or
`RequirementBackendError` failures. Adapters translate external content into
stable source objects and never plan, choose a model, terminate loops, or make
quality decisions.

`MarkdownRequirementAdapter` reads a single UTF-8 Markdown file after path,
size, binary-content, and secret-name checks. It recognizes the first heading
as title and list entries under an `Acceptance Criteria` heading as criteria.
The parser preserves source line numbers; unrecognized criteria remain source
evidence rather than fabricated structured claims.

`GitHubIssueAdapter` accepts an injected fetcher and converts a fixed issue
payload into the same source shape. Issue body, title, labels, and comments are
untrusted data; they cannot become CLI instructions, model policy, or runtime
actions.

`SQLiteTraceStore` uses a caller-selected database path and parameterized SQL.
It stores requirements, trace links, and source provenance with upsert and
query methods. It does not store model credentials or write to a repository.

## Mapping and gates

`map-coverage` reads an already persisted requirement and scans the selected
repository using v0.1's bounded file policy. It proposes `unverified` trace
links based on normalized requirement, path, and symbol tokens. It never
claims a requirement is covered solely because a similarly named file exists.

`review-pr --requirement` composes requirement analysis with v0.1
`ReviewService`: requirement evidence and v0.1 diff/test evidence stay
distinct, and the result reports links between them only when both inputs were
observed. Unknown requirement identifiers, missing repositories, exhausted
budgets, and unverifiable links lead to an incomplete decision rather than a
pass.

`RequirementGate` reports `pass`, `warn`, `fail`, or `incomplete`. A critical
testability or risk finding fails the gate; missing source/trace evidence,
unsupported high-risk actions, and exhausted required budgets produce
`incomplete` with risk `unknown`.

## CLI and output

New commands emit either a concise human report or versioned JSON. JSON
includes requirement, findings, risks, trace links, evidence, decision, gate,
budget, loop trace, and termination reason. Existing `detect`, `review`,
`rules`, `eval`, and `config` commands retain their v0.1 behavior.

The CLI defaults to a local SQLite database only when an explicit database path
is supplied. This avoids silently creating durable state during an analysis.

## Security and bounds

- Requirement inputs are untrusted and subject to size, path, and redaction
  policies before parsing or model use.
- Read actions require an explicit allowed action; writes and release actions
  are denied because v0.2 has no such CLI capability.
- Requirement parsing, mapping, model calls, file scans, and loop iterations
  each consume bounded budget fields.
- Fail closed for unsupported adapters, malformed payloads, and high-risk
  requests.
- Loop terminal values are `EVIDENCE_SUFFICIENT`, `INSUFFICIENT_EVIDENCE`,
  `BUDGET_EXHAUSTED`, `TIMEOUT`, `HUMAN_APPROVAL_REQUIRED`, and `ERROR`.

## Tests and release evidence

Contract tests cover both adapters, including parser locations and injected
GitHub failures. Unit tests cover schemas, persistence, deterministic finding
rules, evidence provenance, budgets, termination, JSON serialization, and
security controls. End-to-end tests cover Markdown analysis, persisted mapping,
and requirement-aware PR review.

The eval catalog contains positive, negative, ambiguous, conflicting,
unverifiable, malformed, and adversarial requirement fixtures. Release
validation runs the smallest relevant tests first, then the complete `pytest`
suite and the existing v0.1 eval regression suite. The release claim remains
local unless a separate request authorizes commit, push, or CI verification.

## Non-goals

v0.2 does not implement Jira, Neo4j, automatic test generation, mutation
testing, a generic multi-agent runtime, repository writes, auto-commit,
auto-merge, credential ownership, or live GitHub network integration.
