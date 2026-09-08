# v0.2 收尾与 v0.3 AI 测试工程师 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 先完成可审计的 v0.2 Requirement Intelligence，再交付默认离线、补丁受限、隔离执行的 v0.3 AI Test Engineer。

**Architecture:** v0.2 在 `Requirement`、`Evidence` 与显式 SQLite trace store 上完成分析、映射和需求感知审查。v0.3 新增测试工程领域模型、受限补丁校验、执行后端和门禁编排；生成、执行和修复均可追踪，且绝不写入用户仓库。

**Tech Stack:** Python 3.10+、标准库、pytest、SQLite、argparse、subprocess。

**Spec:** `docs/superpowers/specs/2026-09-07-v02-closeout-v03-test-engineer-design.md`

## Global Constraints

- README 英文主写，保留 `README.zh-CN.md` 切换；新增工程设计、开发和计划文档以中文主写。
- 需求、Issue、补丁与测试输出均不可信；没有证据时必须返回 `INSUFFICIENT_EVIDENCE`。
- 状态型 v0.2 命令必须显式传递 `--trace-db`；追踪链接默认为 `unverified`。
- v0.3 仅处理测试路径的补丁，禁止生产文件变更、自动应用、自动提交、联网和依赖下载。
- 所有循环受文件、时间、工具、模型、执行和修复预算限制。

---

### Task 1: 完成 v0.2 冲突分析与终止契约

**Files:** Modify `packages/qa_agent/requirement_analysis.py`, `packages/qa_agent/evals.py`, `tests/test_requirement_analysis.py`.

**Interfaces:** `RequirementAnalysisService.analyze(request) -> RequirementResult` 产出有 Evidence ID 的 `conflicting_criteria` finding/risk；预算不足时返回 `BUDGET_EXHAUSTED`。

- [ ] **Step 1: 写失败测试**

```python
def test_analysis_reports_evidenced_conflicting_criteria() -> None:
    source = RequirementSource("REQ-1", "Orders", "", "markdown", "req.md", (
        (2, "User must save the order"), (3, "User must not save the order"),
    ))
    result = RequirementAnalysisService().analyze(RequirementRequest(source))
    assert any(item.category == "conflicting_criteria" for item in result.findings)
    assert all(item.evidence_ids for item in result.findings)
```

- [ ] **Step 2: 验证 RED**

Run: `pytest tests/test_requirement_analysis.py::test_analysis_reports_evidenced_conflicting_criteria -q`

Expected: FAIL，因为尚未检测冲突。

- [ ] **Step 3: 最小实现**

```python
_NEGATED = re.compile(r"\bmust not\s+(.+)", re.I)
# 在每个否定条件中寻找同一规范化动作的肯定条件，
# 为一对条件添加 evidenced TestabilityFinding 和 RiskItem。
```

- [ ] **Step 4: 验证 GREEN**

Run: `pytest tests/test_requirement_analysis.py tests/test_evals.py -q`

Expected: PASS；冲突评测期望 `conflicting_criteria`。

- [ ] **Step 5: 提交**

```bash
git add packages/qa_agent/requirement_analysis.py packages/qa_agent/evals.py tests/test_requirement_analysis.py
git commit -m "feat: complete v0.2 conflict analysis"
```

### Task 2: 完成 v0.2 映射、审查组合和报告

**Files:** Modify `packages/qa_agent/requirement_mapping.py`, `packages/qa_agent/requirement_analysis.py`, `packages/qa_agent/reporting.py`, `packages/qa_agent/cli.py`, `tests/test_requirement_mapping.py`, `tests/test_requirement_analysis.py`, `tests/test_requirement_cli.py`.

**Interfaces:** `review_pr(requirement, evidence, repository, base) -> RequirementResult` 必须保留需求/审查证据、gate、trace 与 budget；新增 `render_requirement_human(result) -> str`。

- [ ] **Step 1: 写失败测试**

