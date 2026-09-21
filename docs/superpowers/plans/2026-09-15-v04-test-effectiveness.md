# v0.4 Test Effectiveness & Mutation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在保持 v0.3 wire contract 与原始工作树只读的前提下，交付 Python/offline-first 的 Test Effectiveness 闭环：语义 context、Mutation evidence、survivor mapping、multi-signal score/gate、bounded Agent Runtime、SQLite provenance、CLI/eval 和可复现 benchmark harness。

**Architecture:** Agent Runtime 持有 phase 顺序、权限、预算、Observation、Evidence verification、re-plan 和 termination；MutationBackend 只检测/执行/归一化 process observation；Model Runtime 只在显式开启时执行一次 schema-validated survivor mapping。首个 vertical slice 使用 version-1 offline report，所有结论由 Requirement/Intent/Scenario/Oracle/Evidence 与明确的 process completeness 共同决定。

**Tech Stack:** Python 3.11+、标准库 dataclasses/json/pathlib/hashlib/subprocess/tempfile/sqlite3/decimal、argparse、pytest、现有 provider-neutral model contracts；不新增运行时依赖，不自动下载工具或模型。

**Spec:** docs/superpowers/specs/2026-09-15-v04-test-effectiveness-design.md

## Global Constraints

- v0.3 callers keep the existing positional constructors, v0.3 output schema, legacy default behavior, and generated-candidate semantics when semantic fields are absent.
- v0.4 uses ExecutionBudget.v04_defaults(): max_iterations 8, max_tool_calls 8, max_model_calls 1, timeout_seconds 120, max_replans 1, max_mutants 500, max_report_bytes 2,000,000, max_context_bytes 1,000,000.
- score is killed / (killed + survived); timeout, error, and not_run are retained outside the denominator; decimal half-up serialization uses four decimal places; denominator zero is None.
- Gate precedence is incomplete, fail, pass, warn; pass requires a completed run, no non-eligible outcomes, verified survivor links, verified execution/assertion Evidence, and an explicit threshold.
- All v0.4 Evidence has subject, source_ref, bounded redaction metadata, location, SHA-256 content hash, provider, extractor, timestamp, and loop provenance; status is only verified or unverified.
- Context and report are untrusted data. No report, Requirement, test, stdout, or model field may become shell/policy instructions; subprocess calls use argv arrays and shell=False.
- The analyzed repository and the user worktree remain read-only. Mutation execution uses a controlled temporary copy; WRITE, COMMIT, MERGE, and RELEASE are denied.
- v0.4 trace databases are explicit durable outputs outside the analyzed repository and use additive SQLite migrations with PRAGMA user_version; existing tables are never removed or rewritten.
- Every task follows RED → GREEN → REFACTOR, runs the smallest relevant test first, and ends with an exact-path commit. A test pass does not constitute real-project, CI, release, or external indexing evidence.
- Do not update root README, roadmap, CHANGELOG, or release metadata to claim v0.4 shipped until the final verification task has the required implementation and benchmark evidence.

---

### Task 1: Synchronize the v0.4 engineering pack

**Files:**

- Modify: docs/v0.4-engineering/README.md
- Modify: docs/v0.4-engineering/ARCHITECTURE.md
- Modify: docs/v0.4-engineering/DOMAIN_MODEL.md
- Modify: docs/v0.4-engineering/IMPLEMENTATION_PLAN.md
- Modify: docs/v0.4-engineering/ADAPTER_SPEC.md
- Modify: docs/v0.4-engineering/EVIDENCE_AND_GATES.md
- Modify: docs/v0.4-engineering/MODEL_RUNTIME.md
- Modify: docs/v0.4-engineering/EVAL_SPEC.md
- Modify: docs/v0.4-engineering/SECURITY.md
- Modify: docs/v0.4-engineering/AGENT_LOOP.md
- Modify: docs/v0.4-engineering/ISSUE_BACKLOG.md
- Modify: docs/v0.3-engineering/README.md
- Modify: docs/v0.3-engineering/DOMAIN_MODEL.md
- Test: tests/test_documentation_contracts.py

**Interfaces:**

- Produces one consistent source-of-truth pack for TestEffectivenessContext, MutationTraceLink, report schema 1, process/observation statuses, Gate precedence, exact budgets, model boundary, and benchmark evidence.
- Keeps v0.3 documentation describing compatibility rather than silently changing its meaning.

- [ ] **Step 1: Write the failing documentation contract test**

~~~python
from pathlib import Path


def test_v04_pack_lists_the_frozen_contracts() -> None:
    root = Path(__file__).parents[1]
    paths = sorted((root / "docs" / "v0.4-engineering").glob("*.md"))
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    for marker in (
        "TestEffectivenessContext",
        "MutationTraceLink",
        "observation_status",
        "max_report_bytes",
        "report schema 1",
        "incomplete",
        "unverified",
        "allow_dirty",
    ):
        assert marker in text


def test_v03_pack_mentions_explicit_legacy_import() -> None:
    root = Path(__file__).parents[1]
    text = "\n".join(
        (root / "docs" / "v0.3-engineering" / name).read_text(encoding="utf-8")
        for name in ("README.md", "DOMAIN_MODEL.md")
    )
    assert "v0.4" in text
    assert "legacy" in text
    assert "Business Oracle" in text


def test_v04_markdown_fences_are_balanced() -> None:
    root = Path(__file__).parents[1]
    for path in (root / "docs" / "v0.4-engineering").glob("*.md"):
        assert path.read_text(encoding="utf-8").count("```") % 2 == 0
~~~

- [ ] **Step 2: Run the contract test and verify it fails**

Run: /opt/homebrew/bin/pytest tests/test_documentation_contracts.py -q

Expected: FAIL because the current v0.4 pack does not contain the complete context, report, gate, and benchmark vocabulary.

- [ ] **Step 3: Update the engineering pack**

Write the same approved boundaries into each corresponding file:

