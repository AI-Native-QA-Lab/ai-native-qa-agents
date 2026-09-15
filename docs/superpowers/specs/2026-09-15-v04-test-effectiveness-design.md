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

实现前先把本设计中的 staged scope、`TestEffectivenessContext`、
`MutationTraceLink`、report version `1`、Gate precedence 和 benchmark evidence
boundary 同步到 `docs/v0.4-engineering/` 的 Architecture、Domain Model、
Implementation Plan、Adapter、Evidence/Gates、Model Runtime、Eval、Security
和 Backlog 文档；否则工程包与本设计不一致，不能开始代码任务。
同步后的 Architecture/Domain Model inventory 必须逐项列出
`TestEffectivenessContext`、`MutationTraceLink` 和 Assessment/Gate 的关联；
Adapter/Evidence/Eval/Security 文档必须引用同一 report schema、status enum、
budget limit 和 evidence boundary，不能继续保留只描述“接入 Mutation 工具”的
旧版 shorthand。

## 范围与非目标

### 本版本范围

- Acceptance Criterion、Risk、Observable Behavior、Business Oracle 与
  `TestIntent`/`TestScenario` 的显式关联。
- `TestEffectivenessContext` 输入契约，用于把 Requirement、Intent、Scenario、
  test identity 和相关 Evidence 明确带入 effectiveness workflow。
- `MutationRun`、`Mutant`、`MutationResult`、`MutationTraceLink`、
  `EffectivenessScore`、`FakeTestSignal` 和
  `TestEffectivenessAssessment` 的版本化契约。
- version `1` engine-agnostic offline mutation report 的严格解析、校验、
  归一化和 Evidence 生成。
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

- `acceptance_criterion_ids: tuple[str, ...] = ()`
- `risk_ids: tuple[str, ...] = ()`
- `observable_behavior: str | None = None`
- `business_oracle: str | None = None`

`TestScenario` 增加 `business_oracle: str | None` 和
`acceptance_criterion_ids: tuple[str, ...]`、`test_ids: tuple[str, ...]`，它们的
默认值分别为 `None`、`()`、`()`。为兼容已持久化的 v0.3 结果，
新增字段在旧输入中可以为空；但 v0.4 effectiveness assessment 将空的
`observable_behavior`、`business_oracle` 或必要的 criterion 关联视为证据
不足，不会用 `requirement_id`、`"test passes"` 等占位文本补齐。

`test_ids` 是 Mutation report 中 `executed_test_ids` 和 `killing_test_ids` 使用
的稳定身份。它们可以是 framework-native node id，但必须在 context 中原样列出；
仅有文件名或路径相似性不能构成 verified test identity。`risk_ids` 可以为空，
只有 context 同时提供对应风险 Evidence 时才参与高风险判定。

`TestEffectivenessContext` 是 assessment 的显式输入，至少包含：context schema
version `v0.4`、requirement id、一个或多个 enriched `TestIntent`、相关
`TestScenario`、test identity 列表、observable behavior/business oracle、
repository-relative target paths 和 test paths、
execution evidence IDs、assertion evidence IDs、可引用的
Requirement/criterion/risk Evidence IDs，以及 context artifact hash。context
artifact 同时携带新增 Evidence records，或明确引用 trace store 中已经存在的
同 id records；孤立的 Evidence ID 不算有效证据。
context 可以来自 v0.3 结果的离线导出，或由调用方准备的受限 JSON；CLI 不从
测试文件名称臆造 Intent/Oracle。没有 context 时，workflow 在 `UNDERSTAND`
阶段终止为 `INSUFFICIENT_EVIDENCE`，不会先执行昂贵的 Mutation。

其最小输入形状为：

```json
{
  "schema_version": "v0.4",
  "requirement_id": "REQ-1",
  "intents": [
    {
      "id": "TI-1",
      "requirement_id": "REQ-1",
      "subject": "checkout decline behavior",
      "acceptance_criterion_ids": ["AC-1"],
      "risk_ids": [],
      "observable_behavior": "Declined payment shows an error",
      "business_oracle": "The response is rejected and the error is visible",
      "evidence_ids": ["EV-REQ-001", "EV-AC-001"]
    }
  ],
  "scenarios": [
    {
      "id": "TS-1",
      "intent_id": "TI-1",
      "name": "declined payment",
      "steps": ["submit a declined payment"],
      "expected_outcome": "the error state is visible",
      "test_ids": ["tests/test_checkout.py::test_declined"],
      "acceptance_criterion_ids": ["AC-1"],
      "business_oracle": "The error state is asserted",
      "evidence_ids": ["EV-TEST-001", "EV-AC-001"]
    }
  ],
  "test_ids": ["tests/test_checkout.py::test_declined"],
  "target_paths": ["src/checkout.py"],
  "test_paths": ["tests/test_checkout.py"],
  "execution_evidence_ids": ["EV-EXEC-001"],
  "assertion_evidence_ids": ["EV-TEST-001"],
  "evidence_ids": ["EV-REQ-001", "EV-AC-001", "EV-TEST-001", "EV-EXEC-001"],
  "evidence": [
    {
      "id": "EV-REQ-001",
      "type": "requirement",
      "subject": "REQ-1",
      "path": "requirement.md",
      "source_ref": "requirement.md#L1",
      "line_start": 1,
      "line_end": 1,
      "content_hash": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
      "status": "verified",
      "provider": "repository",
      "extractor": "v0.2-requirement",
      "created_at": "2026-09-15T00:00:00+00:00",
      "loop_iteration": 0,
      "redacted_excerpt": null,
      "metadata": {
        "redaction": {"applied": false, "policy": "bounded-redacted-v1", "max_bytes": 4096},
        "limits": {"context_bytes": 1000000, "report_bytes": 2000000}
      }
    },
    {
      "id": "EV-AC-001",
      "type": "acceptance_criteria",
      "subject": "AC-1",
      "path": "requirement.md",
      "source_ref": "requirement.md#L1",
      "line_start": 1,
      "line_end": 1,
      "content_hash": "sha256:3333333333333333333333333333333333333333333333333333333333333333",
      "status": "verified",
      "provider": "repository",
      "extractor": "v0.2-acceptance-criteria",
      "created_at": "2026-09-15T00:00:00+00:00",
      "loop_iteration": 0,
      "redacted_excerpt": null,
      "metadata": {
        "redaction": {"applied": false, "policy": "bounded-redacted-v1", "max_bytes": 4096},
        "limits": {"context_bytes": 1000000, "report_bytes": 2000000}
      }
    },
    {
      "id": "EV-TEST-001",
      "type": "test_assertion",
      "subject": "tests/test_checkout.py::test_declined",
      "path": "tests/test_checkout.py",
      "source_ref": "tests/test_checkout.py#L1",
      "line_start": 1,
      "line_end": 1,
      "content_hash": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
      "status": "verified",
      "provider": "pytest",
      "extractor": "v0.3-review",
      "created_at": "2026-09-15T00:00:00+00:00",
      "loop_iteration": 0,
      "redacted_excerpt": null,
      "metadata": {
        "redaction": {"applied": false, "policy": "bounded-redacted-v1", "max_bytes": 4096},
        "limits": {"context_bytes": 1000000, "report_bytes": 2000000}
      }
    },
    {
      "id": "EV-EXEC-001",
      "type": "test_execution",
      "subject": "tests/test_checkout.py::test_declined",
      "path": "tests/test_checkout.py",
      "source_ref": "tests/test_checkout.py#L1",
      "line_start": 1,
      "line_end": 1,
      "content_hash": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
      "status": "verified",
      "provider": "pytest",
      "extractor": "v0.3-execution",
      "created_at": "2026-09-15T00:00:00+00:00",
      "loop_iteration": 0,
      "redacted_excerpt": null,
      "metadata": {
        "redaction": {"applied": false, "policy": "bounded-redacted-v1", "max_bytes": 4096},
        "limits": {"context_bytes": 1000000, "report_bytes": 2000000}
      }
    }
  ],
  "artifact_hash": "sha256:0000000000000000000000000000000000000000000000000000000000000000"
}
```

