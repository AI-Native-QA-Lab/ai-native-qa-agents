# v0.2 Evidence & Gates — Requirement Intelligence

## Expansion
requirement, acceptance_criteria, trace_link, risk_analysis; Requirement Gate

## Flow
```text
Action → Observation → Evidence → Verification → Finding/Decision → Gate
```

Evidence should retain source, subject, location/id, timestamp, extractor/tool version, content hash where useful, and loop provenance.

Missing critical evidence must result in `INSUFFICIENT_EVIDENCE`, not fabricated certainty.
