# v0.4 Test Effectiveness & Mutation Design

## 目标与调整后的定位

v0.4 不定义为“接入 Mutation 工具”，而定义为 **Test Effectiveness**
闭环。它要回答：

```text
Test Exists ≠ Test Works
```

Mutation 是重要的 Evidence Provider，但不是产品边界。一个有效性结论必须
能够回溯到 Requirement、Acceptance Criterion、Risk、Observable Behavior、
Test Intent、Test Scenario 和 Business Oracle。

本设计同时吸收 v0.3 复盘结论：

1. v0.4 的第一阶段先增强 v0.3 的测试语义契约，并提供可重复的真实项目验证
   入口；不把 fixture/golden eval 当成真实项目证据。
2. 首个可执行切片采用 Python 优先和 engine-agnostic offline mutation report。
   PIT、Stryker 先实现能力检测、typed errors、fixtures 和 contract tests，
   不宣称已经完成 Java 或 TypeScript 的真实 Mutation 执行。
3. 不新增复杂的 multi-agent orchestrator，不把 Model Runtime 变成循环控制器，
   也不为不同 provider 逐个堆叠 adapter。

本设计不要求额外发布一个 v0.3.x 版本。v0.3 语义增强作为 v0.4 的入口阶段
落地；真实项目 benchmark、误报控制和 Mutation 证据是 v0.4 收尾与发布前的
独立验收项。

## 范围与非目标

### 本版本范围

- Acceptance Criterion、Risk、Observable Behavior、Business Oracle 与
  `TestIntent`/`TestScenario` 的显式关联。
- `MutationRun`、`Mutant`、`MutationResult`、`MutationTraceLink`、
  `EffectivenessScore`、`FakeTestSignal` 和
  `TestEffectivenessAssessment` 的版本化契约。
- 离线 mutation report 的严格解析、校验、归一化和 Evidence 生成。
- `MutationBackend` 协议、Python capability detection，以及 mutmut 的
  受控执行边界。
- PIT/Stryker 的 capability detection、typed errors、离线 fixtures 和
  adapter contract tests。
- survivor 到 Requirement/Test Intent/Scenario/Business Oracle 的确定性映射。
- Execution、Assertion、Requirement Relevance、Mutation 四类有效性信号的
  组合评估；模型信号只能作为标明来源的可选补充。
- SQLite trace store、JSON/human CLI、v0.4 eval 和可重复参考项目。
- 真实项目验证 harness；验证结果必须带 repository revision、输入 artifact、
  命令、输出和限制说明。

### 非目标

- 支持所有语言、所有 Mutation 引擎或自动下载外部依赖。
- 用 LLM 输出单一的 `fake_probability`。
- 自动接受、应用、提交、合并或发布生成的测试/补丁。
- 修改生产代码或用户原始工作树。
- 无边界的模型循环、自动 multi-agent 编排或 provider-specific 业务逻辑。
- 把 coverage percentage、测试数量或模型 confidence 当成测试有效性证明。

## 总体架构与数据流

```text
Requirement + Evidence
        ↓
Acceptance Criterion + Risk
        ↓
Observable Behavior + Business Oracle
        ↓
Test Intent + Test Scenario
        ↓
Bounded Test Selection
        ↓
MutationBackend
        ↓
MutationRun / Mutant / MutationResult
        ↓
Survivor Mapping
        ↓
EffectivenessScore + FakeTestSignal
        ↓
Evidence Verification
        ↓
Mutation Gate
        ↓
Decision / Termination
```

Agent Runtime 是控制面，拥有 action 顺序、权限、预算、Observation、
`LoopTrace`、Evidence verification、重规划和终止。Backend 只负责执行或
解析外部 Mutation 系统。Model Runtime 只处理显式的语义 mapping/reasoning
任务，不能修改 `AgentState`、Evidence truth、权限或终止状态。