上面的 `REVISION` 和示例 hash 仅表示字段形状，不是可直接通过校验的 fixture；
reference example 和 eval fixture 必须用真实 revision，并按本文规定重新计算
canonical artifact/raw bytes hash。

`intents`、`scenarios`、`test_ids`、`target_paths`、`test_paths` 和 `evidence_ids`
必须是 bounded arrays；`target_paths`/`test_paths` 必须是 repository-relative、
normalized、无 `..`/绝对路径的非空数组。context 中的 requirement id 必须与 CLI 参数一致；
`test_ids` 必须在至少一个
context 中的 requirement id 必须与 CLI 参数一致。`test_ids` 必须在至少一个
scenario 中出现，且不能重复。实现可以保留 v0.3 的其它字段，但不能省略上述
用于 mapping 和 verification 的字段。`execution_evidence_ids` 和
`assertion_evidence_ids` 必须非空；其 IDs 必须存在于 context/trace store 的
Evidence records 中，且至少有一条 `status = verified` 才能成为 `pass` 的输入。

context artifact hash 的计算输入是删除自身 `artifact_hash` 字段后的 canonical
JSON（UTF-8、对象键排序、无空白）；验证时必须重新计算，不能信任 JSON 内的
hash。`evidence` 中每个 record 的 `id` 必须唯一，且所有被引用的 Evidence ID
必须在同一 context 或 trace store 中解析到一个 record。criterion/risk ID 也必须
能解析到 context 中的 Requirement/criterion/risk Evidence；只有 ID 文本而没有
对应 Evidence 的关联不成立。

`TestEngineeringRequest` 在现有 `framework` 字段之后追加同样的 optional 字段，
具体为 `acceptance_criterion_ids: tuple[str, ...] = ()`、
`risk_ids: tuple[str, ...] = ()`、`observable_behavior: str | None = None` 和
`business_oracle: str | None = None`，以保留现有 v0.3 positional call 的参数
顺序。v0.3 调用方不传这些字段时保持现有 v0.3 行为和
`schema_version = "v0.3"`，包括当前 legacy 的 generated-candidate 描述；
legacy `TestEngineeringResult.to_dict()` 在这些字段仍为默认值时保持原 v0.3
wire shape，不强制写入 v0.4-only keys。v0.3 输入读取只允许把新增字段当作
optional additive fields，缺失字段按上述默认值处理。v0.4 context importer
只能显式接收 `schema_version = "v0.4"`，或由单独的 `import_v03` 路径读取
`schema_version = "v0.3"` 并标记 `source_version = "v0.3"`/legacy semantics；
它不会静默升级版本，也不把旧的 `"test passes"` 转换为 Business Oracle。缺少
新语义字段的 imported context 必须在 `UNDERSTAND` fail closed，而不是执行
Mutation 后再补字段。

Service 的输入对象固定为：`TestEffectivenessRequest(requirement_id: str,
repository: Path, context: TestEffectivenessContext | None, mutation_report: Path | None,
backend: MutationBackend | None, min_score: float | None, budget: ExecutionBudget)`。
`mutation_report` 与 `backend` 必须恰有一个非空；`context = None` 或
`min_score = None` 是可序列化的 incomplete request，而不是隐式默认值。CLI 负责
在构造 durable store 前读取 bounded context、选择 offline parser 或注入固定
backend；Service 不从字符串拼接命令，也不从 report/Requirement 读取执行指令。

### Mutation 模型

`MutationRun` 至少包含：run id、assessment id、backend、repository revision、target paths、
selected test IDs/paths、process status、observation status、mutant ids 和 Evidence IDs。
`process status`
只允许 `completed`、`partial`、`unavailable`、`error`、`not_run`。
`observation status` 只允许 `complete`、`partial`、`unknown`，用于区分“每个
计划项都有明确结果，但其中有 not_run/timeout/error”和“报告被截断、无法知道
遗漏了什么”。
Backend 的进程状态不是 Agent Loop 的终止原因；后者只由
`TestEffectivenessAssessment.termination_reason` 产生。比如 backend timeout
会保留 `MutationResult.outcome = timeout` 和 `process_status = partial`，由
Agent Runtime 决定 assessment 是 `TIMEOUT` 还是 `INSUFFICIENT_EVIDENCE`。