```python
def test_requirement_review_keeps_requirement_and_review_evidence(tmp_path: Path) -> None:
    requirement = Requirement("REQ-1", "Checkout", "", "markdown", "req.md")
    evidence = [Evidence("EV-REQ-001", "requirement", "req.md", 1, 1, "sha256:x")]
    (tmp_path / "test_empty.py").write_text("def test_empty():\n    pass\n")
    result = RequirementAnalysisService().review_pr(requirement, evidence, tmp_path)
    assert "EV-REQ-001" in {item.id for item in result.evidence}
    assert result.gate is not None
```

- [ ] **Step 2: 验证 RED**

Run: `pytest tests/test_requirement_analysis.py::test_requirement_review_keeps_requirement_and_review_evidence -q`

Expected: FAIL，因为 v0.2 组合结果未完整传递 gate。

- [ ] **Step 3: 最小实现**

```python
result.gate = review.gate
result.loop_trace = review.loop_trace
result.budget = review.budget

def render_requirement_human(result: RequirementResult) -> str:
    return f"Decision: {result.decision}\nTermination: {result.termination_reason}\nEvidence: {len(result.evidence)}"
```

缺少 requirement/evidence 必须输出结构化不足证据并 exit 2；保留映射限制和 `unverified` 状态。

- [ ] **Step 4: 验证 GREEN**

