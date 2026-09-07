# v0.2 Requirement Intelligence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Deliver offline, evidence-backed requirement analysis, trace mapping, and requirement-aware PR review without regressing v0.1.

**Architecture:** Add a small requirement domain, bounded adapters, explicit SQLite storage, and deterministic analysis next to the v0.1 reviewer. Reuse its Evidence, runtime controls, file policy, and ReviewService. Add no dependencies or generic agent framework.

**Tech Stack:** Python 3.11+, standard-library dataclasses, sqlite3, json, pathlib, re, and pytest.

**Spec:** docs/superpowers/specs/2026-09-06-v02-requirement-intelligence-design.md

## Global Constraints

- Preserve every v0.1 command and public contract.
- Stateful commands require --trace-db; never create a default durable path.
- Treat requirements as untrusted: guard size, binary content, and secret names before parsing.
- All findings and links cite evidence; confidence never makes a link verified.
- Do not add network, credentials, repository writes, generated tests, or release actions.

---

### Task 1: Add v0.2 domain contracts

**Files:** Create packages/qa_agent/requirements.py; modify packages/qa_agent/__init__.py; create tests/test_requirements.py.

**Interfaces:** frozen Requirement, AcceptanceCriterion, TestabilityFinding, RiskItem, TraceLink, RequirementResult. Result serialization includes schema_version v0.2 and reuses existing Evidence, GateResult, ExecutionBudget.

- [ ] Write a failing serialization test:

    def test_requirement_result_has_v02_schema() -> None:
        item = Requirement("REQ-1", "Checkout", "body", "markdown", "req.md", (AcceptanceCriterion("REQ-1-AC-1", "Pay", 3),))
        payload = RequirementResult(requirement=item).to_dict()
        assert payload["schema_version"] == "v0.2"
        assert payload["requirement"]["acceptance_criteria"][0]["line"] == 3

- [ ] Run pytest tests/test_requirements.py::test_requirement_result_has_v02_schema -q. Expected: FAIL because the module is absent.
- [ ] Implement dataclass serialization with dataclasses.asdict; reject blank IDs, invalid target kinds/severities, and findings without evidence via ValueError.
- [ ] Run pytest tests/test_requirements.py -q. Expected: PASS.
- [ ] Commit:

    git add packages/qa_agent/requirements.py packages/qa_agent/__init__.py tests/test_requirements.py
    git commit -m "feat: add v0.2 requirement contracts"

### Task 2: Add safe source adapters

**Files:** Create packages/qa_agent/requirement_adapters.py; create tests/test_requirement_adapters.py.

**Interfaces:** RequirementSource(id, title, body, source_kind, source_ref, criterion_lines); MarkdownRequirementAdapter(max_file_bytes).fetch(path); GitHubIssueAdapter(fetcher=None).fetch(identifier, issue_file=None); typed RequirementNotFound, RequirementAccessDenied, RequirementBackendError.

- [ ] Write failing tests for a # Checkout Markdown title and its line-4 Acceptance Criteria list item, plus a local JSON issue with number/title/body/html_url.
- [ ] Run pytest tests/test_requirement_adapters.py -q. Expected: FAIL with missing module.
- [ ] Implement UTF-8 file loading; reject .env, credentials*, secrets*, binaries, and oversized input. Parse the first # heading and direct list items below a case-insensitive ## Acceptance Criteria heading until the next heading. The issue adapter accepts title/body only and never calls network when issue_file is provided.
- [ ] Test malformed JSON, absent fields, injected PermissionError, secret/binary/oversized files.
- [ ] Run pytest tests/test_requirement_adapters.py -q. Expected: PASS.
- [ ] Commit:

    git add packages/qa_agent/requirement_adapters.py tests/test_requirement_adapters.py
    git commit -m "feat: add requirement source adapters"

### Task 3: Add explicit SQLite trace storage

**Files:** Create packages/qa_agent/trace_store.py; create tests/test_trace_store.py.

**Interfaces:** SQLiteTraceStore(path); save_requirement(requirement, evidence); get_requirement(id); replace_links(id, links); get_links(id).

- [ ] Write a failing round-trip test that saves REQ-1, requirement Evidence EV-1, and unverified code TraceLink checkout.py then loads both objects identically.
- [ ] Run pytest tests/test_trace_store.py -q. Expected: FAIL with missing module.
- [ ] Implement requirements and trace_links tables using sqlite3 parameter placeholders and one context manager per operation; JSON-encode tuple fields and source evidence only.
- [ ] Test unknown ID, stale-link replacement, and paths containing quotes.
- [ ] Run pytest tests/test_trace_store.py -q. Expected: PASS.
- [ ] Commit:

    git add packages/qa_agent/trace_store.py tests/test_trace_store.py
    git commit -m "feat: persist requirement trace links"

### Task 4: Implement deterministic analysis and gate

**Files:** Create packages/qa_agent/requirement_analysis.py; create tests/test_requirement_analysis.py.

**Interfaces:** RequirementRequest(source, max_actions=6, max_file_bytes=1000000); RequirementAnalysisService.analyze(request) -> RequirementResult. Ordered actions: parse-requirement, analyze-testability, analyze-risk, verify-and-gate.