状态不变量固定为：`completed` 只能包含 `killed`/`survived` 结果，并且每个
active mutant 都必须有一个 terminal result；`partial` 至少包含一个 eligible
mutant，所有已返回的 mutant 都必须有显式 outcome，未执行部分以 `not_run`
保留；`unavailable`/`error`/`not_run` 不得被当成可评估的完整 MutationRun。
一个 `observation_status = complete`、结果可解释但包含 `not_run` 或 per-mutant
timeout/error 的 `partial` run 可以产生 `EVIDENCE_SUFFICIENT` + `warn`（或按
阈值产生 `fail`）；`observation_status = partial/unknown` 的报告、进程超时导致
的截断、没有可验证的完整观察，或者 Agent 自身因 timeout/budget 停止时，必须
使用相应的非 `EVIDENCE_SUFFICIENT` termination reason 并得到 `incomplete`。

`Mutant` 至少包含：mutant id、repository-relative path、positive line number、
operator、original text、mutated text、normalized status 和 Evidence IDs。
`normalized status` 只允许 `active`、`invalid`、`not_run`。外部 backend 可以
返回结构上完整但自身标记为 `invalid` 或 `not_run` 的记录；这类记录不进入
eligible denominator，但其状态和错误/未执行 Evidence 必须保留。offline
report 若在结构校验阶段发现缺字段、非法值或路径逃逸，整个 report 返回
typed invalid-input error，不把 malformed 输入部分归一化为 `invalid` mutant。

`MutationResult` 至少包含：run id、mutant id、outcome、executed test ids、killing
test ids、duration、stdout/stderr content hashes 和 Evidence IDs。`outcome` 只允许：

```text
killed | survived | timeout | error | not_run
```

`MutationTraceLink` 至少包含：run id、mutant id、mapping status 和 Evidence IDs；
requirement id、intent id、scenario id、business oracle 在
`verified`/`unverified` 时按实际可得性填写，在 `unmapped` 时必须为 `None`，
不能填入占位文本。mapping status 允许 `verified`、`unverified`、`unmapped`。
只有报告中的 exact test identity 与 context 中的 `test_ids`、对应 scenario、
Business Oracle 和 Evidence 全部一致时才可产生 `verified`。对 survivor，exact
identity 来自该 mutant 的 `executed_test_ids`；若该字段为空，只能在 run-level
`selected_test_ids` 唯一对应一个 scenario 时使用，否则为 `unmapped`。路径名、
文件名或自然语言相似性最多产生 `unverified`，不能升级为 verified。

当一个 survivor 没有候选 Intent/Scenario 时，仍创建只带 run id、mutant id、
`mapping_status = "unmapped"` 和 survivor Evidence 的 link；当候选来自启发式
路径/token 匹配但没有 exact test identity 时，创建带可得字段的
`unverified` link。这样既保留 survivor，又不伪造缺失的 Requirement 或 Oracle。

`EffectivenessScore` 至少包含：eligible mutants、killed mutants、survived
mutants、timeout mutants、error mutants、not-run mutants、score、score status
和 Evidence IDs。`score` 为 `float | None`，非空时必须在闭区间 `[0, 1]`；
`score status` 只允许 `computed`、`not_computable`、`incomplete`。只有 `killed`
与 `survived` 属于 eligible denominator；`timeout`、`error` 和 `not_run` 必须
单独保留，不能静默计为 killed 或 survived。计算先使用整数计数，再用
decimal half-up 规则序列化为四位小数；分母为零时 score 为 `None`。计数不变量
为 `eligible = killed + survived`，且每个 active mutant 只能出现在五种 outcome
之一；`not_run` 不得被当作“没有结果”而从 total 中删除。

`FakeTestSignal` 至少包含：signal id、signal kind、severity、message、source、
verification status 和 Evidence IDs。首个切片支持静态断言信号、执行信号、
Requirement relevance 信号、Oracle 缺失信号和 Mutation survivor 信号；每条
信号必须能解释触发原因。`signal kind` 只允许
`static_assertion`、`execution`、`requirement_relevance`、`oracle_missing`、
`mutation_survivor`、`semantic`；severity 沿用 `critical`、`high`、`medium`、
`low`。首个切片的 deterministic severity policy 固定为：缺失关键 Oracle 或
Requirement relevance 为 `high`，明显恒真/无效 assertion 或 execution failure
为 `high`，普通 verified survivor 为 `medium`；若 survivor 能通过 verified
Risk Evidence 关联到 `high`/`critical` risk，则升级为 `high`/`critical`；模型
产生的 semantic signal 最高为 `medium` 且必须是 `unverified`。该 policy 只允许
Evidence-backed risk metadata 触发升级，不能由模型自行提供 severity。

`TestEffectivenessAssessment` 至少包含：assessment id、requirement id、MutationRun、
EffectivenessScore、survivor links、fake-test signals、decision、termination
reason、Mutation Gate、Evidence IDs、LoopTrace 和 ExecutionBudget。

`decision` 只允许 `pass`、`warn`、`fail`、`incomplete`；`termination_reason`
只允许 `EVIDENCE_SUFFICIENT`、`INSUFFICIENT_EVIDENCE`、`BUDGET_EXHAUSTED`、
`TIMEOUT`、`HUMAN_APPROVAL_REQUIRED`、`ERROR`。`incomplete` 是 decision，
不是 termination reason；关键输入缺失时使用
`decision = incomplete, termination_reason = INSUFFICIENT_EVIDENCE`。

新增 v0.4 输出模型使用 `schema_version = "v0.4"`；嵌入的旧 v0.3
`TestIntent`/`TestScenario` 保留其兼容字段和来源版本，不被伪装成新的
evidence。新生成的 Mutation/assessment IDs 由输入 artifact 内容 hash 和领域
对象标识派生；导入的 v0.3 IDs 原样保留。输出排序按 stable id/path/line 排序，
确保相同输入产生相同的 score、mapping 和 decision。时间戳只用于 provenance，
不参与评分。

### Evidence envelope