1. ARCHITECTURE and DOMAIN_MODEL list Requirement → Context → MutationRun → MutationTraceLink → Assessment/Gate and state that backend process status is not Agent termination.
2. IMPLEMENTATION_PLAN and ISSUE_BACKLOG assign the exact package/test files used by later tasks.
3. ADAPTER_SPEC freezes detect/run/parse signatures, typed errors, fixtures, capability contracts, and the four adapter security contracts.
4. EVIDENCE_AND_GATES freezes the Evidence envelope, score denominator, Gate precedence, and verified/unverified boundary.
5. AGENT_LOOP freezes phase order, permission-before-action, budget counters, replan limit, LoopTrace fields, and terminal reasons.
6. MODEL_RUNTIME freezes one task type, one model call, structured output, fallback metadata, and no provider-specific business logic.
7. EVAL_SPEC and SECURITY freeze the benchmark manifest, dirty-tree policy, artifact hashes, redaction limits, command allowlist, and no-write boundary.
8. v0.3 README and DOMAIN_MODEL document optional appended fields, explicit v0.3 import, and fail-closed behavior for missing Oracle semantics.

- [ ] **Step 4: Run the contract test and documentation checks**

Run: /opt/homebrew/bin/pytest tests/test_documentation_contracts.py -q

Expected: PASS.

Run: git diff --check

Expected: no output.

- [ ] **Step 5: Commit**

~~~bash
git add docs/v0.4-engineering docs/v0.3-engineering/README.md docs/v0.3-engineering/DOMAIN_MODEL.md tests/test_documentation_contracts.py
git commit -m "docs: synchronize v0.4 engineering pack"
~~~

### Task 2: Preserve v0.3 contracts and extend Evidence provenance

**Files:**

- Modify: packages/qa_agent/test_engineering.py
- Modify: packages/qa_agent/test_engineering_service.py
- Modify: packages/qa_agent/review.py
- Modify: packages/qa_agent/requirements.py
- Modify: tests/test_test_engineering.py
- Modify: tests/test_test_engineering_service.py
- Modify: tests/test_trace_store.py
- Create: tests/test_v03_compatibility.py

**Interfaces:**

- TestIntent appends acceptance_criterion_ids: tuple[str, ...] = (), risk_ids: tuple[str, ...] = (), observable_behavior: str | None = None, and business_oracle: str | None = None.
- TestScenario appends business_oracle: str | None = None, acceptance_criterion_ids: tuple[str, ...] = (), and test_ids: tuple[str, ...] = ().
- TestEngineeringRequest appends those four fields after framework so current positional calls remain valid.
- Evidence appends optional subject, source_ref, redacted_excerpt, and metadata fields; legacy serializers omit empty v0.4-only fields.

- [ ] **Step 1: Write failing compatibility tests**

~~~python
def test_v03_result_keeps_legacy_wire_shape() -> None:
    from qa_agent.test_engineering import TestCandidateStatus, TestEngineeringResult, TestIntent

    payload = TestEngineeringResult(
        intent=TestIntent("TI-1", "REQ-1", "checkout", ("EV-REQ-001",)),
        status=TestCandidateStatus("rejected", "INSUFFICIENT_EVIDENCE", ("EV-REQ-001",)),
    ).to_dict()

    assert payload["schema_version"] == "v0.3"
    assert set(payload["intent"]) == {"id", "requirement_id", "subject", "evidence_ids"}


def test_semantic_fields_are_appended_without_changing_old_arguments() -> None:
    from pathlib import Path
    from qa_agent.test_engineering import TestIntent
    from qa_agent.test_engineering_service import TestEngineeringRequest

    intent = TestIntent("TI-1", "REQ-1", "checkout", ("EV-1",), ("AC-1",), ("RISK-1",), "decline", "error is visible")
    request = TestEngineeringRequest("REQ-1", Path("."), ("EV-1",), 60, 0, ("tests",), "pytest", ("AC-1",), ("RISK-1",), "decline", "error is visible")
    assert intent.business_oracle == "error is visible"
    assert request.acceptance_criterion_ids == ("AC-1",)
~~~

- [ ] **Step 2: Run the compatibility tests and verify they fail**

Run: /opt/homebrew/bin/pytest tests/test_v03_compatibility.py tests/test_test_engineering.py -q

Expected: FAIL because the constructors do not accept semantic fields and legacy serialization currently uses dataclasses without a v0.4 field filter.

- [ ] **Step 3: Add appended fields and explicit legacy serializers**

Add the four optional fields exactly after the current positional fields. Add Evidence extension fields with empty-compatible defaults. Implement serializer helpers that emit the original v0.3/v0.2 shape when the result schema is legacy, while v0.4 callers can request the complete envelope. Update ReviewResult, RequirementResult, and TestEngineeringResult to use these helpers instead of exposing empty extension keys through asdict.

Keep TestEngineeringService’s old generated candidate subject and expected outcome for requests without semantic fields. Do not turn generated-candidate or test passes into a Business Oracle.

- [ ] **Step 4: Run focused regression tests**

Run: /opt/homebrew/bin/pytest tests/test_v03_compatibility.py tests/test_test_engineering.py tests/test_test_engineering_service.py tests/test_trace_store.py -q

Expected: PASS, including all existing v0.3 behavior tests.

- [ ] **Step 5: Commit**

~~~bash
git add packages/qa_agent/test_engineering.py packages/qa_agent/test_engineering_service.py packages/qa_agent/review.py packages/qa_agent/requirements.py tests/test_v03_compatibility.py tests/test_test_engineering.py tests/test_test_engineering_service.py tests/test_trace_store.py
git commit -m "feat: extend v0.3 semantics without breaking legacy output"
~~~

### Task 3: Add bounded v0.4 runtime controls

**Files:**

- Modify: packages/qa_agent/runtime.py
- Modify: packages/qa_agent/review.py
- Modify: packages/qa_agent/requirements.py
- Modify: packages/qa_agent/test_engineering.py
- Create: tests/test_runtime_v04.py

**Interfaces:**

- ExecutionBudget gains max_replans, max_mutants, max_report_bytes, and max_context_bytes, plus classmethod v04_defaults() -> ExecutionBudget and validate(v04: bool = False) -> None.
- PermissionContext is a frozen dataclass containing repository, controlled_copy, allowed_actions, approval_required_actions, max_command_args, and max_file_bytes.
- PermissionResult is a frozen dataclass containing action, allowed, reason, evidence_id, and external_command_executed.
- TerminationPolicy.evaluate(*, budget: ExecutionBudget, iteration, tool_calls, model_calls, replans, elapsed_seconds, permission, process_observation_complete, evidence_sufficient) -> str | None; existing should_stop(state, budget) remains for legacy services.
- LoopTrace preserves its first four positional fields and appends assessment_id, phase, permission_evidence_id, evidence_ids, and termination_reason with legacy-compatible defaults.

- [ ] **Step 1: Write failing runtime tests**

