# v0.4 Real-Project Validation

## Purpose and evidence boundary

The checked-in `examples/v04-sample/` is a reference fixture. It proves that
the v0.4 context, report, service, persistence, CLI, and output contracts can
run together. It does not prove mutation effectiveness on a production
repository, model quality, business acceptance, CI success, release
readiness, or deployment.

Real-project validation uses the version-1 manifest contract in
`benchmarks/v04/manifest.schema.json` and the fixed runner in
`qa_agent.benchmark`. Each case records the repository path and revision,
framework, raw Requirement/test-context/mutation artifacts and SHA-256 hashes,
the auditable runner `argv`, working-tree status, ground-truth labels, and
adjudication. The harness recomputes hashes and revision before execution and
does not consume stale results after a mismatch.

## Repository and artifact policy

The original repository is read-only. A clean tree is the default. A dirty
tree is rejected unless the manifest explicitly sets `allow_dirty: true` and
records both a snapshot hash and a human-readable reason; the harness compares
the snapshot before and after and never resets, cleans, overwrites, or commits
the repository. Paths must resolve to the manifest's declared artifacts, and
raw bytes—not parsed JSON—are hashed.

Manifest `argv` is an audit record. The benchmark constructs only the fixed
`assess-effectiveness` runner and takes bounded paths/numeric policy values
from the validated manifest. It never executes arbitrary shell text from a
Requirement, test, mutation report, model output, or `argv` field.

## Ground truth and metrics

Survivor and signal labels include an object identity, expected outcome or
classification, Evidence reference, and reviewer decision. Adjudication is
`resolved`, `unresolved`, or `not_applicable`; unresolved cases are retained
for traceability but excluded from precision/recall-style denominators. The
versioned aggregate metrics are:

```text
precision = TP / (TP + FP)
recall = TP / (TP + FN)
false_positive_rate = FP / (FP + TN)
useful_finding_rate = useful_findings / reported_findings
survivor_explanation_accuracy = correctly_explained / eligible_survivors
```

Cost per report and latency per report are computed only when the result has
actual usage/elapsed evidence. Any zero or unmeasured denominator is `None`,
not zero or an invented 100% score.

## Release-readiness limits

Python/pytest, Playwright/TypeScript, AI-generated tests, and Java/PIT are
separate evidence classes. Java/PIT and Playwright/TypeScript count as
validated only when the required environment, framework execution, raw
artifacts, repository revision, and adjudication are reproducible. Static
tests, local evals, and a passing reference fixture do not establish real
project behavior, semantic/model replay, CI/merge, package/release,
deployment, or indexing evidence. Those states remain explicitly
`NOT_RUN`, `UNASSESSED`, `BLOCKED`, or `INSUFFICIENT_EVIDENCE` until their own
evidence is collected.