每个 v0.4 Evidence 必须沿用现有 `Evidence` 字段：id、type、path、positive
line range、content hash、status、provider、extractor、created timestamp 和
loop iteration；并以向后兼容的可选字段扩展 `subject`、`source_ref`、
`redacted_excerpt` 和 `metadata`。v0.4 新生成的 Evidence 必须填写全部扩展字段：
`subject` 是稳定的 Requirement/Intent/Scenario/Test/Mutant/Assessment ID，
`source_ref` 是可复现的 artifact 或 repository-relative location，
`redacted_excerpt` 为 `null` 或不超过 4096 UTF-8 bytes 的文本，`metadata` 必须
至少包含：

```json
{
  "redaction": {"applied": false, "policy": "bounded-redacted-v1", "max_bytes": 4096},
  "limits": {"context_bytes": 1000000, "report_bytes": 2000000}
}
```

Permission Evidence 还必须在 `metadata.permission` 中记录 action、allowed、
reason 和是否执行了 external command；被拒绝的 action 必须为 false，且不能有
对应 command observation。新增 type 至少包括已有的 `requirement`、
`acceptance_criteria`、`test_assertion`、`test_execution`，以及 `test_context`、`mutation_report`、
`mutation_run`、`mutant_killed`、`mutant_survived`、`mutation_unexecuted`、
`effectiveness_score`、`fake_test_signal` 和 `backend_capability`。
Evidence 的 path/subject/source_ref 必须能定位到 context、报告、
repository-relative source 或 backend output；`line_start >= 1`、
`line_end >= line_start`，content hash 必须是带算法前缀的 SHA-256。v0.4 Evidence
的 `status` 只允许现有的 `verified` 或 `unverified`；其它状态是 invalid input。
缺少
subject/location/source hash、超出 excerpt/limits，或 status 未经 verifier 确认
时不能通过 Evidence verification。context 序列化大小上限为
`max_context_bytes`，raw report 文件上限为 `max_report_bytes`，query 返回的
Evidence 数量和单条 excerpt 也必须受同一 Service budget 限制。原始大段
stdout/stderr 不直接写入 Evidence，只保存有界的 redacted excerpt（如调用方
明确允许）和 content hash。

## Backend 与 Adapter 边界

`MutationBackend` 提供两个独立能力：

1. `detect(repository) -> BackendCapability`：报告是否安装、版本、支持的
   语言/framework、不可用原因和风险限制。
2. `run(request) -> MutationBackendResult`：在受控副本中执行并返回 process
   observation；Agent Runtime 再把它组装成 `MutationRun`。

`MutationRequest` 至少包含 repository path、repository revision、target paths、
selected test ids/paths、timeout、max mutants 和 permission context。
`MutationBackendResult` 至少包含 backend/tool version、process status、observation
status、
normalized mutants、normalized mutation results、provider Evidence 和 raw
report hash。Backend 只拥有 process status 和 observation，不拥有 Agent Loop
termination、gate decision、re-plan 或 durable quality truth。

`MutationBackendResult.process_status` 使用 `MutationRun` 的同一组
`completed`/`partial`/`unavailable`/`error`/`not_run` 值；它不会携带或覆盖
assessment termination reason。Offline adapter 的 `parse(report_path,
repository_revision, limits) -> MutationBackendResult` 也只返回 observation，
由 Service 注入 run/assessment IDs 并创建 Agent-owned Evidence。

`BackendCapability.status` 只允许 `available`、`unavailable`、`unsupported`。
Typed errors 至少区分 `MutationInputError`、`MutationUnavailableError`、
`MutationUnsupportedError`、`MutationConfigurationError` 和
`MutationExecutionError`；Service 将它们转换为有 Evidence 的 process result
和适当的 Agent termination，而不是吞掉错误。

转换规则固定为：`MutationInputError`、`MutationUnavailableError` 和
`MutationUnsupportedError` 产生 `decision = incomplete`、
`termination_reason = INSUFFICIENT_EVIDENCE`；`MutationConfigurationError` 或
`MutationExecutionError` 在没有完整可解释 observation 时产生同样的
`incomplete`，在有 `observation_status = complete` 的 partial result 时由 Gate
按 `warn`/`fail` 处理；未分类异常才产生 `termination_reason = ERROR`。每种错误
都必须创建带 source/location/hash 的 Evidence，且不得把错误吞成空 report。

Backend 不决定选哪些测试、不做重规划、不计算质量门、不调用模型，也不写入
原始工作树。

offline adapter 接受 version `1` 的 engine-agnostic JSON。报告只作为输入数据
解析，任何字段类似 shell command、prompt 或 instruction 的内容都不会执行。
其最小结构为：

```json
{
  "schema_version": 1,
  "backend": "offline",
  "repository_revision": "REVISION",
  "observation_status": "complete",
  "target_paths": ["src/cart.py"],
  "selected_test_ids": ["tests/test_cart.py::test_declined"],
  "mutants": [
    {
      "id": "M-001",
      "path": "src/cart.py",
      "line": 12,
      "operator": "replace-constant",
      "original": "return False",
      "mutated": "return True",
      "outcome": "killed",
      "executed_test_ids": ["tests/test_cart.py::test_declined"],
      "killing_test_ids": ["tests/test_cart.py::test_declined"],
      "duration_ms": 12,
      "stdout_hash": "sha256:...",
      "stderr_hash": null
    }
  ]
}
```

`schema_version`、`backend`、`repository_revision`、`observation_status`、`target_paths`、
`selected_test_ids` 和 `mutants` 是必填字段且数组不能为空；每个 mutant 的 id、
relative path、positive line、operator、original、mutated、outcome 和
`executed_test_ids` 是必填字段。`executed_test_ids` 必须是
`selected_test_ids` 的非重复子集；`killing_test_ids` 在 `killed` 时必须是非空的
`executed_test_ids` 子集，在其它 outcome 时必须为空。`not_run` 的
`executed_test_ids` 必须为空。duration 可以为零，output hashes 可以为 null。
outcome 只允许已有的五个值。`observation_status` 只允许 `complete` 或
`partial`；`complete` 表示报告对它声明的全部计划 mutant 给出明确 terminal
outcome，`partial` 表示报告可能被截断或遗漏计划项。
报告的 revision 必须与调用方观察到的 repository revision 一致；缺失或冲突
时不计算 score。`backend` 只能是 `offline`、`mutmut`、`pit` 或 `stryker`；
`schema_version` 必须是整数 `1`。assessment Service 还必须校验 report 的
`target_paths` 是 context target paths 的非空子集，`selected_test_ids` 是
context `test_ids` 的非空子集；不满足时保留 report Evidence 但以
`INSUFFICIENT_EVIDENCE` fail closed。