~~~python
def test_v04_budget_has_fixed_defaults() -> None:
    from qa_agent.runtime import ExecutionBudget

    budget = ExecutionBudget.v04_defaults()
    assert budget.max_iterations == 8
    assert budget.max_tool_calls == 8
    assert budget.max_model_calls == 1
    assert budget.timeout_seconds == 120
    assert budget.max_replans == 1
    assert budget.max_mutants == 500
    assert budget.max_report_bytes == 2_000_000
    assert budget.max_context_bytes == 1_000_000


def test_termination_policy_checks_permission_timeout_budget_in_order() -> None:
    from qa_agent.runtime import ExecutionBudget, PermissionResult, TerminationPolicy

    budget = ExecutionBudget.v04_defaults()
    permission = PermissionResult("WRITE", False, "policy denied", "EV-PERM-1", False)
    reason = TerminationPolicy().evaluate(
        budget=budget,
        iteration=1, tool_calls=0, model_calls=0, replans=0,
        elapsed_seconds=0, permission=permission,
        process_observation_complete=False, evidence_sufficient=False,
    )
    assert reason == "INSUFFICIENT_EVIDENCE"
~~~

- [ ] **Step 2: Run the runtime tests and verify they fail**

Run: /opt/homebrew/bin/pytest tests/test_runtime_v04.py -q

Expected: FAIL because v0.4 budget fields, permission objects, and evaluate are absent.

- [ ] **Step 3: Implement the runtime controls**

Retain current legacy defaults for ExecutionBudget() and use v04_defaults() only from the effectiveness workflow. Reject negative counters, non-positive timeout/byte limits in v0.4 mode, and invalid action/status values before UNDERSTAND. Use monotonic elapsed seconds. Evaluate permission rejection first, timeout second, budget exhaustion third, and evidence insufficiency fourth. Never let a backend set Agent termination.

Add legacy-aware loop/evidence serialization so the new optional fields do not alter v0.1-v0.3 JSON when they are unused.

- [ ] **Step 4: Run focused and legacy runtime tests**

Run: /opt/homebrew/bin/pytest tests/test_runtime_v04.py tests/test_runtime_services.py tests/test_review_service.py -q

Expected: PASS.

- [ ] **Step 5: Commit**

~~~bash
git add packages/qa_agent/runtime.py packages/qa_agent/review.py packages/qa_agent/requirements.py packages/qa_agent/test_engineering.py tests/test_runtime_v04.py
git commit -m "feat: add bounded v0.4 runtime policy"
~~~

### Task 4: Implement v0.4 domain models, context validation, scoring, and Gate

**Files:**

- Create: packages/qa_agent/effectiveness.py
- Create: tests/test_effectiveness.py
- Create: tests/fixtures/v04/context-valid.json

**Interfaces:**

- TestEffectivenessContext.from_dict(payload: dict[str, Any], max_bytes: int) -> TestEffectivenessContext and to_dict() -> dict[str, Any].
- Domain dataclasses: Mutant, MutationResult, MutationRun, MutationTraceLink, EffectivenessScore, FakeTestSignal, MutationGateResult, and TestEffectivenessAssessment.
- MutationRun constructor order: run_id, assessment_id, backend, repository_revision, target_paths, selected_test_paths, selected_test_ids, process_status, observation_status, mutant_ids, evidence_ids.
- MutationResult constructor order: run_id, mutant_id, outcome, executed_test_ids, killing_test_ids, duration_ms, stdout_hash, stderr_hash, evidence_ids.
- canonical_json_bytes(value: object) -> bytes and artifact_hash(value: object, omit_field: str | None = None) -> str.
- score_results(results: Sequence[MutationResult], evidence_ids: Sequence[str]) -> EffectivenessScore.
- evaluate_mutation_gate(context_valid: bool, run: MutationRun | None, score: EffectivenessScore, links: Sequence[MutationTraceLink], signals: Sequence[FakeTestSignal], threshold: float | None, execution_evidence: Sequence[Evidence], assertion_evidence: Sequence[Evidence], termination_reason: str) -> MutationGateResult.

- [ ] **Step 1: Write failing model and Gate tests**

~~~python
def test_partial_one_killed_and_many_not_run_never_passes() -> None:
    from qa_agent.effectiveness import MutationResult, MutationRun, score_results, evaluate_mutation_gate

    results = [
        MutationResult("RUN-1", "M-1", "killed", ("tests/test_checkout.py::test_declined",), ("tests/test_checkout.py::test_declined",), 1, None, None, ("EV-M-1",)),
    ] + [
        MutationResult("RUN-1", f"M-{index}", "not_run", (), (), 0, None, None, (f"EV-M-{index}",))
        for index in range(2, 101)
    ]
    score = score_results(results, ("EV-SCORE-1",))
    run = MutationRun("RUN-1", "ASSESS-1", "offline", "REV-1", ("src/checkout.py",), ("tests/test_checkout.py",), ("tests/test_checkout.py::test_declined",), "partial", "complete", tuple(item.mutant_id for item in results), ("EV-RUN-1",))
    from qa_agent.review import Evidence
    evidence_metadata = {"redaction": {"applied": False, "policy": "bounded-redacted-v1", "max_bytes": 4096}, "limits": {"context_bytes": 1_000_000, "report_bytes": 2_000_000}}
    verified_execution = Evidence("EV-EXEC-1", "test_execution", "tests/test_checkout.py", 1, 1, "sha256:" + "e" * 64, subject="tests/test_checkout.py::test_declined", source_ref="tests/test_checkout.py#L1", metadata=evidence_metadata)
    verified_assertion = Evidence("EV-ASSERT-1", "test_assertion", "tests/test_checkout.py", 1, 1, "sha256:" + "a" * 64, subject="tests/test_checkout.py::test_declined", source_ref="tests/test_checkout.py#L1", metadata=evidence_metadata)
    gate = evaluate_mutation_gate(True, run, score, (), (), 0.8, [verified_execution], [verified_assertion], "EVIDENCE_SUFFICIENT")
    assert score.score == 1.0
    assert gate.decision == "warn"


def test_unmapped_survivor_keeps_null_semantic_fields() -> None:
    from qa_agent.effectiveness import MutationTraceLink

    link = MutationTraceLink("RUN-1", "M-1", None, None, None, None, "unmapped", ("EV-M-1",))
    assert link.mapping_status == "unmapped"
    assert link.intent_id is None
