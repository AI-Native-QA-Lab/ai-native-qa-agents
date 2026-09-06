# v0.4 Evidence & Gates — Test Effectiveness & Mutation

## Expansion
mutation_run, mutant_survived, mutant_killed, effectiveness_score; Mutation Gate

## Flow
```text
Action → Observation → Evidence → Verification → Finding/Decision → Gate
```

Evidence should retain source, subject, location/id, timestamp, extractor/tool version, content hash where useful, and loop provenance.

Missing critical evidence must result in `INSUFFICIENT_EVIDENCE`, not fabricated certainty.