首个纵向切片的默认路径完全确定性：读取已持久化的 Requirement/Evidence，
解析离线报告，生成规范化结果，做 survivor mapping，计算 score，验证引用，
再运行 Mutation Gate。没有必要的语义字段、mutation 结果或映射证据时，
结果必须保留为 `INSUFFICIENT_EVIDENCE`。

## 领域契约

### v0.3 语义增强

`TestIntent` 保留现有字段并增加：

- `acceptance_criterion_ids: tuple[str, ...]`
- `risk_ids: tuple[str, ...]`
- `observable_behavior: str | None`
- `business_oracle: str | None`

`TestScenario` 增加 `business_oracle: str | None` 和
`acceptance_criterion_ids: tuple[str, ...]`。为兼容已持久化的 v0.3 结果，
新增字段在旧输入中可以为空；但 v0.4 effectiveness assessment 将空的
`observable_behavior`、`business_oracle` 或必要的 criterion 关联视为证据
不足，不会用 `requirement_id`、`"test passes"` 等占位文本补齐。

### Mutation 模型

`MutationRun` 至少包含：run id、backend、repository revision、target paths、
selected test paths、run status、termination reason、mutant ids 和
Evidence IDs。

`Mutant` 至少包含：mutant id、repository-relative path、positive line number、
operator、original text、mutated text、normalized status 和 Evidence IDs。

`MutationResult` 至少包含：mutant id、outcome、killing test ids、duration、
stdout/stderr content hashes 和 Evidence IDs。`outcome` 只允许：

```text
killed | survived | timeout | error | not_run
```

`MutationTraceLink` 至少包含：mutant id、requirement id、intent id、scenario
id、business oracle、mapping status 和 Evidence IDs。mapping status 允许
`verified`、`unverified`、`unmapped`；确定性路径默认只能产生 `unverified`
或 `unmapped`，不能把路径名相似性升级为 verified。

`EffectivenessScore` 至少包含：eligible mutants、killed mutants、survived
mutants、score、score status 和 Evidence IDs。只有 `killed` 与 `survived`
属于 eligible denominator；`timeout`、`error` 和 `not_run` 必须单独保留，
不能静默计为 killed 或 survived。

`FakeTestSignal` 至少包含：signal kind、severity、message、source、
verification status 和 Evidence IDs。首个切片支持静态断言信号、执行信号、
Requirement relevance 信号、Oracle 缺失信号和 Mutation survivor 信号；每条
信号必须能解释触发原因。

`TestEffectivenessAssessment` 至少包含：requirement id、MutationRun、
EffectivenessScore、survivor links、fake-test signals、decision、termination
reason、Mutation Gate、Evidence IDs、LoopTrace 和 ExecutionBudget。

所有模型使用稳定的 v0.4 schema marker。稳定 id 由输入 artifact 的内容 hash
和领域对象标识派生；输出排序按稳定 id/path/line 排序，确保相同输入产生相同
的 score、mapping 和 decision。时间戳只用于 provenance，不参与评分。

## Backend 与 Adapter 边界

`MutationBackend` 提供两个独立能力：

1. `detect(repository) -> BackendCapability`：报告是否安装、版本、支持的
   语言/framework、不可用原因和风险限制。
2. `run(request) -> MutationRun`：在受控副本中执行，或把外部报告转换成统一
   的 Mutation 结果。

Backend 不决定选哪些测试、不做重规划、不计算质量门、不调用模型，也不写入
  原始工作树。

offline adapter 接受 version `1` 的 engine-agnostic JSON。报告只作为输入数据
解析，任何字段类似 shell command、prompt 或 instruction 的内容都不会执行。
必须校验：顶层对象、schema version、backend、mutant 数组、path 边界、line、
outcome、数组大小、字符串大小和 JSON 总大小。重复 mutant id、未知 outcome、
非法路径、缺少必要字段和 malformed JSON 返回 typed invalid-input error，不能
产生部分成功的通过结论。