~~~

- [ ] **Step 2: Run the model tests and verify they fail**

Run: /opt/homebrew/bin/pytest tests/test_effectiveness.py -q

Expected: FAIL because packages/qa_agent/effectiveness.py does not exist.

- [ ] **Step 3: Implement the domain contracts**

Parse bounded arrays, repository-relative normalized target/test paths, unique IDs, exact context schema v0.4, evidence references, canonical artifact hashes, and verified/unverified Evidence status. Reject mismatched self-hashes, missing Oracle/criterion Evidence, invalid line ranges, duplicate IDs, and legacy imported context without explicit import_v03 handling.

Implement the five-outcome result partition and the score count invariant eligible = killed + survived. Serialize score with Decimal half-up to four places. Implement Gate predicates input_complete, assessable_run, quality_failure, and clean_pass in the fixed precedence incomplete → fail → pass → warn. A partial run with observation_status complete may warn/fail; a truncated or unknown observation is incomplete. A low score is fail only when inputs and observation are complete.

- [ ] **Step 4: Run focused domain tests**

Run: /opt/homebrew/bin/pytest tests/test_effectiveness.py -q

Expected: PASS for valid context, canonical hash, enum validation, score boundaries, high-risk signal escalation, all Gate branches, and killed=1/not_run=99.

- [ ] **Step 5: Commit**

~~~bash
git add packages/qa_agent/effectiveness.py tests/test_effectiveness.py tests/fixtures/v04/context-valid.json
git commit -m "feat: add v0.4 effectiveness domain contracts"
~~~

### Task 5: Freeze backend protocol, capability records, and typed errors

**Files:**

- Create: packages/qa_agent/mutation_backends.py
- Create: tests/test_mutation_backends.py

**Interfaces:**

- MutationBackend protocol: detect(repository: Path) -> BackendCapability and run(request: MutationRequest) -> MutationBackendResult.
- BackendCapability fields: backend, status, tool_version, languages, frameworks, reason, limits, and evidence.
- MutationRequest fields: repository, repository_revision, target_paths, selected_test_ids, selected_test_paths, timeout_seconds, max_mutants, and permission_context.
- MutationBackendResult fields: backend, tool_version, process_status, observation_status, mutants, results, evidence, and raw_report_hash; it has no Agent termination or Gate decision.
- MutationBackendResult constructor order: backend, tool_version, process_status, observation_status, mutants, results, evidence, raw_report_hash.
- Typed errors: MutationInputError, MutationUnavailableError, MutationUnsupportedError, MutationConfigurationError, and MutationExecutionError.

- [ ] **Step 1: Write failing protocol tests**

~~~python
def test_backend_result_has_process_not_agent_termination() -> None:
    from qa_agent.mutation_backends import BackendCapability, MutationBackendResult

    capability = BackendCapability("offline", "available", None, ("Python",), ("pytest",), None, {}, ())
    result = MutationBackendResult("offline", None, "partial", "complete", (), (), (), "sha256:" + "1" * 64)
    assert capability.status == "available"
    assert result.process_status == "partial"
    assert not hasattr(result, "termination_reason")


def test_typed_backend_errors_are_distinct() -> None:
    from qa_agent.mutation_backends import MutationInputError, MutationUnavailableError

    assert not issubclass(MutationInputError, MutationUnavailableError)
    assert str(MutationInputError("bad report")) == "bad report"
~~~

- [ ] **Step 2: Run the protocol tests and verify they fail**

Run: /opt/homebrew/bin/pytest tests/test_mutation_backends.py -q

Expected: FAIL because the backend module and result contracts are absent.

- [ ] **Step 3: Implement the protocol and validators**

Use frozen dataclasses for value records, Literal-equivalent runtime validation for process/observation/capability statuses, and a runtime-checkable Protocol. Keep all command construction out of the protocol. Validate target/test path boundaries and max_mutants before a backend receives a request.

- [ ] **Step 4: Run focused tests**

Run: /opt/homebrew/bin/pytest tests/test_mutation_backends.py -q

Expected: PASS.

- [ ] **Step 5: Commit**

~~~bash
git add packages/qa_agent/mutation_backends.py tests/test_mutation_backends.py
git commit -m "feat: define mutation backend contracts"
~~~

### Task 6: Implement offline report parsing and tool adapter boundaries

**Files:**

- Create: packages/qa_agent/mutation_adapters.py
- Create: tests/test_mutation_adapters.py
- Create: tests/fixtures/v04/mutation/report-valid.json
- Create: tests/fixtures/v04/mutation/report-prompt-data.json
- Create: tests/fixtures/v04/mutation/report-partial.json

**Interfaces:**

- OfflineMutationReportAdapter.parse(report_path: Path, repository_revision: str, limits: ExecutionBudget) -> MutationBackendResult.
- MutmutMutationBackend, PitMutationBackend, and StrykerMutationBackend implement MutationBackend.
- Offline report v1 requires schema_version integer 1, backend, repository_revision, observation_status, target_paths, selected_test_ids, and mutants.
- Each mutant requires id, path, positive line, operator, original, mutated, outcome, executed_test_ids, and killing_test_ids; executed IDs are a subset of selected IDs, and killed IDs are a subset of executed IDs.

- [ ] **Step 1: Write failing adapter tests**

~~~python
import json


def test_offline_parser_normalizes_valid_report(tmp_path) -> None:
    from qa_agent.mutation_adapters import OfflineMutationReportAdapter
    from qa_agent.runtime import ExecutionBudget

    report = {
        "schema_version": 1,
        "backend": "offline",
        "repository_revision": "REV-1",
        "observation_status": "complete",
        "target_paths": ["src/cart.py"],
        "selected_test_ids": ["tests/test_cart.py::test_declined"],
        "mutants": [{
            "id": "M-1", "path": "src/cart.py", "line": 12,
            "operator": "replace-constant", "original": "False",
            "mutated": "True", "outcome": "killed",
            "executed_test_ids": ["tests/test_cart.py::test_declined"],
            "killing_test_ids": ["tests/test_cart.py::test_declined"],
            "duration_ms": 1, "stdout_hash": None, "stderr_hash": None,
        }],
    }
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    result = OfflineMutationReportAdapter().parse(path, "REV-1", ExecutionBudget.v04_defaults())
    assert result.results[0].outcome == "killed"
    assert result.observation_status == "complete"


