# v0.4 Evaluation — Test Effectiveness & Mutation

## Focus
mutation parser accuracy, survivor mapping, fake-test precision/recall, score stability

## Layers
1. Parser/rule/adapter
2. Skill/task
3. Agent loop
4. End-to-end workflow

## Metrics
Precision, recall, FPR, evidence alignment, decision accuracy, tool selection accuracy, unnecessary tool calls, re-plan accuracy, termination accuracy, iterations, model calls, cost and latency.

Do not rely only on LLM-as-judge.

## Frozen v0.4 eval and benchmark boundary

`qa-agent eval --version v0.4` covers report schema 1 parsing, exact survivor
mapping, score/Gate branches, signals, budgets, termination, and adversarial
inputs such as duplicate IDs, path escape, prompt-in-data, oversized reports,
revision conflict, permission denial, budget exhaustion, and unavailable tools.
Fixtures and golden cases prove workflow contracts only; they are not real-project
effectiveness evidence.

The real-project harness consumes benchmark manifest version 1. A case records
repository path/revision, framework, raw Requirement/context/report artifacts and
SHA-256 hashes, fixed runner argv as an audit record, clean/dirty-tree status,
ground-truth labels, adjudication, execution limits, and result evidence. Dirty
trees require explicit `allow_dirty`, snapshot hash, and reason; unresolved
adjudication is excluded from precision/recall denominators.

Metrics are versioned per case: precision, recall, false-positive rate, useful
finding rate, survivor explanation accuracy, cost per report, and latency per
report. A zero or unmeasured denominator is `None`, not zero or 1. Java/PIT and
Playwright/TypeScript count only when environment and artifacts are reproducible.
