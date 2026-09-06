# v0.8 Security — Production Quality Agent

## Version-specific risks
Production data sensitive; PII/secret redaction; read-only queries; time/field/size limits

## Mandatory controls
Untrusted-input isolation, redaction, context/query/file limits, execution/model/tool budgets, permission checks, protected WRITE/RELEASE, no model credential ownership, auditable LoopTrace, fail-closed behavior for unsupported high-risk actions.