def test_prompt_data_is_never_executed(tmp_path) -> None:
    from pathlib import Path
    from qa_agent.mutation_adapters import OfflineMutationReportAdapter
    from qa_agent.runtime import ExecutionBudget

    path = tmp_path / "report.json"
    fixture = Path(__file__).parent / "fixtures" / "v04" / "mutation" / "report-prompt-data.json"
    path.write_bytes(fixture.read_bytes())
    result = OfflineMutationReportAdapter().parse(path, "REV-1", ExecutionBudget.v04_defaults())
    assert result.results[0].outcome == "survived"
~~~

- [ ] **Step 2: Run adapter tests and verify they fail**

Run: /opt/homebrew/bin/pytest tests/test_mutation_adapters.py -q

Expected: FAIL because the parser and adapters are absent.

- [ ] **Step 3: Implement strict parsing and capability adapters**

Read raw report bytes once, reject files above max_report_bytes, compute raw SHA-256 before JSON parsing, parse only JSON data, and reject malformed JSON, duplicate IDs, missing fields, invalid outcomes, path escape, oversized strings/arrays, mismatched revision, and inconsistent executed/killing IDs. Return typed errors without partial success.

Derive process_status from explicit outcomes and observation_status. A complete observation with explicit not_run/timeout/error entries is partial; a report that may be truncated is observation_status partial and cannot pass the Gate. Use no shell command from report fields.

Mutmut detection uses shutil.which and records unavailable capability without downloading anything. Its run path constructs a fixed allowlisted argv, copies into a temporary controlled directory, applies timeout/resource limits, and returns only process observation. PIT and Stryker return capability plus typed unsupported/unavailable/configuration results in this slice and never pretend to execute.

- [ ] **Step 4: Run adapter and security tests**

Run: /opt/homebrew/bin/pytest tests/test_mutation_adapters.py tests/test_mutation_backends.py -q

Expected: PASS for valid, partial, duplicate, bad-version, unknown-outcome, path-escape, oversized, prompt-in-data, capability, typed error, and no-download cases.

- [ ] **Step 5: Commit**

~~~bash
git add packages/qa_agent/mutation_adapters.py tests/test_mutation_adapters.py tests/fixtures/v04/mutation
git commit -m "feat: add offline mutation report and adapter contracts"
~~~

### Task 7: Add additive SQLite persistence and Evidence queries

**Files:**

- Modify: packages/qa_agent/trace_store.py
- Create: tests/test_trace_store_v04.py

**Interfaces:**

- SQLiteTraceStore.save_evidence(records: Sequence[Evidence]) -> None and get_evidence_by_ids(ids: Sequence[str], limit: int) -> list[Evidence].
- SQLiteTraceStore.save_test_context(context: TestEffectivenessContext) -> None and get_test_context(context_id: str) -> TestEffectivenessContext | None.
- SQLiteTraceStore.save_mutation(run: MutationRun, mutants: Sequence[Mutant], results: Sequence[MutationResult], links: Sequence[MutationTraceLink]) -> None.
- SQLiteTraceStore.save_assessment(assessment: TestEffectivenessAssessment) -> None and get_assessment(assessment_id: str) -> TestEffectivenessAssessment | None.
- Legacy save_requirement/get_requirement/replace_links/get_links behavior remains unchanged.

- [ ] **Step 1: Write failing migration and round-trip tests**

~~~python
def test_v04_migration_preserves_legacy_tables_and_adds_explicit_links(tmp_path) -> None:
    from qa_agent.trace_store import SQLiteTraceStore

    store = SQLiteTraceStore(tmp_path / "trace.db")
    with store._connect() as connection:
        names = {
            row[0]
            for row in connection.execute("select name from sqlite_master where type = 'table'")
        }
        version = connection.execute("pragma user_version").fetchone()[0]
    assert {"requirements", "trace_links", "test_contexts", "mutation_runs", "mutation_results", "mutation_trace_links", "assessments", "observations", "loop_traces"} <= names
    assert version == 2


def test_v04_evidence_query_is_bounded_and_round_trips(tmp_path) -> None:
    from qa_agent.review import Evidence
    from qa_agent.trace_store import SQLiteTraceStore

    store = SQLiteTraceStore(tmp_path / "trace.db")
    evidence = Evidence("EV-1", "test_context", "context.json", 1, 1, "sha256:" + "1" * 64, subject="CTX-1", source_ref="context.json#L1", metadata={"redaction": {"applied": False, "policy": "bounded-redacted-v1", "max_bytes": 4096}, "limits": {"context_bytes": 10, "report_bytes": 10}})
    store.save_evidence([evidence])
    assert store.get_evidence_by_ids(["EV-1"], 1) == [evidence]
~~~

- [ ] **Step 2: Run the store tests and verify they fail**

Run: /opt/homebrew/bin/pytest tests/test_trace_store_v04.py tests/test_trace_store.py -q

Expected: FAIL because the generic Evidence and v0.4 tables/methods are absent.

- [ ] **Step 3: Implement additive schema version 2**

Enable foreign_keys on every connection. For user_version 0, preserve the existing requirements and trace_links tables and create evidence_records, test_contexts, mutation_runs, mutants, mutation_results, mutation_trace_links, assessments, observations, and loop_traces with the exact columns from the spec. Use CREATE TABLE IF NOT EXISTS and CREATE INDEX IF NOT EXISTS only; set user_version to 2 after a transaction. Reject versions above 2.

Store canonical JSON in *_json columns, keep run_id/context_id/assessment_id/observation_id as explicit columns and relationships, sort query results by stable IDs, and apply the supplied result limit before serialization. Do not store credentials or raw unbounded output.

- [ ] **Step 4: Run store and legacy tests**

Run: /opt/homebrew/bin/pytest tests/test_trace_store_v04.py tests/test_trace_store.py tests/test_requirement_cli.py -q

Expected: PASS.

- [ ] **Step 5: Commit**

~~~bash
git add packages/qa_agent/trace_store.py tests/test_trace_store_v04.py
git commit -m "feat: add additive v0.4 trace persistence"
~~~

### Task 8: Implement the deterministic effectiveness service loop

**Files:**

- Create: packages/qa_agent/effectiveness_service.py
- Create: tests/test_effectiveness_service.py
- Modify: tests/conftest.py

**Interfaces:**

