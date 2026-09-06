# v0.2 Security — Requirement Intelligence

## Version-specific risks
Requirement text is untrusted; issue content cannot become runtime instructions; context minimization

## Mandatory controls
Untrusted-input isolation, redaction, context/query/file limits, execution/model/tool budgets, permission checks, protected WRITE/RELEASE, no model credential ownership, auditable LoopTrace, fail-closed behavior for unsupported high-risk actions.
