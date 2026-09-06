# v1.0 Evidence & Gates — AI Native QA System

## Expansion
unified Evidence Spec, decision provenance, cross-agent traces; all important decisions auditable

## Flow
```text
Action → Observation → Evidence → Verification → Finding/Decision → Gate
```

Evidence should retain source, subject, location/id, timestamp, extractor/tool version, content hash where useful, and loop provenance.

Missing critical evidence must result in `INSUFFICIENT_EVIDENCE`, not fabricated certainty.