- TestEffectivenessRequest fields: requirement_id: str, repository: Path, context: TestEffectivenessContext | None, mutation_report: Path | None, backend: MutationBackend | None, min_score: float | None, budget: ExecutionBudget.
- TestEffectivenessService(store: SQLiteTraceStore | None = None, model_mapper: "SurvivorMappingProvider | None" = None); use a forward annotation in Task 8 and define the runtime-checkable protocol in Task 9.
- TestEffectivenessService.assess(request: TestEffectivenessRequest) -> TestEffectivenessAssessment.
- resolve_repository_revision(repository: Path) -> str uses local git HEAD when available, otherwise a deterministic repository tree hash; it never fetches or uses network.
- tests/conftest.py provides valid_context from the Task 4 fixture and valid_report from the Task 6 fixture; service tests patch the revision observation to REV-1 when using the fixed report.

~~~python
import json
from pathlib import Path

import pytest

from qa_agent.effectiveness import TestEffectivenessContext


@pytest.fixture
def valid_context() -> TestEffectivenessContext:
    fixture = Path(__file__).parent / "fixtures" / "v04" / "context-valid.json"
    return TestEffectivenessContext.from_dict(json.loads(fixture.read_text(encoding="utf-8")), 1_000_000)


@pytest.fixture
def valid_report(tmp_path: Path) -> Path:
    source = Path(__file__).parent / "fixtures" / "v04" / "mutation" / "report-valid.json"
    target = tmp_path / "report.json"
    target.write_bytes(source.read_bytes())
    return target
~~~

- [ ] **Step 1: Write failing loop tests**

~~~python
def test_missing_context_stops_before_backend(tmp_path) -> None:
    from qa_agent.effectiveness_service import TestEffectivenessRequest, TestEffectivenessService
    from qa_agent.runtime import ExecutionBudget

    class Backend:
        called = False
        def detect(self, repository):
            self.called = True
            raise AssertionError("backend must not run")
        def run(self, request):
            self.called = True
            raise AssertionError("backend must not run")

    backend = Backend()
    assessment = TestEffectivenessService().assess(
        TestEffectivenessRequest("REQ-1", tmp_path, None, None, backend, 0.8, ExecutionBudget.v04_defaults())
    )
    assert assessment.decision == "incomplete"
    assert assessment.termination_reason == "INSUFFICIENT_EVIDENCE"
    assert backend.called is False


def test_exact_identity_creates_verified_survivor_link(tmp_path, valid_context, valid_report, monkeypatch) -> None:
    import qa_agent.effectiveness_service as effectiveness_service
    from qa_agent.effectiveness_service import TestEffectivenessRequest, TestEffectivenessService
    from qa_agent.runtime import ExecutionBudget

    monkeypatch.setattr(effectiveness_service, "resolve_repository_revision", lambda _: "REV-1")
    assessment = TestEffectivenessService().assess(
        TestEffectivenessRequest("REQ-1", tmp_path, valid_context, valid_report, None, 0.8, ExecutionBudget.v04_defaults())
    )
    assert assessment.termination_reason == "EVIDENCE_SUFFICIENT"
    assert all(link.mapping_status == "verified" for link in assessment.survivor_links)
~~~

- [ ] **Step 2: Run service tests and verify they fail**

Run: /opt/homebrew/bin/pytest tests/test_effectiveness_service.py -q

Expected: FAIL because the service module and assessment workflow are absent.

- [ ] **Step 3: Implement the fixed phase loop**

Run phases in this exact order: UNDERSTAND, SELECT, MUTATE, OBSERVE, MAP, EVALUATE, VERIFY, GATE, DECIDE/STOP. At every phase create an Observation before its Evidence and append a LoopTrace. Check permissions before SELECT and MUTATE. Stop in UNDERSTAND when context is missing/invalid; do not call detect/run or create a mutation process.

For offline reports, resolve repository revision, parse with OfflineMutationReportAdapter, and validate report target paths/test IDs as context subsets. For a backend, call detect then run only when capability is available and the permission result allows EXECUTE_MUTATION. Inject deterministic run/assessment IDs after the backend returns. Convert typed errors to Agent-owned Evidence and the termination mapping from the spec.

Map killed and survivor results using exact executed test IDs, scenario test IDs, verified scenario/intent/oracle Evidence, and run-selected IDs only when they uniquely identify one scenario. Emit unverified for explainable heuristic candidates and unmapped with null semantic fields when no candidate exists. Never infer a verified link from path/token similarity.

Compute score and deterministic signals, verify all referenced Evidence, then call evaluate_mutation_gate. Set EVIDENCE_SUFFICIENT only after VERIFY succeeds; use TIMEOUT/BUDGET_EXHAUSTED/HUMAN_APPROVAL_REQUIRED/ERROR when the runtime stops earlier. Persist every observation, trace, run, result, link, signal, and assessment through the trace store.

- [ ] **Step 4: Run service tests and adversarial boundaries**

Run: /opt/homebrew/bin/pytest tests/test_effectiveness_service.py tests/test_effectiveness.py tests/test_mutation_adapters.py -q

Expected: PASS for phase ordering, no backend on missing context, verified/unverified/unmapped mapping, partial report warning, threshold failure, high-risk failure, missing Evidence, revision conflict, budget exhaustion, permission rejection, and deterministic repeated input.

- [ ] **Step 5: Commit**

~~~bash
git add packages/qa_agent/effectiveness_service.py tests/test_effectiveness_service.py
git commit -m "feat: implement deterministic effectiveness loop"
~~~

### Task 9: Add optional schema-validated model mapping metadata

**Files:**

- Modify: packages/qa_agent/model_runtime.py
- Modify: packages/qa_agent/effectiveness_service.py
- Create: tests/test_model_runtime.py

**Interfaces:**

- ModelFallbackMetadata fields: fallback_used: bool, requested_provider: str | None, selected_provider: str | None, fallback_reason: str | None.
- ModelResponse carries the fallback metadata with defaults that preserve current provider call sites.
- validate_model_mapping(payload: dict[str, Any], known_ids: dict[str, set[str]]) -> list[dict[str, str | None]] rejects unknown IDs, missing rationale, duplicate mutant links, and output keys outside the fixed schema.
- SurvivorMappingProvider.map(context: dict[str, Any], survivor_ids: tuple[str, ...]) -> ModelResponse is the only optional model hook; the default is None and it cannot mutate AgentState or Evidence status.
- The only v0.4 task type is effectiveness-survivor-mapping; output schema is links containing mutant_id, requirement_id, intent_id, scenario_id, oracle, and rationale.
- Model mapping is disabled by default, limited to one call, receives only redacted bounded context, and can only produce unverified links until deterministic Evidence verification accepts the IDs.