- [ ] Write failing tests for Fast checkout and System handles errors. Assert evidenced categories ambiguous, unverifiable, missing_error_path. Add a max_actions=1 case that returns incomplete/BUDGET_EXHAUSTED.
- [ ] Run pytest tests/test_requirement_analysis.py -q. Expected: FAIL with missing service.
- [ ] Implement exact deterministic dictionaries: ambiguous words fast/easy/robust/user-friendly/appropriate; observable words display/return/reject/redirect/status/within/must not/can; error words error/fail/declin/invalid/denied/timeout. Create SHA-256 criterion evidence at the original line. Detect must plus must not for the same normalized subject as conflicting_criteria.
- [ ] Reuse AgentState, ExecutionBudget, LoopTrace, Observer, Evaluator, EvidenceVerifier. Critical risk fails; missing evidence, timeout, and exhausted budget yield incomplete.
- [ ] Run pytest tests/test_requirement_analysis.py -q. Expected: PASS for positive, ambiguity, conflict, missing-error, unavailable-source, and budget cases.
- [ ] Commit:

    git add packages/qa_agent/requirement_analysis.py tests/test_requirement_analysis.py
    git commit -m "feat: analyze requirement testability and risk"

### Task 5: Add bounded mapping and PR composition

**Files:** Create packages/qa_agent/requirement_mapping.py; modify packages/qa_agent/requirement_analysis.py; create tests/test_requirement_mapping.py; modify tests/test_requirement_analysis.py.

**Interfaces:** map_requirement(requirement, evidence_ids, repository, max_files, max_file_bytes) -> list[TraceLink]; RequirementAnalysisService.review_pr(requirement, requirement_evidence, repository, base=None) -> RequirementResult.

- [ ] Write a failing test where Checkout maps to checkout.py as code/unverified/0.2 and where absent requirement evidence makes review_pr incomplete.
- [ ] Run pytest tests/test_requirement_mapping.py tests/test_requirement_analysis.py -q. Expected: FAIL with missing mapper/review_pr.
- [ ] Map normalized title/body tokens only against file stems. Apply the v0.1 ignored directory, secret name, binary, size, and file-count policy. Every link stays unverified at 0.2.
- [ ] Compose ReviewService.review(ReviewRequest(repository, base=base)) without modifying it. Keep its evidence distinct and do not upgrade TraceLinks if review passes.
- [ ] Run pytest tests/test_requirement_mapping.py tests/test_requirement_analysis.py tests/test_review_service.py -q. Expected: PASS including secret/binary skip, no tokens, missing repository, unknown base.
- [ ] Commit:

    git add packages/qa_agent/requirement_mapping.py packages/qa_agent/requirement_analysis.py tests/test_requirement_mapping.py tests/test_requirement_analysis.py
    git commit -m "feat: map requirements to bounded review evidence"

### Task 6: Deliver CLI, reporting, evals, examples, and docs

**Files:** Modify packages/qa_agent/cli.py, packages/qa_agent/evals.py, README.md, README.zh-CN.md, docs/v0.2-engineering/README.md, tests/test_cli.py, tests/test_evals.py. Create packages/qa_agent/requirement_reporting.py, tests/test_requirement_reporting.py, examples/v02-requirement/checkout.md, examples/v02-requirement/github-issue.json, examples/v02-requirement/README.md.

**Interfaces:** analyze-requirement FILE --trace-db PATH; map-coverage --requirement ID --repository PATH --trace-db PATH; review-pr REPOSITORY --requirement ID --trace-db PATH with optional --github-issue-file and --base; qa-agent eval --version v0.2.

- [ ] Write failing CLI tests: omitted --trace-db exits 2 and reports the flag; successful analysis persists then map-coverage emits status unverified. Add a v0.2 eval test requiring positive, negative, ambiguous, conflicting, unverifiable, adversarial cases.
- [ ] Run pytest tests/test_cli.py tests/test_evals.py tests/test_requirement_reporting.py -q. Expected: FAIL because v0.2 interfaces are absent.
- [ ] Implement argparse handlers. Persist after analysis. Load Markdown from storage or an issue through --github-issue-file. JSON delegates to RequirementResult.to_dict; human output includes decision, termination, counts, Unverified trace links, and Risk: unknown for incomplete. Exit codes: pass/warn=0, fail=1, incomplete=2.
- [ ] Add six fixed, in-memory, no-network eval cases. Add a title/body-only issue JSON. Add exact command documentation in English README and equivalent Chinese navigation; commands, identifiers, and paths stay unchanged.
- [ ] Run pytest -q. Expected: PASS.
- [ ] Run qa-agent eval. Expected: 155 v0.1 cases and precision/recall 1.0.
- [ ] Run qa-agent eval --version v0.2. Expected: six cases, no failures.
- [ ] Run git diff --check. Expected: no output.
- [ ] Commit:

    git add packages/qa_agent/cli.py packages/qa_agent/evals.py packages/qa_agent/requirement_reporting.py examples/v02-requirement README.md README.zh-CN.md docs/v0.2-engineering/README.md tests/test_cli.py tests/test_evals.py tests/test_requirement_reporting.py
    git commit -m "feat: add requirement intelligence CLI and evals"

## Final verification

- [ ] Re-run every command above, then run both examples with an explicit temporary trace database.
- [ ] Run git status --short --branch; preserve unrelated changes and report actual outcomes only.
