# v0.4 real-project benchmark harness

This directory defines the reproducible benchmark boundary for v0.4. A
benchmark case is a version-1 manifest, not a free-form shell command. The
harness re-hashes every raw artifact and re-observes the repository revision
before running the fixed `assess-effectiveness` runner.

## Manifest and execution

Use [manifest.schema.json](manifest.schema.json) as the structural contract.
The manifest records absolute or manifest-relative paths for the Requirement,
test context, and mutation report, plus raw SHA-256 hashes, a fixed runner
`argv` audit record, framework, repository revision, working-tree observation,
ground truth, and adjudication.

```python
from pathlib import Path
from qa_agent.benchmark import aggregate_metrics, load_manifest, run_case, validate_case

loaded = load_manifest(Path("case.json"))
if loaded.manifest is not None:
    current = validate_case(loaded.manifest)
    result = run_case(loaded.manifest) if current.decision == "pass" else None
```

Dirty trees are rejected unless `allow_dirty` is true and the manifest records
the observed snapshot hash and a reason. The runner never resets, cleans,
writes, or patches the original repository. Manifest `argv` is evidence for
review; it is not executed as a shell command. Only fixed paths and numeric
values are accepted by the runner.

## Metrics

For adjudicated cases, the harness aggregates:

- `precision = TP / (TP + FP)`
- `recall = TP / (TP + FN)`
- `false_positive_rate = FP / (FP + TN)`
- `useful_finding_rate = useful_findings / reported_findings`
- `survivor_explanation_accuracy = correctly_explained / eligible_survivors`
- `cost_per_report` and `latency_per_report` only when the result records them

Every zero or unavailable denominator is `None`, never zero or a synthetic
perfect score. Unresolved or non-applicable adjudication cases are excluded
from precision/recall-style denominators. Reference fixtures prove workflow
contracts; they are not real-project effectiveness evidence. Java/PIT and
Playwright/TypeScript cases count as validated only when their environment and
artifacts are reproducible.