- [ ] **Step 1: Write failing model contract tests**

~~~python
def test_model_response_retains_explicit_fallback_metadata() -> None:
    from qa_agent.model_runtime import ModelFallbackMetadata, ModelResponse

    response = ModelResponse(
        "injected", "test-model", structured_output={"links": []},
        fallback=ModelFallbackMetadata(True, "primary", "secondary", "primary unavailable"),
    )
    assert response.fallback.fallback_used is True
    assert response.fallback.selected_provider == "secondary"


def test_invalid_model_mapping_ids_are_not_accepted() -> None:
    from qa_agent.effectiveness_service import validate_model_mapping

    result = validate_model_mapping({"links": [{"mutant_id": "M-1", "intent_id": "UNKNOWN"}]}, {"mutant_ids": {"M-1"}, "intent_ids": {"TI-1"}})
    assert result == []
~~~

- [ ] **Step 2: Run model tests and verify they fail**

Run: /opt/homebrew/bin/pytest tests/test_model_runtime.py -q

Expected: FAIL because fallback metadata and mapping validation are absent.

- [ ] **Step 3: Implement metadata and strict mapping validation**

Add the metadata as an additive ModelResponse field without changing existing positional arguments. Validate task type, structured output capability, one-call budget, bounded redacted context, exact output keys, known IDs, non-empty rationale, and fallback metadata. A provider error, schema error, or policy denial keeps links unverified/unmapped and never changes the Gate.

- [ ] **Step 4: Run model and service tests**

Run: /opt/homebrew/bin/pytest tests/test_model_runtime.py tests/test_effectiveness_service.py -q

Expected: PASS.

- [ ] **Step 5: Commit**

~~~bash
git add packages/qa_agent/model_runtime.py packages/qa_agent/effectiveness_service.py tests/test_model_runtime.py
git commit -m "feat: constrain optional survivor model mapping"
~~~

### Task 10: Add CLI, v0.4 evals, and the reference example

**Files:**

- Modify: packages/qa_agent/cli.py
- Modify: packages/qa_agent/evals.py
- Create: tests/test_cli_effectiveness.py
- Create: tests/test_v04_evals.py
- Create: evals/v04/README.md
- Create: evals/v04/cases.json
- Create: examples/v04-sample/README.md
- Create: examples/v04-sample/requirement.md
- Create: examples/v04-sample/test-context.json
- Create: examples/v04-sample/mutation-report.json
- Create: examples/v04-sample/repository/src/checkout.py
- Create: examples/v04-sample/repository/tests/test_checkout.py

**Interfaces:**

- CLI command: qa-agent assess-effectiveness with optional parser flags requirement, repository, trace-db, test-context, mutation-report, backend choices mutmut/pit/stryker, min-score, and format human/json.
- _render_effectiveness(assessment, output_format) prints the exact v0.4 JSON envelope or all required human fields.
- Missing semantic inputs produce decision incomplete, termination_reason INSUFFICIENT_EVIDENCE, exit 2, and no database creation.
- qa-agent eval --version v0.4 runs parser, mapping, score, signal, budget, termination, and adversarial cases.

- [ ] **Step 1: Write failing CLI/eval tests**

~~~python
def test_missing_effectiveness_arguments_are_structured_and_do_not_create_db(tmp_path, capsys) -> None:
    from qa_agent.cli import main

    database = tmp_path / "trace.db"
    assert main(["assess-effectiveness", "--format", "json", "--trace-db", str(database)]) == 2
    output = capsys.readouterr().out
    assert '"decision": "incomplete"' in output
    assert '"termination_reason": "INSUFFICIENT_EVIDENCE"' in output
    assert not database.exists()


def test_v04_eval_command_is_registered(capsys) -> None:
    from qa_agent.cli import main

    assert main(["eval", "--version", "v0.4"]) == 0
    assert '"failures": []' in capsys.readouterr().out
~~~

- [ ] **Step 2: Run CLI/eval tests and verify they fail**

Run: /opt/homebrew/bin/pytest tests/test_cli_effectiveness.py tests/test_v04_evals.py -q

Expected: FAIL because the command, v0.4 eval choice, and fixtures are absent.

- [ ] **Step 3: Implement parser validation and output**

Make all v0.4 command flags optional at argparse construction and perform semantic validation before SQLiteTraceStore construction. Enforce exactly one of mutation-report/backend, explicit min-score in [0, 1] excluding NaN/Infinity, existing repository directory, existing context/report files, and trace-db outside the repository with a writable parent. Use the fixed missing-input JSON object from the spec. Unknown flags remain argparse usage errors. Exit pass/warn 0, fail 1, incomplete/invalid 2, internal error 3.

Load context with max_context_bytes, construct the offline parser or fixed backend, pass the explicit ExecutionBudget, render assessment JSON with mutation_run/score/survivor_links/signals/evidence_ids/loop_trace/budget/gate/artifacts, and never read a command from report/Requirement/model data.

- [ ] **Step 4: Add eval cases and reference files**

Create eval cases for valid pass, partial warning, low-score failure, missing Oracle, unmapped survivor, bad revision, duplicate ID, path escape, prompt-in-data, permission denial, budget exhaustion, and unavailable backend. Keep their labels and expected outcomes in evals/v04/cases.json. Create a reference sample whose context includes target_paths/test_paths, exact test identity, verified requirement/criterion/test/execution Evidence, and a version-1 report. Run the sample against examples/v04-sample/repository, which is outside any Git worktree; resolve_repository_revision hashes sorted relative paths and file bytes in that directory, so the checked-in report revision has no cyclic dependency on the report file. The example test copies that directory to a temporary path and uses the same service without changing the source sample.

- [ ] **Step 5: Run CLI, eval, and reference smoke tests**

Run: /opt/homebrew/bin/pytest tests/test_cli_effectiveness.py tests/test_v04_evals.py tests/test_cli.py -q

Expected: PASS.

Run: PYTHONPATH=packages python3 -m qa_agent.cli eval --version v0.4

Expected: JSON output with failures equal to an empty list and exit 0.

- [ ] **Step 6: Commit**

~~~bash
git add packages/qa_agent/cli.py packages/qa_agent/evals.py tests/test_cli_effectiveness.py tests/test_v04_evals.py evals/v04 examples/v04-sample
git commit -m "feat: expose v0.4 effectiveness CLI and eval"
~~~