offline report 的 raw bytes hash 在读取后立即计算，作为
`MutationBackendResult.raw_report_hash` 和 `mutation_report` Evidence 的来源
hash；不以解析后的 JSON 重新序列化结果替代原始 hash。report 的
`process_status` 由 adapter 根据所有 active mutant 的结果归一化：所有 active
mutant 都有 killed/survived 为 `completed`，存在显式 timeout/error/not_run 且
仍有 eligible 结果为 `partial`，没有可评估结果或 adapter 无法运行则为
`unavailable`/`error`/`not_run`。adapter 不得把缺失 mutant 行推断成 killed。

必须校验：顶层对象、schema version、backend、mutant 数组、path 边界、line、
outcome、数组大小、字符串大小和 JSON 总大小。重复 mutant id、未知 outcome、
非法路径、缺少必要字段和 malformed JSON 返回 typed invalid-input error，不能
产生部分成功的通过结论。

mutmut adapter 是首个真实执行后端。它通过显式 allowlist、临时副本、超时、
资源预算和只读源代码边界运行，并将不可用、执行失败和部分结果分别归一化。
PIT/Stryker adapter 在本阶段至少提供 capability result、typed unavailable/
unsupported/configuration errors、固定 fixtures 和协议测试；未实际执行时
返回 `INSUFFICIENT_EVIDENCE`。

每个 offline、mutmut、PIT 和 Stryker adapter 都必须有四类独立验证：capability
contract、typed error contract、固定 input/output fixture 和不执行不可信字段的
security contract。未安装工具不是测试失败，也不能被转换成空的 mutation run。
实现与测试的最小归属为：`packages/qa_agent/mutation_backends.py` 定义协议、
capability 和 typed errors，`packages/qa_agent/mutation_adapters.py` 定义四个
adapter；`tests/test_mutation_backends.py`、`tests/test_mutation_adapters.py` 和
`tests/fixtures/v04/mutation/` 分别覆盖协议/错误、各 adapter fixture 及
prompt-in-data、shell-like field、path escape、report-size 与 command allowlist
安全契约。Backend capability 的 `reason`、tool version、supported frameworks、
limits 和 Evidence source 也必须出现在可序列化结果中。

## 有效性评估与 Gate

评分定义为：

```text
score = killed_mutants / (killed_mutants + survived_mutants)
```

分母为零时 `score = None`，`score_status = not_computable`。threshold 是
调用方显式提供的 Mutation Gate policy，不把一个没有项目背景的全局数字伪装
成普适事实；缺少 threshold 时，assessment 可以报告计算结果，但 Gate 不得
给出 `pass`。

Mutation Gate 先计算以下互斥前置状态，再按固定优先级决策，避免规则重叠：

- `input_complete`：context、report、repository revision、threshold、Oracle、
  execution/assertion Evidence 和所有被引用 Evidence 均可验证；至少存在一个
  eligible mutant；Agent termination 为 `EVIDENCE_SUFFICIENT`；并且
  `assessable_run` 为 true。
- `assessable_run`：`process_status` 为 `completed`，或为 `partial` 且
  `observation_status = complete`；后一种情况表示所有已计划的结果都有明确的
  killed/survived/timeout/error/not_run outcome，而不是报告截断。
- `quality_failure`：score 低于 threshold，或存在已验证的 high/critical
  survivor/fake signal。
- `clean_pass`：score 达到 threshold、run 为 `completed`、没有
  timeout/error/not_run、没有 high/critical signal、所有 survivor link 都是
  `verified`，并且 execution 与 assertion Evidence 至少各有一条 verified 记录。

在这些定义上，Gate 使用以下固定优先级：

1. `incomplete`：`input_complete` 为 false；包括 context/report/repository
   evidence 缺失或无效、revision 冲突、没有 eligible mutant、backend
   `unavailable`/`error`/`not_run`、关键 Oracle/threshold 缺失、execution/assertion
   Evidence 缺失、run 不可评估（包括 `observation_status = partial/unknown`），
   或 Agent termination 不是 `EVIDENCE_SUFFICIENT`。此时 `score_status` 可保留已计算的中间值，但
   decision 不得是 pass/warn/fail。
2. `fail`：`quality_failure` 为 true。该级别要求输入完整且 run 可解释；仅有
   unverified/unmapped mapping 不得直接触发 fail。
3. `pass`：`clean_pass` 为 true。
4. `warn`：输入完整、没有触发 fail，且 score 达到 threshold，但存在
   `partial` process、低/中严重度 signal、unverified/unmapped survivor mapping
   或其它已明确说明的有效性限制。若输入完整但 score 低于 threshold，按第 2
   条为 fail，不会落入 warn。

因此，`killed = 1, not_run = 99` 在有 valid report 且 observation complete 时
只能是 `partial + warn`（阈值不满足则为 fail），绝不能是 pass；如果 99 个
未执行项没有显式记录或 report 被截断，则是 incomplete。timeout/error/not_run
不计入 score，但只要它们使 run 不可解释或 Agent 未到达验证终点就必须 incomplete。

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
预算；`max_replans = 1`；没有“模型建议继续”这一隐式循环条件。

v0.4 沿用 `ExecutionBudget`，但必须通过显式的 `ExecutionBudget.v04_defaults()`
构造首个切片预算，不能改变 v0.1-v0.3 调用方现有的构造默认值。v0.4 budget
的完整字段和类型固定为：`max_iterations: int`、`max_tool_calls: int`、
`max_model_calls: int`、`timeout_seconds: int`、`max_replans: int`、
`max_mutants: int`、`max_report_bytes: int`、`max_context_bytes: int`。计数和
byte limit 必须是非负整数，`timeout_seconds` 和 byte limit 必须大于零；非法
预算在进入 `UNDERSTAND` 前返回 `ERROR`，不调用 backend。v0.4 defaults 为
`max_iterations = 8`、`max_tool_calls = 8`、`max_model_calls = 1`、
`timeout_seconds = 120`、`max_replans = 1`、`max_mutants = 500`、
`max_report_bytes = 2_000_000`、`max_context_bytes = 1_000_000`。

