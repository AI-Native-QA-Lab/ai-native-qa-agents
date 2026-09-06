# v0.1 Implementation Plan

## 1. Milestone

```text
v0.1.0 — Evidence-driven PR Quality Reviewer
```

## 2. Definition of Success

真实项目运行：

```bash
qa-agent review --base main
```

能够：

1. 识别项目语言与测试框架
2. 分析 Git Diff
3. 发现 pytest / Playwright 测试
4. 执行至少 10 条高质量静态规则
5. 可选调用 AI 做语义 Review
6. 生成 Evidence-backed Findings
7. 应用 Quality Gate
8. 输出 Human / JSON / SARIF
9. 在 GitHub Action 中运行
10. 通过 Eval Dataset 验证 False Positive

## 3. 推荐技术栈

Core:

```text
Python 3.11+
```

Package:

```text
uv / hatch / poetry 三选一
```

建议优先：

```text
uv
```

CLI:

```text
Typer
```

Schema:

```text
Pydantic v2
```

Git:

```text
GitPython 或 subprocess git
```

建议：

```text
subprocess git
```

减少额外抽象。

AST:

```text
Python ast
tree-sitter
```

Report:

```text
Rich
JSON
SARIF
```

Tests:

```text
pytest
```

Lint:

```text
ruff
```

Typing:

```text
mypy 或 pyright
```

## 4. Phase 1 — Foundation

目标：

```text
可运行 CLI + 稳定 Domain Model
```

Tasks:

- 初始化仓库
- pyproject.toml
- CLI skeleton
- Config loader
- Evidence model
- Finding model
- ReviewResult
- GateResult
- JSON serialization
- Logging

DoD:

```bash
qa-agent --help
qa-agent config show
```

通过。

## 5. Phase 2 — Repository Intelligence

实现：

- Git repository detection
- Base branch resolution
- git diff
- changed file classification
- source/test file detection
- project language detection

输出：

```bash
qa-agent detect
```

示例：

```text
Languages:
- Python
- TypeScript

Frameworks:
- pytest
- Playwright
```

## 6. Phase 3 — Test Adapters

PytestAdapter：

- discover test file
- discover test function
- assertion extraction
- fixture detection
- mock extraction
- skip / xfail detection

PlaywrightAdapter：

- discover spec
- discover test()
- expect extraction
- locator / action extraction
- skip detection
- page.waitForTimeout detection

DoD:

给定 fixtures，能生成统一 TestEntity。

## 7. Phase 4 — Rule Engine

实现：

```text
RuleRegistry
RuleContext
RuleRunner
FindingFactory
```

首批至少：

```text
TQ001
TQ002
TQ003
TQ005
TQ006
TQ010
TQ011
TQ012
TQ014
TQ015
```

推荐争取完成全部 15 条。

## 8. Phase 5 — Diff & Relevance

实现：

```text
CodeChange
RelatedTestCandidate
RelevanceScore
```

第一版评分：

```text
import reference: +0.5
symbol match: +0.3
filename similarity: +0.2
```

Git co-change 可推迟。

输出：

```text
Changed code without likely related tests
```

必须标记：

```text
confidence
```

避免作为绝对事实。

## 9. Phase 6 — Semantic Reviewer

ContextBuilder 只提供：

```text
test source
nearby production symbol
rule signals
diff context
```

不提供整个 repo。

SemanticReview 输出：

```yaml
intent:
  ...

oracle_quality:
  strong|medium|weak

issues:
  - ...

confidence:
  0.84

verification_status:
  partially_verified
```

AI Finding 必须带：

```text
source = semantic-reviewer
```

## 10. Phase 7 — Gate Engine

默认：

```yaml
gates:
  fail_on:
    - critical
```

可配置：

```yaml
gates:
  fail_on:
    - critical
    - high
```

Gate 不能只看数量，还要保留 Findings。

## 11. Phase 8 — Reporting

Human：

```text
Summary
Risk
Changed Files
Findings
Evidence
Recommendation
```

JSON：

机器可读完整结果。

SARIF：

用于 GitHub Code Scanning。

## 12. Phase 9 — Evals

Dataset：

```text
evals/test_quality/
  python/
  playwright/
```

场景：

- good
- fake
- weak
- ambiguous
- adversarial

最低：

```text
80 cases
```

目标：

Deterministic Rule：

```text
Precision >= 95%
```

Semantic Review：

```text
Precision >= 80%
False Positive <= 15%
```

这些是初始工程目标，不是永久 SLA。

## 13. Phase 10 — GitHub Action

输入：

```yaml
with:
  base: main
  format: sarif
```

输出：

- job summary
- optional PR summary comment
- SARIF upload
- exit code

默认避免：

```text
per-line AI comment spam
```

## 14. Phase 11 — Security

必须：

- redact `.env`
- redact obvious secret patterns
- ignore binary
- file size limit
- max context size
- malicious prompt text treated as source data
- fork PR 不读取 protected secret

## 15. Phase 12 — Release

Release checklist：

```text
unit tests
adapter contract tests
rule evals
semantic evals
CLI smoke
GitHub Action smoke
docs
examples
```

Tag：

```text
v0.1.0
```

## 16. 8 周计划

### Week 1
Foundation

### Week 2
Repository Scanner + Detection

### Week 3
pytest + Playwright Adapter

### Week 4
Rule Engine + first rules

### Week 5
Diff + Test Relevance

### Week 6
Semantic Reviewer + Gate

### Week 7
Evals + False Positive reduction

### Week 8
SARIF + GitHub Action + Docs + Release

## 17. v0.1 Non-goals

明确不做：

```text
test generation
test execution orchestration
mutation
Jira
failure investigation
release decision
multi-agent
knowledge graph
web dashboard
```

## 18. v0.2 Compatibility

v0.1 预留：

```text
Evidence.type
Finding.subject
Backend protocol location
Adapter Registry
ReviewContext
```

为 Requirement Intelligence 接入做准备。

但不要提前实现 RequirementBackend。

---

## Agent Loop Implementation Workstream

v0.1 must implement a minimal bounded runtime in parallel with the reviewer.

### Runtime Models

- AgentState
- Observation
- LoopTrace
- ExecutionBudget
- TerminationReason

### Runtime Services

- ReviewPlanner
- ActionExecutor
- Observer
- Evaluator
- EvidenceVerifier
- TerminationPolicy

### Default v0.1 Loop

```text
detect
→ diff
→ discover tests
→ rules
→ optional semantic review
→ verify findings
→ gate
→ stop
```

The planner is deterministic. Re-plan means choosing another predefined review action, not arbitrary LLM autonomy.

### Additional Definition of Done

- every review has a LoopTrace
- max iteration/tool/model budgets are enforced
- budget exhaustion is visible in ReviewResult
- semantic review cannot bypass evidence verification
- `INSUFFICIENT_EVIDENCE` is supported
