# v0.3 Security — AI Test Engineer

## Version-specific risks
Patch-only generation; no auto-commit; isolated execution; timeout/network/resource policy

## Mandatory controls
Untrusted-input isolation, redaction, context/query/file limits, execution/model/tool budgets, permission checks, protected WRITE/RELEASE, no model credential ownership, auditable LoopTrace, fail-closed behavior for unsupported high-risk actions.
