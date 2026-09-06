# AI Native QA Agents — v0.1 Architecture

## 1. 目标

v0.1 只解决一个核心问题：

> 对真实代码仓库中的测试进行证据驱动的质量审查，并结合 Git Diff 识别潜在测试缺口。

v0.1 不是测试生成器，也不是 Multi-Agent 平台。

## 2. 范围

支持：

- Local Git Repository
- Python + pytest
- TypeScript + Playwright
- Git Diff 分析
- Test Discovery
- Deterministic Rule Engine
- Optional LLM Semantic Review
- Evidence-backed Findings
- Quality Gates
- Human / JSON / SARIF 输出
- GitHub Action

暂不支持：

- Requirement Backend
- Test Generation
- Mutation Testing
- Failure Investigation
- Release Decision
- Production Observability
- Multi-Agent Runtime
- Knowledge Graph

## 3. 架构原则

### 3.1 Deterministic First

AST、Git Diff、测试发现、规则匹配优先使用确定性逻辑。LLM 只处理语义判断。

### 3.2 Evidence First

所有 Finding 尽量关联 Evidence。无 Evidence 的 AI 判断必须标记为 `unverified`。

### 3.3 Adapter First

Agent Core 不绑定 pytest、Playwright 或 GitHub。

### 3.4 AI Optional

关闭 AI 后，v0.1 仍必须可以完成基础审查。

## 4. 组件图

```text
CLI / GitHub Action
        │
        ▼
Review Application Service
        │
        ├── Repository Scanner
        ├── Diff Analyzer
        ├── Project Detector
        ├── Test Framework Adapter
        ├── Rule Engine
        ├── Semantic Reviewer (optional)
        ├── Evidence Builder
        ├── Finding Aggregator
        ├── Quality Gate Engine
        └── Report Renderer
```

## 5. 推荐目录

```text
ai-native-qa-agents/
├── pyproject.toml
├── README.md
├── README.zh-CN.md
├── packages/
│   ├── qa_common/
│   │   ├── models/
│   │   ├── evidence/
│   │   ├── findings/
│   │   ├── gates/
│   │   └── config/
│   ├── qa_core/
│   │   ├── review/
│   │   ├── repository/
│   │   ├── diff/
│   │   ├── detection/
│   │   └── reporting/
│   └── qa_cli/
├── adapters/
│   ├── languages/
│   │   ├── python/
│   │   └── typescript/
│   ├── testing/
│   │   ├── pytest/
│   │   └── playwright/
│   └── ai/
│       ├── anthropic/
│       └── openai/
├── rules/
│   └── test_quality/
├── evals/
│   └── test_quality/
├── integrations/
│   └── github_action/
├── examples/
└── tests/
```

## 6. 核心流程

```text
Repository
   │
   ▼
Detect Project
   │
   ▼
Read Git Diff
   │
   ▼
Discover Tests
   │
   ▼
Parse Tests
   │
   ├── Rule Engine
   │
   └── Semantic Reviewer
   │
   ▼
Build Evidence
   │
   ▼
Generate Findings
   │
   ▼
Aggregate Risk
   │
   ▼
Apply Quality Gate
   │
   ▼
Render Report
```

## 7. Application Service

建议定义单一入口：

```python
class ReviewService:
    def review(self, request: ReviewRequest) -> ReviewResult:
        ...
```

v0.1 不需要复杂 Agent Orchestrator。

## 8. 数据模型

核心模型：

- Evidence
- Finding
- ReviewRequest
- ReviewResult
- TestEntity
- CodeChange
- QualityDecision
- GateResult

使用 Pydantic 建模。

## 9. AI Boundary

LLM 可以判断：

- assertion 是否真正验证业务行为
- 测试是否只验证实现细节
- 测试 intent
- 潜在遗漏行为
- Finding 的解释

LLM 不可以凭空声明：

- 测试已执行
- 测试已通过
- 覆盖率数值
- Mutation Score
- 某 Requirement 已覆盖

这些必须由 Tool / Evidence 提供。

## 10. Security Boundary

Repository 内容始终视为不可信数据。

必须包含：

- Prompt Injection 隔离
- Secret Redaction
- Context Size Limit
- File Allow/Deny Rules
- AI Provider 输入过滤
- GitHub Fork PR Secret Protection

## 11. v0.1 Architecture Decision Records

建议首批 ADR：

- ADR-001 Python 作为 Core 实现语言
- ADR-002 Pydantic 作为 Domain Schema
- ADR-003 Tree-sitter 用于多语言结构解析
- ADR-004 Rule Engine 与 LLM Reviewer 分离
- ADR-005 SARIF 作为 CI 标准输出之一
- ADR-006 AI Provider 可选且可插拔

---

## Agent Runtime

v0.1 changes `ReviewService` from a simple linear pipeline into a bounded review loop.

```text
ReviewRequest
   ↓
AgentState
   ↓
Deterministic Plan
   ↓
Action
   ↓
Observation
   ↓
Evidence
   ↓
Evaluate
   ↓
Need more predefined evidence?
 ├── yes → next review action
 └── no  → Verify → Gate → ReviewResult
```

Required v0.1 runtime components:

- AgentState
- Observation
- LoopTrace
- ExecutionBudget
- TerminationPolicy
- deterministic ReviewPlanner
- EvidenceVerifier

No unrestricted LLM planner is included in v0.1.
