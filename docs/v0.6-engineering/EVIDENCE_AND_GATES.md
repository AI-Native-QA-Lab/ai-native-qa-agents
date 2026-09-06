# v0.6 Evidence & Gates — CI / Pull Request Agent

## Expansion
ci_run, baseline_delta, suppression; PR Gate

## Flow
```text
Action → Observation → Evidence → Verification → Finding/Decision → Gate
```

Evidence should retain source, subject, location/id, timestamp, extractor/tool version, content hash where useful, and loop provenance.

Missing critical evidence must result in `INSUFFICIENT_EVIDENCE`, not fabricated certainty.
