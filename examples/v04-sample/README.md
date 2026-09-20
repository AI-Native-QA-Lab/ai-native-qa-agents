# v0.4 Test Effectiveness Sample

This sample is a small offline-first assessment. The repository contains a
checkout behavior and one exact pytest identity. `test-context.json` records
verified requirement, acceptance-criterion, assertion, and execution Evidence;
`mutation-report.json` is a schema-1 report whose revision is the deterministic
hash of `repository/`.

Run it from the repository root with:

```bash
PYTHONPATH=packages python3 -m qa_agent.cli assess-effectiveness \
  --requirement REQ-CHECKOUT-001 \
  --repository examples/v04-sample/repository \
  --trace-db /tmp/qa-agent-v04-sample.db \
  --test-context examples/v04-sample/test-context.json \
  --mutation-report examples/v04-sample/mutation-report.json \
  --min-score 1.0 \
  --format json
```

The source sample is read-only; the trace database is intentionally outside
the sample repository.
