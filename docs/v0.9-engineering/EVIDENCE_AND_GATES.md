# v0.9 Evidence & Gates — Quality Knowledge Graph

## Expansion
all persisted important edges retain provenance; Knowledge Verification Gate

## Flow
```text
Action → Observation → Evidence → Verification → Finding/Decision → Gate
```

Evidence should retain source, subject, location/id, timestamp, extractor/tool version, content hash where useful, and loop provenance.

Missing critical evidence must result in `INSUFFICIENT_EVIDENCE`, not fabricated certainty.
