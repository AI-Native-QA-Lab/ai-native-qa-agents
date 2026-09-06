# v0.5 Evidence & Gates — Failure Investigator

## Expansion
test_failure, log_excerpt, hypothesis_support, hypothesis_contradiction; Investigation Evidence Gate

## Flow
```text
Action → Observation → Evidence → Verification → Finding/Decision → Gate
```

Evidence should retain source, subject, location/id, timestamp, extractor/tool version, content hash where useful, and loop provenance.

Missing critical evidence must result in `INSUFFICIENT_EVIDENCE`, not fabricated certainty.