mutmut adapter 是首个真实执行后端。它通过显式 allowlist、临时副本、超时、
资源预算和只读源代码边界运行，并将不可用、执行失败和部分结果分别归一化。
PIT/Stryker adapter 在本阶段至少提供 capability result、typed unavailable/
unsupported/configuration errors、固定 fixtures 和协议测试；未实际执行时
返回 `INSUFFICIENT_EVIDENCE`。

## 有效性评估与 Gate

评分定义为：

```text
score = killed_mutants / (killed_mutants + survived_mutants)
```

分母为零时 `score = None`，`score_status = not_computable`。threshold 是
调用方显式提供的 Mutation Gate policy，不把一个没有项目背景的全局数字伪装
成普适事实；缺少 threshold 时，assessment 可以报告计算结果，但 Gate 不得
给出 `pass`。

Mutation Gate 的决策规则：

- `pass`：score 可计算、达到显式 threshold、关键 survivor 已有 verified 或
  可审计的 unverified mapping，且不存在高严重度 fake-test signal。
- `warn`：score 可计算但存在低风险 survivor、unverified/unmapped mapping 或
  低严重度信号。
- `fail`：score 未达到 threshold，或存在高影响且已验证的 survivor/信号。
- `incomplete`：没有可验证结果、分母为零、关键 Oracle/Requirement evidence
  缺失、backend 不可用、执行超时或输入无法解释。

结论状态与终止原因分离。assessment 的 `decision` 不能覆盖
`termination_reason`；任何关键证据缺失必须保留 `INSUFFICIENT_EVIDENCE`。
模型 confidence 只能附着在模型信号上，不能改变上述规则。

## Agent Loop 与重规划

循环固定为：

```text
UNDERSTAND → SELECT → MUTATE → OBSERVE → MAP → EVALUATE → VERIFY → GATE
                                                                  ↓
                                                              DECIDE/STOP
```

每个动作都先生成 Observation，再产生 Evidence。只有以下情况允许一次受限
重规划：backend capability/configuration 可恢复、存在可定位但未映射的 survivor、
测试选择范围明确不足且预算允许补充证据，或 schema-valid 的语义 mapping
确实能消除不确定性。每次重规划写入 `LoopTrace` 并消耗 iteration/tool/model
预算；没有“模型建议继续”这一隐式循环条件。

终止原因固定为：

```text
EVIDENCE_SUFFICIENT
INSUFFICIENT_EVIDENCE
BUDGET_EXHAUSTED
TIMEOUT
HUMAN_APPROVAL_REQUIRED
ERROR
```

## 持久化与 CLI

`SQLiteTraceStore` 新增 mutation runs、mutation results、trace links 和
assessments 的参数化表及查询/替换方法。持久化内容包括来源、repository
revision、report hash、backend/tool version、Evidence IDs 和 loop provenance；
不保存凭据，不写入 repository。

新增命令：

```bash
qa-agent assess-effectiveness \
  --requirement REQ-ID \
  --repository . \
  --trace-db ./trace.db \
  --mutation-report ./mutation-report.json \
  --min-score 0.80 \
  --format json
```

`--mutation-report` 与 `--backend` 二选一；本阶段离线报告是默认可重复入口。
缺少 `--trace-db`、`--requirement`、输入报告或显式 `--min-score` 时，CLI
返回结构化 `incomplete`，不隐式创建数据库、不读取系统时钟作为 policy、
不发起网络请求。

`qa-agent eval --version v0.4` 运行离线 parser、mapping、score、signal、
budget、termination 和 adversarial cases。human/JSON 输出均包含 decision、
termination、score status、survivor summary、signal、evidence ids、gate、
loop trace 和 budget。

## 真实项目验证

仓库内提供一个最小可重复 `examples/v04-sample/`，用于端到端 smoke 和
契约回归；它只证明 workflow 可运行，不证明真实项目效果。