Run: `pytest tests/test_requirement_mapping.py tests/test_requirement_analysis.py tests/test_requirement_cli.py tests/test_trace_store.py -q`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add packages/qa_agent/requirement_mapping.py packages/qa_agent/requirement_analysis.py packages/qa_agent/reporting.py packages/qa_agent/cli.py tests/test_requirement_mapping.py tests/test_requirement_analysis.py tests/test_requirement_cli.py
git commit -m "feat: complete v0.2 requirement workflow"
```

### Task 3: 固化 v0.2 离线评测与中文工程文档

**Files:** Modify `packages/qa_agent/evals.py`, `tests/test_evals.py`, `docs/README.md`, `docs/v0.2-engineering/*.md`, `ROADMAP_AND_VERSION_DESIGN.md`, `MASTER_IMPLEMENTATION_ROADMAP.md`.

**Interfaces:** `qa-agent eval --version v0.2` 覆盖正例、负例、歧义、缺失错误路径、冲突、不可验证、恶意文本、坏映射/预算边界。

- [ ] **Step 1: 写失败测试**

```python
def test_v02_eval_catalog_covers_required_requirement_cases() -> None:
    total, failures = run_v02_evals()
    assert total >= 8
    assert failures == []
```

- [ ] **Step 2: 验证 RED**

Run: `pytest tests/test_evals.py::test_v02_eval_catalog_covers_required_requirement_cases -q`

Expected: FAIL，当前 catalog 只有六条用例。

- [ ] **Step 3: 最小实现**

添加 budget、malicious issue 和坏映射边界用例；将 `docs/README.md` 与 v0.2 工程包中文化，命令、标识符、路径和 schema 名称保持原文。

- [ ] **Step 4: 验证 v0.2 完整门禁**

Run: `pytest -q && qa-agent eval && qa-agent eval --version v0.2 && git diff --check`

Expected: 全部 exit 0。

- [ ] **Step 5: 提交**

```bash
git add docs ROADMAP_AND_VERSION_DESIGN.md MASTER_IMPLEMENTATION_ROADMAP.md packages/qa_agent/evals.py tests/test_evals.py
git commit -m "docs: complete Chinese v0.2 engineering documentation"
```

### Task 4: 新增 v0.3 测试工程领域契约

**Files:** Create `packages/qa_agent/test_engineering.py`, `tests/test_test_engineering.py`; modify `packages/qa_agent/__init__.py`.

**Interfaces:** `TestIntent`、`TestPlan`、`TestScenario`、`GeneratedPatch`、`ExecutionResult`、`RepairAttempt`、`TestCandidateStatus` 与 `TestEngineeringResult.to_dict()`，输出 `schema_version == "v0.3"`。

- [ ] **Step 1: 写失败测试**

```python
def test_v03_result_serializes_evidenced_candidate() -> None:
    result = TestEngineeringResult(
        intent=TestIntent("TI-1", "REQ-1", "checkout", ("EV-REQ-001",)),
        status=TestCandidateStatus("rejected", "INSUFFICIENT_EVIDENCE", ("EV-REQ-001",)),
    )
    assert result.to_dict()["schema_version"] == "v0.3"
```

- [ ] **Step 2: 验证 RED**

Run: `pytest tests/test_test_engineering.py::test_v03_result_serializes_evidenced_candidate -q`

Expected: FAIL with `ModuleNotFoundError`。

- [ ] **Step 3: 最小实现**

```python
@dataclass(frozen=True)
class GeneratedPatch:
    id: str
    files: tuple[PatchFile, ...]
    evidence_ids: tuple[str, ...]
    def __post_init__(self) -> None:
        if not self.files or not self.evidence_ids:
            raise ValueError("patch files and evidence are required")
```

- [ ] **Step 4: 验证 GREEN**

Run: `pytest tests/test_test_engineering.py -q`

Expected: PASS。

### Task 5: 实现补丁安全校验与隔离 pytest 执行器

**Files:** Create `packages/qa_agent/execution.py`, `tests/test_execution.py`.

**Interfaces:** `validate_patch(patch, test_roots) -> None` 与 `PytestExecutionBackend.execute(repository, patch, timeout_seconds) -> ExecutionResult`。

- [ ] **Step 1: 写失败测试**

```python
@pytest.mark.parametrize("path", ("src/orders.py", "../test_escape.py", "/tmp/test_escape.py"))
def test_patch_validator_rejects_unsafe_paths(path: str) -> None:
    patch = GeneratedPatch("GP-1", (PatchFile(path, "def test_x():\n    assert True\n"),), ("EV-1",))
    with pytest.raises(PatchSafetyError):
        validate_patch(patch, ("tests",))
```

- [ ] **Step 2: 验证 RED**

Run: `pytest tests/test_execution.py::test_patch_validator_rejects_unsafe_paths -q`

Expected: FAIL with `ModuleNotFoundError`。

- [ ] **Step 3: 最小实现**

```python
with tempfile.TemporaryDirectory() as work:
    sandbox = Path(work) / "repository"
    shutil.copytree(repository, sandbox, ignore=_ignore_untrusted)
    _apply_test_only_patch(sandbox, patch, test_roots)
    completed = subprocess.run((sys.executable, "-m", "pytest"), cwd=sandbox,
                               text=True, capture_output=True, timeout=timeout_seconds)
```

记录退出码、stdout/stderr 摘要、耗时和超时；绝不改动原 `repository`。

- [ ] **Step 4: 验证 GREEN**

Run: `pytest tests/test_execution.py -q`

Expected: PASS，覆盖成功、失败、超时和原仓库未改动。

### Task 6: 实现 v0.3 生成、门禁和修复循环

**Files:** Create `packages/qa_agent/test_generation.py`, `packages/qa_agent/test_engineering_service.py`, `tests/test_test_generation.py`, `tests/test_test_engineering_service.py`.

**Interfaces:** `TestGenerator.generate(plan) -> GeneratedPatch` 与 `TestEngineeringService.run(request) -> TestEngineeringResult`；输入包含已持久化的 v0.2 requirement/evidence、执行后端与 `max_repairs`。

- [ ] **Step 1: 写失败测试**

```python
def test_service_is_incomplete_without_explicit_generator(tmp_path: Path) -> None:
    result = TestEngineeringService().run(TestEngineeringRequest("REQ-1", tmp_path))
    assert (result.status.decision, result.status.termination_reason) == ("incomplete", "INSUFFICIENT_EVIDENCE")

def test_service_stops_after_configured_repairs(tmp_path: Path) -> None:
    result = TestEngineeringService(generator=AlwaysFailingGenerator()).run(
        TestEngineeringRequest("REQ-1", tmp_path, max_repairs=1))
    assert result.status.termination_reason == "BUDGET_EXHAUSTED"
```

- [ ] **Step 2: 验证 RED**

Run: `pytest tests/test_test_engineering_service.py -q`

Expected: FAIL with `ModuleNotFoundError`。

- [ ] **Step 3: 最小实现**

```python
if generator is None or not requirement_evidence:
    return _incomplete("INSUFFICIENT_EVIDENCE")
patch = generator.generate(plan)
validate_patch(patch, request.test_roots)
execution = backend.execute(request.repository, patch, request.timeout_seconds)
return _rejected_or_retry(execution) if not execution.passed else _review_and_accept(patch, execution)
```

Parse、Compile、Execution、Assertion、Reviewer 都产出 gate evidence；修复只能替换当前测试补丁。

- [ ] **Step 4: 验证 GREEN**

Run: `pytest tests/test_test_generation.py tests/test_test_engineering_service.py -q`

Expected: PASS。

### Task 7: 添加 Playwright 检测、CLI、评测和中文文档验收

**Files:** Modify `packages/qa_agent/execution.py`, `packages/qa_agent/cli.py`, `packages/qa_agent/evals.py`, `tests/test_execution.py`, `tests/test_cli.py`, `tests/test_evals.py`; create `tests/test_documentation_contracts.py`; modify `docs/v0.3-engineering/*.md`, `docs/README.md`, `README.md`, `README.zh-CN.md`, `pyproject.toml`.

**Interfaces:** `qa-agent engineer-test --requirement --repository --trace-db --generator-file --framework {pytest,playwright}`；`qa-agent eval --version v0.3`。

- [ ] **Step 1: 写失败测试**

```python
def test_playwright_backend_reports_unavailable_without_installing(tmp_path: Path) -> None:
    result = PlaywrightExecutionBackend(executable="does-not-exist").execute(tmp_path, valid_patch(), 1)
    assert result.termination_reason == "INSUFFICIENT_EVIDENCE"
    assert result.command == ()

def test_v03_docs_describe_patch_only_and_no_auto_commit() -> None:
    security = Path("docs/v0.3-engineering/SECURITY.md").read_text()
    assert "Patch-only" in security and "no auto-commit" in security
```

- [ ] **Step 2: 验证 RED**

Run: `pytest tests/test_execution.py::test_playwright_backend_reports_unavailable_without_installing tests/test_documentation_contracts.py -q`

Expected: FAIL，适配器与同步文档尚不存在。

- [ ] **Step 3: 最小实现**

```python
engineer = commands.add_parser("engineer-test", help="Generate and validate a test candidate")
engineer.add_argument("--requirement", required=True)
engineer.add_argument("--repository", required=True, type=Path)
engineer.add_argument("--trace-db", required=True, type=Path)
engineer.add_argument("--generator-file", required=True, type=Path)
engineer.add_argument("--framework", choices=("pytest", "playwright"), default="pytest")
```

Playwright 不可用时不安装内容。生成器只读受限本地 JSON fixture。将 v0.3 工程包中文化，README 保持英文主写/中文切换，且仅在全部门禁通过后更新版本元数据。

- [ ] **Step 4: 完整验收**

Run: `pytest -q && qa-agent eval && qa-agent eval --version v0.2 && qa-agent eval --version v0.3 && python3 -m compileall -q packages && git diff --check`

Expected: 每条命令 exit 0。

- [ ] **Step 5: 范围审计后提交**

```bash
git diff --cached --name-only
git diff --cached --stat
git add docs README.md README.zh-CN.md pyproject.toml packages tests
git commit -m "feat: complete v0.3 AI test engineer"
```

## 自检结果

- Spec coverage: Tasks 1–3 覆盖 v0.2 的分析、工作流、评测、文档和完整门禁；Tasks 4–7 覆盖 v0.3 契约、补丁安全、执行、重试、CLI、评测、文档和验收。
- Placeholder scan: 无 `TBD`、`TODO` 或“类似前一任务”占位。
- Interface consistency: 契约先于执行器，执行器先于循环，循环先于 CLI/评测，文档在已验证的外部行为基础上更新。

