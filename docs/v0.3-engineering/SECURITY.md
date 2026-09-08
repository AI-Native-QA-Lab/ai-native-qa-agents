# v0.3 Security — AI Test Engineer

## Version-specific risks
Patch-only generation; no auto-commit; isolated execution; timeout/network/resource policy

## Execution isolation
- Default: local temporary worktree copy; original repository is never written by generated patches.
- Optional: Docker backend (`--execution-backend docker`) with no network, read-only source mount, dropped capabilities, and resource limits.
- Containers are not an implicit prerequisite for the default local path.

## Mandatory controls
Untrusted-input isolation, redaction, context/query/file limits, execution/model/tool budgets, permission checks, protected WRITE/RELEASE, no model credential ownership, auditable LoopTrace, fail-closed behavior for unsupported high-risk actions.
