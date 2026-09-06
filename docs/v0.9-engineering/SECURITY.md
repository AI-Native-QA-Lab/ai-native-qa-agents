# v0.9 Security — Quality Knowledge Graph

## Version-specific risks
Source permissions propagate; sensitive graph access control; unverified LLM inference not persisted as fact

## Mandatory controls
Untrusted-input isolation, redaction, context/query/file limits, execution/model/tool budgets, permission checks, protected WRITE/RELEASE, no model credential ownership, auditable LoopTrace, fail-closed behavior for unsupported high-risk actions.
