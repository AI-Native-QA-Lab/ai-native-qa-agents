# v0.5 Security — Failure Investigator

## Version-specific risks
Log redaction; context limits; failure text cannot authorize tools; READ/ANALYZE by default

## Mandatory controls
Untrusted-input isolation, redaction, context/query/file limits, execution/model/tool budgets, permission checks, protected WRITE/RELEASE, no model credential ownership, auditable LoopTrace, fail-closed behavior for unsupported high-risk actions.
