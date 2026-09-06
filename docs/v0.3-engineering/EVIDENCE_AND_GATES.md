# v0.3 Evidence & Gates — AI Test Engineer

## Expansion
generated_patch, compile_result, test_execution, repair_attempt; Parse/Compile/Execution/Assertion/Reviewer Gates

## Flow
```text
Action → Observation → Evidence → Verification → Finding/Decision → Gate
```

Evidence should retain source, subject, location/id, timestamp, extractor/tool version, content hash where useful, and loop provenance.

Missing critical evidence must result in `INSUFFICIENT_EVIDENCE`, not fabricated certainty.
