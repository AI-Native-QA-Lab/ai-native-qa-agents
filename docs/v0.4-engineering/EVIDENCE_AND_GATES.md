# v0.4 Evidence & Gates — Test Effectiveness & Mutation

## Expansion
mutation_run, mutant_survived, mutant_killed, effectiveness_score; Mutation Gate

## Flow
```text
Action → Observation → Evidence → Verification → Finding/Decision → Gate
```

Evidence should retain source, subject, location/id, timestamp, extractor/tool version, content hash where useful, and loop provenance.

Missing critical evidence must result in `INSUFFICIENT_EVIDENCE`, not fabricated certainty.

## Evidence envelope

v0.4 extends the existing Evidence record with optional `subject`, `source_ref`,
`redacted_excerpt`, and `metadata`. New records must fill all four extensions.
`subject` is a stable Requirement/Intent/Scenario/Test/Mutant/Assessment id;
`source_ref` is a reproducible artifact or repository-relative location;
`redacted_excerpt` is null or at most 4096 UTF-8 bytes. Metadata includes the
bounded redaction policy and context/report limits. Content hashes are prefixed
SHA-256 values, line ranges are positive, and status is only `verified` or
`unverified`.

The supported v0.4 types include `requirement`, `acceptance_criteria`,
`test_assertion`, `test_execution`, `test_context`, `mutation_report`,
`mutation_run`, `mutant_killed`, `mutant_survived`, `mutation_unexecuted`,
`effectiveness_score`, `fake_test_signal`, and `backend_capability`. Permission
Evidence additionally records action, allowed, reason, and
`external_command_executed`; a denied action has no command observation.

## Score and Gate precedence

Only killed and survived results enter the score denominator:
`score = killed / (killed + survived)`. Timeout, error, and not_run remain
separate counts. A zero denominator is `score_status=not_computable` with
`score=null`; otherwise Decimal half-up serialization uses four decimal places.

The Gate evaluates mutually exclusive predicates in this order:

1. `incomplete`: missing/invalid context, report, revision, Oracle, threshold,
   Evidence, eligible mutants, assessable observation, or
   `EVIDENCE_SUFFICIENT` termination.
2. `fail`: complete inputs with a score below threshold or verified high/critical
   quality signal.
3. `pass`: completed clean run, threshold met, no non-eligible outcome, no
   high/critical signal, verified survivor links, and verified execution/assertion
   Evidence.
4. `warn`: assessable input with a partial process or lower-severity limitation.

Thus `killed=1, not_run=99` with complete observation can only warn (or fail when
the threshold is not met), never pass. A truncated or unknown observation is
incomplete.