### Task 11: Implement real-project benchmark validation and publish the final v0.4 validation docs

**Files:**

- Create: packages/qa_agent/benchmark.py
- Create: tests/test_benchmark.py
- Create: benchmarks/v04/README.md
- Create: benchmarks/v04/manifest.schema.json
- Create: docs/v0.4-engineering/REAL_PROJECT_VALIDATION.md

**Interfaces:**

- load_manifest(path: Path) -> BenchmarkValidationResult validates schema_version 1, case_id, repository path/revision, framework, artifact path/hash records, argv record, allow_dirty, working_tree observation, ground_truth, and adjudication; a valid result carries BenchmarkManifest and an invalid result carries decision incomplete plus reasons.
- validate_case(manifest: BenchmarkManifest) -> BenchmarkValidationResult recomputes artifact hashes/revision and returns incomplete on mismatch without using old results.
- run_case(manifest: BenchmarkManifest) -> BenchmarkCaseResult executes only the fixed assess-effectiveness runner with manifest paths/numeric values, never arbitrary argv.
- aggregate_metrics(results: Sequence[BenchmarkCaseResult]) -> dict[str, float | None] computes precision, recall, false_positive_rate, useful_finding_rate, survivor_explanation_accuracy, cost_per_report, and latency_per_report with None for zero denominators or unmeasured data.

- [ ] **Step 1: Write failing benchmark tests**

~~~python
def test_dirty_case_requires_snapshot_and_reason(tmp_path) -> None:
    from qa_agent.benchmark import load_manifest

    path = tmp_path / "manifest.json"
    path.write_text('{"schema_version": 1, "case_id": "case-1", "allow_dirty": true, "working_tree": {"status": "dirty"}}', encoding="utf-8")
    result = load_manifest(path)
    assert result.decision == "incomplete"
    assert "snapshot_hash" in result.reasons


def test_zero_metric_denominators_are_none() -> None:
    from qa_agent.benchmark import aggregate_metrics

    metrics = aggregate_metrics([])
    assert metrics["precision"] is None
    assert metrics["false_positive_rate"] is None
    assert metrics["cost_per_report"] is None
~~~

- [ ] **Step 2: Run benchmark tests and verify they fail**

Run: /opt/homebrew/bin/pytest tests/test_benchmark.py -q

Expected: FAIL because benchmark.py and the version-1 manifest validator are absent.

- [ ] **Step 3: Implement manifest and case validation**

Use raw bytes for artifact SHA-256, a fixed repository revision observation, and a clean-tree default. Reject dirty trees unless allow_dirty is true with non-empty snapshot_hash and reason; compare snapshots before and after and never clean, overwrite, or reset the original repository. Treat argv as an audit record and construct the actual runner from fixed code, with path and numeric values taken only after bounded validation. Exclude unresolved ground-truth/adjudication cases from precision/recall denominators. Record None for unavailable cost/latency measurements.

- [ ] **Step 4: Write the validation document**

Document the manifest version 1 shape, artifact/hash rules, fixed runner, clean/dirty policy, ground-truth labels, adjudication statuses, metric formulas, evidence boundary, and the difference between reference fixtures and real-project evidence. State that Java/PIT and Playwright/TypeScript count only when their environment and artifacts are reproducible.

- [ ] **Step 5: Run benchmark and documentation tests**

Run: /opt/homebrew/bin/pytest tests/test_benchmark.py tests/test_documentation_contracts.py -q

Expected: PASS.

- [ ] **Step 6: Commit**

~~~bash
git add packages/qa_agent/benchmark.py tests/test_benchmark.py benchmarks/v04 docs/v0.4-engineering/REAL_PROJECT_VALIDATION.md
git commit -m "feat: add reproducible v0.4 benchmark validation"
~~~

### Task 12: Run the complete verification gate and record evidence

**Files:**

- No source-file changes are required; record command output and evidence status in the final handoff.

**Interfaces:**

- The final evidence record distinguishes unit/static checks, CLI/eval smoke, reference-example execution, real-project benchmark, CI, merge, package, release, and external indexing.

- [ ] **Step 1: Run the focused v0.4 suite**

Run: /opt/homebrew/bin/pytest tests/test_v03_compatibility.py tests/test_runtime_v04.py tests/test_effectiveness.py tests/test_mutation_backends.py tests/test_mutation_adapters.py tests/test_trace_store_v04.py tests/test_effectiveness_service.py tests/test_model_runtime.py tests/test_cli_effectiveness.py tests/test_v04_evals.py tests/test_benchmark.py -q

Expected: PASS.

- [ ] **Step 2: Run the complete repository regression**

Run: /opt/homebrew/bin/pytest -q

Expected: all existing and new tests pass with no v0.1-v0.3 regressions.

- [ ] **Step 3: Run versioned evals and CLI smoke**

~~~bash
PYTHONPATH=packages python3 -m qa_agent.cli eval --version v0.1
PYTHONPATH=packages python3 -m qa_agent.cli eval --version v0.2
PYTHONPATH=packages python3 -m qa_agent.cli eval --version v0.3
PYTHONPATH=packages python3 -m qa_agent.cli eval --version v0.4
PYTHONPATH=packages python3 -m qa_agent.cli assess-effectiveness --format json
~~~

Expected: v0.1-v0.4 eval commands exit 0; the missing-input smoke exits 2 and emits the structured incomplete envelope without creating a repository-local database.

- [ ] **Step 4: Run static, documentation, and diff checks**

Run: ruff check packages tests

Expected: PASS; if Ruff is unavailable, record that tool absence as an unverified environment check rather than a code pass.

Run: mypy packages

Expected: PASS; report any environment-only missing configuration separately.

Run: git diff --check

Expected: no output.

Run: /opt/homebrew/bin/pytest tests/test_documentation_contracts.py -q

Expected: PASS, including balanced Markdown fences and v0.4 pack markers.

- [ ] **Step 5: Verify repository scope and status**

Run:

~~~bash
git status --short
git diff --name-only origin/main...HEAD
git log -1 --oneline
~~~

Expected: only the planned v0.4 files are changed; no user worktree changes are reverted; the final report states the exact branch and commit, test results, any unavailable external backend, and the independent status of real-project evidence, CI, merge, package, release, and external indexing.

Do not create a release tag, push, merge, or claim release readiness from local tests alone.