计数语义固定为：每次进入一个 loop phase 的状态转移消耗一个 iteration；
backend capability/read/execute 和 durable trace query 各消耗一个 tool call；
模型 provider invoke 消耗一个 model call；重规划动作消耗一个 re-plan。context
读取按 UTF-8 bytes 计入 `max_context_bytes`，raw report 读取按文件 bytes 计入
`max_report_bytes`，mutation 选择按 mutant 数计入 `max_mutants`。每个 action 和
输入读取前检查对应上限；wall-clock 使用 monotonic runtime timer，超时终止为
`TIMEOUT`；迭代/工具/模型/重规划/mutant/report/context 上限终止为
`BUDGET_EXHAUSTED`。这些预算由 Agent Runtime/Service 持有，Backend 不得自行
扩大或重置。

v0.4 `LoopTrace` 在保留 v0.3 的 `iteration`、`action_id`、`status`、
`observation_id` 字段之外，必须记录 `assessment_id`、phase、permission result
ID、evidence IDs 和 termination reason（无则为 `null`）。status 只允许
`started`、`completed`、`rejected`、`skipped`、`terminated`；trace 按 iteration
和 action stable order 序列化，不能只保存最终状态。

`PermissionContext` 至少包含 repository path、受控副本 path、allowed actions、
approval-required actions 和 command/file limits；`PermissionResult` 的完整
字段为 `action`、`allowed`、`reason`、`evidence_id`、`external_command_executed`。
其中 action 只允许 `READ`、`EXECUTE_MUTATION`、`MODEL_SURVIVOR_MAPPING`、
`WRITE`、`COMMIT`、`MERGE`、`RELEASE`；v0.4 默认只允许前三者，后四者无论
是否有 approval 都拒绝。缺少 result 时 action 不得执行。

`TerminationPolicy` 是 Agent Runtime 的无副作用策略对象，输入当前 iteration、
tool/model/re-plan counts、monotonic elapsed time、permission result、process
observation completeness 和 evidence state，输出一个终止原因或 `None`。检查
顺序固定为：权限拒绝、timeout、budget exhaustion、evidence insufficiency；
`EVIDENCE_SUFFICIENT` 只由 `VERIFY` 成功后产生，已确定的 `fail`/`warn` 只在
`VERIFY` 后作为正常评估终点，不提前结束 `MUTATE`。Backend 不能直接设置
assessment 的 termination reason。`TerminationPolicy` 同时保留现有
`should_stop(state, budget)` 入口供旧服务使用；v0.4 使用带 evidence/process
状态的 `evaluate(...)` 入口。

权限检查在 `SELECT` 和 `MUTATE` 前执行，默认只允许 `READ`、
`EXECUTE_MUTATION`（受控副本）和可选的 `MODEL_SURVIVOR_MAPPING`；`WRITE`、
`COMMIT`、`MERGE`、`RELEASE` 始终拒绝。权限结果必须先写入 Observation/Evidence，
再决定是否调用外部命令。被拒绝的高风险动作若需要用户授权则终止为
`HUMAN_APPROVAL_REQUIRED`；若授权上下文缺失或证据不充分则终止为
`INSUFFICIENT_EVIDENCE`，两者都不调用外部命令。

每个 action 的完整 permission result 至少包含 action、allowed、reason、
evidence id 和 `external_command_executed`；缺少 result 时 action 不得执行。
该 policy 只授权受控副本中的执行，不授权对原始 repository 的写操作。

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

`SQLiteTraceStore` 新增 test contexts、mutation runs、mutation results、
mutation trace links 和 assessments 的参数化表及查询/替换方法。持久化内容
包括来源、repository revision、report hash、backend/tool version、Evidence IDs
和 loop provenance；不保存凭据，不执行 repository write。`--trace-db` 是调用方
显式指定的 durable output，v0.4 CLI 拒绝将其放在 repository 路径下，以免把
trace state 与被分析工作树混在一起。

Schema 初始化/迁移使用 SQLite `PRAGMA user_version` 和 additive migrations，
不得删除或重写现有 v0.2/v0.3 表。legacy database 的 `user_version = 0` 视为
未版本化旧 schema；migration 只执行 `CREATE TABLE IF NOT EXISTS` 和必要的
`CREATE INDEX IF NOT EXISTS`，完成后设置为 v0.4 schema version `2`。已知高于
`2` 的版本返回 migration error，不降级也不覆盖数据。每个连接都必须启用
`PRAGMA foreign_keys = ON`，写入使用 transaction。

新增表的最小列和主键固定如下（`*_json` 必须是 canonical JSON，禁止把
Requirement/Intent/Scenario/Mutation 的关键关联只藏在 payload 中）：

- `evidence_records(evidence_id PRIMARY KEY, requirement_id, subject, type, path,
  source_ref, line_start, line_end, content_hash, status, provider, extractor,
  created_at, loop_iteration, metadata_json)`。
- `test_contexts(context_id PRIMARY KEY, requirement_id, schema_version,
  repository_revision, artifact_hash, payload_json, evidence_ids_json, source_version)`。
- `mutation_runs(run_id PRIMARY KEY, assessment_id, backend, tool_version,
  repository_revision, process_status, observation_status, target_paths_json,
  selected_test_ids_json, selected_test_paths_json, mutant_ids_json, report_hash,
  evidence_ids_json)`。
- `mutants(run_id, mutant_id, path, line, operator, original, mutated,
  normalized_status, evidence_ids_json, PRIMARY KEY(run_id, mutant_id))`。
- `mutation_results(run_id, mutant_id, outcome, executed_test_ids_json,
  killing_test_ids_json, duration_ms, stdout_hash, stderr_hash, evidence_ids_json,
  PRIMARY KEY(run_id, mutant_id))`。
- `mutation_trace_links(run_id, mutant_id, requirement_id, intent_id, scenario_id,
  business_oracle, mapping_status, evidence_ids_json, PRIMARY KEY(run_id, mutant_id))`。
- `assessments(assessment_id PRIMARY KEY, requirement_id, context_id, run_id,
  score_json, gate_json, decision, termination_reason, evidence_ids_json,
  loop_trace_json, budget_json)`。
