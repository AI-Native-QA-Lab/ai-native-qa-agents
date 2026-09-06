# v0.6 Security — CI / Pull Request Agent

## Version-specific risks
Fork PR secret protection; minimal token permissions; AI safe-disable; PR content untrusted

## Mandatory controls
Untrusted-input isolation, redaction, context/query/file limits, execution/model/tool budgets, permission checks, protected WRITE/RELEASE, no model credential ownership, auditable LoopTrace, fail-closed behavior for unsupported high-risk actions.
