# v0.4 Security — Test Effectiveness & Mutation

## Version-specific risks
Mutation execution isolation; CPU/time budget; working-tree protection; command allowlist

## Mandatory controls
Untrusted-input isolation, redaction, context/query/file limits, execution/model/tool budgets, permission checks, protected WRITE/RELEASE, no model credential ownership, auditable LoopTrace, fail-closed behavior for unsupported high-risk actions.

## Frozen security contracts

Requirement text, test source, report fields, stdout/stderr, and model output are
untrusted data. They never become shell, policy, or prompt instructions. Commands
use fixed argv arrays with `shell=False`; report/model fields cannot add commands.

The analyzed repository and user worktree are read-only. Mutation execution uses a
controlled temporary copy with explicit path, file-count, report/context-byte,
mutant, CPU/time, tool, model, and iteration limits. WRITE, COMMIT, MERGE, and
RELEASE are denied regardless of approval context. Unsupported or high-risk
actions fail closed and produce a permission Evidence record without a command
observation.

The offline report parser computes raw bytes SHA-256 before parsing and rejects
malformed JSON, duplicate IDs, unknown outcomes, path escape, oversized strings or
arrays, and shell-like prompt data without executing it. Redacted excerpts are
bounded to 4096 UTF-8 bytes; raw unbounded output and credentials are not stored.

Benchmark manifests are audit inputs, not arbitrary invocations. The harness uses
only a fixed `assess-effectiveness` runner and validates artifact/revision hashes
before execution; it never cleans, resets, overwrites, or publishes the original
repository.