- `observations(observation_id PRIMARY KEY, assessment_id, action_id, phase,
  summary, structured_data_json, evidence_ids_json, created_at)`。
- `loop_traces(assessment_id, iteration, action_id, phase, status, observation_id,
  permission_evidence_id, evidence_ids_json, termination_reason,
  PRIMARY KEY(assessment_id, iteration, action_id))`。

`mutation_results.run_id`、`mutation_trace_links.run_id`、`assessments.context_id`、
`assessments.run_id`、`observations.assessment_id`、`loop_traces.assessment_id` 和
`loop_traces.observation_id` 是显式关联，不能只依赖 JSON 内部的隐含关系。
Evidence query 必须按 `evidence_id`、requirement、subject 和 bounded limit 查询，
返回顺序稳定且不能绕过 `max_context_bytes` 或 excerpt limit。

新增命令：

```bash
qa-agent assess-effectiveness \
  --requirement REQ-ID \
  --repository . \
  --trace-db /tmp/qa-agent-trace.db \
  --test-context ./test-context.json \
  --mutation-report ./mutation-report.json \
  --min-score 0.80 \
  --format json
```

`--mutation-report` 与 `--backend {mutmut|pit|stryker}` 二选一；本阶段离线
报告是默认可重复入口。`--test-context` 是 assessment 的必需输入。
`--min-score` 必须是闭区间 `[0, 1]` 的显式 policy，且拒绝 NaN/Infinity。
v0.4 parser 会保留参数
缺失的语义输入并输出结构化 `decision = incomplete`、
`termination_reason = INSUFFICIENT_EVIDENCE`；未知参数仍是 CLI usage error。
CLI 不隐式创建 repository 内的数据库、不读取系统时钟作为 policy、不发起
网络请求。

v0.4 command 的参数校验在构造 `SQLiteTraceStore` 之前完成；缺少
`--requirement`、`--repository`、`--trace-db`、`--test-context`、
`--mutation-report`/`--backend` 或 `--min-score` 时返回上述结构化 incomplete，
不会创建任何数据库。显式提供且位于 repository 之外的 `--trace-db` 可以创建
或 additive-migrate schema；其 parent directory 不存在、不可写或路径解析失败
也只返回 incomplete/invalid，不创建半成品文件。`--backend` 只选择受支持的
backend，不从 report 读取命令；backend 不可用时返回 `incomplete`。退出码固定
为：`pass`/`warn` 为 0，`fail` 为 1，`incomplete` 或 invalid input 为 2，未分类
内部错误为 3。

`--mutation-report` 与 `--backend` 同时出现是 usage error；只给
`--backend` 时由固定 backend 配置构造 `MutationRequest`，命令和参数不来自
repository/report/model；只给 report 时使用 `OfflineMutationReportAdapter`，
report 内的 backend 字段只用于归一化与 capability 记录。缺失语义参数时，CLI
输出的最小 JSON 仍固定为：

```json
{
  "schema_version": "v0.4",
  "assessment_id": null,
  "requirement_id": null,
  "decision": "incomplete",
  "termination_reason": "INSUFFICIENT_EVIDENCE",
  "missing_inputs": ["--test-context"],
  "score": null,
  "score_status": "not_computable",
  "evidence_ids": [],
  "loop_trace": [],
  "budget": null,
  "gate": {"decision": "incomplete", "reasons": ["missing input"]}
}
```

有 assessment 的 JSON 输出必须至少包含上述字段，并增加 `mutation_run`、
`score` 明细、`survivor_links`、`signals`、`evidence_ids`、`loop_trace`、
`budget`、`gate` 和 `artifacts`（context/report/repository revision/hash）；
human 输出必须逐项显示 decision、termination、score status、eligible/killed/
survived/timeout/error/not_run、survivor mapping、signals、evidence IDs、gate、
loop trace 和 budget。输出中的 `assessment_id` 在拥有 context/report 时由
canonical artifact hash 派生，缺少输入时保持 null。

`qa-agent eval --version v0.4` 运行离线 parser、mapping、score、signal、
budget、termination 和 adversarial cases。human/JSON 输出均包含 decision、
termination、score status、survivor summary、signal、evidence ids、gate、
loop trace 和 budget。

如果启用 Model Runtime，只允许 task type
`effectiveness-survivor-mapping`，要求 `structured_output` capability、最多一
次 model call、redacted bounded context 和固定 mapping output schema。响应必须
包含 provider/model/usage/latency 和完整 fallback metadata：
`fallback_used`、`requested_provider`、`selected_provider`、`fallback_reason`；
没有 fallback 时 `fallback_used = false` 且 `fallback_reason = null`。schema
invalid、provider unavailable 或 policy 拒绝时保留 `unverified`/`unmapped`，不能
升级 Gate。
固定 mapping output schema 为 `{ "links": [{ "mutant_id": string,
"requirement_id": string | null, "intent_id": string | null,
"scenario_id": string | null, "oracle": string | null,
"rationale": string }] }`；输出中的 IDs 必须存在于 bounded context 中，
否则整次 model mapping 不采纳。首个 offline path 默认不调用模型。

## 真实项目验证

仓库内提供一个最小可重复 `examples/v04-sample/`，包含 requirement、enriched
test context、source/tests 和 version-1 mutation report，用于端到端 smoke 和
契约回归；它只证明 workflow 可运行，不证明真实项目效果。真实项目 benchmark
属于 v0.4 release-readiness gate，不是首个 offline implementation slice 的
隐含前提。

真实项目 benchmark harness 必须读取 version `1` manifest。每个 case 至少
包含 case id、repository path、fixed revision、framework、Requirement artifact
path/hash、test artifact path/hash、mutation artifact path/hash、argv command、
clean/dirty-tree observation、ground-truth labels 和带 path/hash 的 adjudication
record。
dirty tree 默认拒绝；只有 manifest 显式记录 `allow_dirty`、状态快照和理由时
才可运行，且不得覆盖或清理原工作树。执行结果、错误、成本/延迟、映射质量
和限制必须写回 case result，并使用 `None` 表示未测量，不把缺失指标写成零。

manifest 的最小结构为：

