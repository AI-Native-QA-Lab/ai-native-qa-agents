# v0.7 Evidence & Gates — Release Guardian

## Expansion
release_candidate, known_defect, performance_result, security_result, approval; Release Gate

## Flow
```text
Action → Observation → Evidence → Verification → Finding/Decision → Gate
```

Evidence should retain source, subject, location/id, timestamp, extractor/tool version, content hash where useful, and loop provenance.

Missing critical evidence must result in `INSUFFICIENT_EVIDENCE`, not fabricated certainty.