真实项目 benchmark harness 必须支持输入固定的 repository path/revision、
framework、Requirement artifact、test artifact、mutation artifact 和命令，
并输出执行结果、错误、成本/延迟、映射质量和限制。至少覆盖不同代码结构的
pytest、Playwright/TypeScript 和 AI-generated test 场景；Java/PIT 只有在实际
环境与 artifact 可复现时才计入已验证样本。

benchmark 结果单独记录以下指标：Real-project Precision、False Positive、
Useful Finding Rate、Mutation Survivor Explanation Accuracy、Cost/PR 和
Latency/PR。fixture eval 的 precision/recall 不得替代这些指标，也不得把
build success 或 zero mutation result 写成 E2E success。

## 安全与边界验证

- 原始 repository 和用户工作树只读；所有补丁、Mutation 和临时文件只存在于
  受控临时副本。
- report、Requirement、测试内容和 stdout/stderr 都是不可信数据，不能变成
  shell、model 或 policy 指令。
- 强制 path、file bytes、file count、JSON size、CPU/time、tool call、model
  call 和 iteration budgets。
- command allowlist、无凭据 ownership、可选 Docker `--network none`、只读
  source mount、capability drop 和 resource limit 在执行边界实现，不依赖 prompt。
- unsupported/high-risk action fail closed；禁止自动 WRITE/RELEASE。
- secret-name、binary input、malformed report、重复 id、路径逃逸、报告过大、
  timeout、backend unavailable 和无 identity 结果均有测试。

## 验证策略与完成标准

实现按 RED → GREEN → REFACTOR 执行。测试覆盖：

- 每个 v0.4 dataclass 的字段、枚举、schema、稳定序列化和非法输入。
- v0.3 旧输入兼容，以及缺少新语义字段时的 v0.4 fail-closed。
- offline report 正例、空结果、重复 id、坏版本、未知 outcome、路径逃逸、
  超限和 prompt-in-data。
- killed/survived/timeout/error/not_run 的评分与 decision 边界。
- survivor mapping 的 verified/unverified/unmapped 边界和 Evidence 完整性。
- backend detection、typed errors、临时副本隔离、超时、allowlist 和不可用
  结果。
- Agent Loop 的 action 顺序、预算、重规划上限、LoopTrace 和全部终止状态。
- SQLite round-trip、CLI human/JSON、v0.4 eval 和 reference example。

在实现收尾前必须运行定向测试、完整 `pytest`、v0.1/v0.2/v0.3 eval、
`qa-agent eval --version v0.4`、Ruff、mypy、CLI smoke、Markdown/Mermaid 检查
和 `git diff --check`。只在这些结果与真实项目验证证据分别记录后，才可判断
v0.4 release readiness；本地代码测试通过不等于真实项目、CI、发布或外部索引
已完成。

## 文件边界

- `packages/qa_agent/test_engineering.py`：兼容性增强的 Intent/Scenario 契约。
- `packages/qa_agent/effectiveness.py`：v0.4 领域模型、状态和值校验。
- `packages/qa_agent/mutation_backends.py`：Backend 协议、能力和执行边界。
- `packages/qa_agent/mutation_adapters.py`：offline、mutmut、PIT、Stryker 归一化。
- `packages/qa_agent/effectiveness_service.py`：确定性有效性循环、mapping、
  score、signals、verification 和 gate。
- `packages/qa_agent/trace_store.py`：v0.4 trace 持久化。
- `packages/qa_agent/cli.py`：effectiveness CLI 和 eval version routing。
- `packages/qa_agent/evals.py`、`evals/test_quality/`：v0.4 正例/负例/歧义/
  对抗评测。
- `examples/v04-sample/`：可重复 reference workflow。
- `docs/v0.4-engineering/`：同步后的 scope、plan、domain、loop、adapter、
  evidence、model、eval、security 和 backlog。

该文件只冻结设计边界；它不代表上述实现已经完成。