```json
{
  "schema_version": 1,
  "case_id": "python-checkout-001",
  "repository": {"path": "/path/to/repository", "revision": "REVISION"},
  "framework": "pytest",
  "artifacts": {
    "requirement": {"path": "requirement.md", "sha256": "sha256:..."},
    "test_context": {"path": "test-context.json", "sha256": "sha256:..."},
    "mutation_report": {"path": "mutation-report.json", "sha256": "sha256:..."}
  },
  "argv": ["qa-agent", "assess-effectiveness", "--requirement", "REQ-1",
           "--repository", "/path/to/repository", "--trace-db", "/tmp/case.db",
           "--test-context", "test-context.json", "--mutation-report",
           "mutation-report.json", "--min-score", "0.80", "--format", "json"],
  "allow_dirty": false,
  "working_tree": {"status": "clean", "snapshot_hash": "sha256:...", "reason": null},
  "ground_truth": {
    "survivor_labels": [{"object_id": "M-001", "expected_outcome": "survived",
                         "expected_classification": "relevant", "evidence_ref": "review.json#M-001",
                         "reviewer_decision": "accepted"}],
    "signal_labels": []
  },
  "adjudication": {"status": "resolved", "record": {"path": "review.json", "sha256": "sha256:..."}}
}
```

运行器在执行前重新计算所有 artifact hash 和 repository revision；不匹配就
返回 `decision = incomplete, termination_reason = INSUFFICIENT_EVIDENCE`，不使用
旧结果。`argv` 是可审计的已记录 invocation，不是可由 report/Requirement/model
注入的 shell 指令；harness 只执行固定的 `qa-agent assess-effectiveness` runner
和 manifest 允许的路径/数值参数。`working_tree.status` 只能是 `clean` 或
`dirty`；dirty case 还必须有 `allow_dirty = true`、非空 snapshot_hash 和
reason，且 harness 在执行前后比较 snapshot，绝不覆盖/清理原工作树。
`ground_truth` 的标签至少包含对象 id、
预期 outcome/classification、evidence reference 和 reviewer decision；
`adjudication.status` 只允许 `resolved`、`unresolved`、`not_applicable`；
`resolved` 时 record path/hash 必填，`unresolved` 时不进入 precision/recall
分母。所有 hash 均用 raw artifact bytes 或固定 snapshot serialization 计算。

至少覆盖不同代码结构的 pytest、Playwright/TypeScript 和 AI-generated test
场景；Java/PIT 只有在实际环境与 artifact 可复现时才计入已验证样本。ground
truth 由固定标签和 reviewer adjudication 组成，未标注或存在未解决分歧的 case
不进入 precision/recall 分母。`TP`/`FP`/`FN`、False Positive Rate、Useful
Finding Rate、Survivor Explanation Accuracy、Cost/PR 和 Latency/PR 的计算规则
与 case manifest 一起版本化；不能只报告一个未经定义的 aggregate score。

指标按 case 聚合：`precision = TP / (TP + FP)`、`recall = TP / (TP + FN)`、
`false_positive_rate = FP / (FP + TN)`、`useful_finding_rate = useful_findings /
reported_findings`、`survivor_explanation_accuracy = correctly_explained /
eligible_survivors`；分母为零时记为 `None` 而不是 `1.0`。Cost/PR 和 Latency/PR
只在实际记录 usage/elapsed evidence 时计算。

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

- `packages/qa_agent/test_engineering.py`、`packages/qa_agent/test_engineering_service.py`：
  兼容性增强的 Intent/Scenario/Request 契约；旧 v0.3 workflow 的输出和
  placeholder 行为保持不变。
- `packages/qa_agent/review.py`：向后兼容的 Evidence envelope 扩展和 v0.4
  provenance/redaction metadata。
- `packages/qa_agent/effectiveness.py`：v0.4 context、领域模型、状态、值校验
  和 Mutation Gate。
- `packages/qa_agent/runtime.py`：兼容的 v0.4 budget、permission 和 termination
  policy 字段。
- `packages/qa_agent/mutation_backends.py`：Backend 协议、能力、typed errors 和
  process result。
- `packages/qa_agent/mutation_adapters.py`：offline、mutmut、PIT、Stryker 归一化。
- `packages/qa_agent/effectiveness_service.py`：确定性有效性循环、mapping、
  score、signals、verification 和 gate。
- `packages/qa_agent/trace_store.py`：v0.4 trace 持久化。
- `packages/qa_agent/cli.py`：effectiveness CLI 和 eval version routing。
- `packages/qa_agent/model_runtime.py`：复用 provider-neutral runtime，增加或
  透传 v0.4 mapping 所需的 fallback metadata；不新增 provider-specific 业务
  adapter。
- `packages/qa_agent/evals.py`、`evals/v04/`：v0.4 正例/负例/歧义/对抗评测；
  `evals/test_quality/` 中的 v0.1 资产不混入 v0.4 默认 PR review。
- `tests/test_effectiveness.py`、`tests/test_effectiveness_service.py`、
  `tests/test_mutation_backends.py`、`tests/test_mutation_adapters.py`、
  `tests/test_trace_store_v04.py`、`tests/test_cli_effectiveness.py`、
  `tests/test_v04_evals.py` 和 `tests/fixtures/v04/`：分别覆盖 domain/gate、
  loop service、backend/adapter contracts、SQLite migration、CLI、eval 和
  固定/对抗输入；Model Runtime 的 mapping/fallback contract 追加到
  `tests/test_model_runtime.py`。
- `examples/v04-sample/`：包含 requirement、test context、source/tests 和
  mutation report 的可重复 reference workflow。
- `docs/v0.4-engineering/REAL_PROJECT_VALIDATION.md`：真实项目 benchmark 的
  输入、结果、限制和 evidence 记录格式。
- `docs/v0.3-engineering/README.md`、`DOMAIN_MODEL.md`：记录向后兼容的语义
  增强和 v0.4 入口关系；根 README、roadmap、CHANGELOG 只在实现进入对应
  状态时同步，不提前声称 v0.4 已可执行。
- `docs/v0.4-engineering/`：同步后的 scope、plan、domain、loop、adapter、
  evidence、model、eval、security 和 backlog。

该文件只冻结设计边界；它不代表上述实现已经完成。
