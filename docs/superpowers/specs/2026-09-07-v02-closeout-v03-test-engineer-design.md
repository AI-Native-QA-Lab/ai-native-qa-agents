# v0.2 收尾与 v0.3 AI 测试工程师设计

## 目标与交付顺序

先完成 v0.2 `Requirement Intelligence` 的所有已批准工作流，再在其经验证的追踪、证据、预算和终止契约上实现 v0.3 `AI Test Engineer`。v0.3 不会绕过 v0.2 的 `INSUFFICIENT_EVIDENCE`、显式 SQLite 路径、未验证追踪链接或确定性优先原则。

README 继续以英文作为主入口并保留中文切换链接；从本设计开始，设计、开发和计划类工程文档以中文为主。命令、标识符、配置键、模型名和文件路径不翻译。

## v0.2 收尾范围

v0.2 必须能以本地 Markdown 或离线 GitHub Issue JSON 为输入，依次完成需求分析、受限的代码/测试候选映射和需求感知的 PR 审查。每个高影响结论必须引用 Evidence ID；映射只能产生 `unverified` 链接，除非独立验证器明确验证。缺少需求、证据、受支持输入或必要执行预算时，结果必须终止为 `INSUFFICIENT_EVIDENCE` 或 `BUDGET_EXHAUSTED`，而不是返回推测性通过结论。

现有 `RequirementAnalysisService` 保留确定性规则。扩展它来检测同一对象上互斥的肯定/否定验收条件，并生成带来源证据的冲突 finding/risk。映射器必须将扫描上限、单文件上限、秘密文件拒绝和二进制拒绝作为强制边界；CLI 要将相同预算应用于分析、映射和 `review-pr`，并稳定输出 JSON 与可读报告。`review-pr` 的结果要携带需求证据与已有审查证据，并在无法证明需求上下文时 fail closed。

v0.2 评测集合覆盖正例、负例、歧义、缺失错误路径、矛盾需求、不可验证需求、恶意指令文本和坏映射。所有评测均离线、确定性且不依赖凭据。

## v0.3 架构

v0.3 从一条已持久化的需求开始，先由确定性规划器生成 `TestIntent`、`TestPlan` 和 `TestScenario`，再由注入式 `TestGenerator` 产生只包含测试文件变更的 `GeneratedPatch`。模型运行时只能作为可选、结构化且预算受限的生成来源；没有提供者时，CLI 返回证据不足而不伪造候选测试。

候选补丁的生命周期固定为：`generate → parse → compile → execute → review → analyze failure → repair → retry → accept/reject`。每一步先产生 Observation，再产生 Evidence；门禁依次为 Parse、Compile、Execution、Assertion 和 Reviewer。任何失败、超时、预算耗尽、越界路径、生产文件变更或没有运行证据的断言都会拒绝候选或终止为不足证据。

执行由 `ExecutionBackend` 协议隔离。第一批实现使用受控的本地临时目录：只复制允许的项目文件、只应用测试路径下的补丁、禁止在原仓库写入，并通过 subprocess 超时强制终止。pytest 执行器是必须实现；Playwright 执行器是同一协议下的可检测适配器，在运行时缺少二进制或配置时返回结构化“不支持/证据不足”，不尝试下载依赖。网络隔离、容器和真实外部模型不是本版本的隐式前提。

修复只允许替换同一个候选测试补丁，最多使用显式 `max_repairs`；不能修改生产代码，不能提交、合并、推送或自动写入用户工作区。接受的候选会以补丁、执行结果、审查结果、修复链路和全部 Evidence ID 形式输出；使用者必须显式选择是否应用。

## 数据流与边界

```text
SQLite Requirement + Evidence
  → v0.2 analysis / trace links
  → TestIntent / TestPlan / TestScenario
  → GeneratedPatch (test files only)
  → isolated ExecutionBackend
  → ExecutionResult + evidence
  → reviewer + gates
  → accepted | rejected | INSUFFICIENT_EVIDENCE | BUDGET_EXHAUSTED
```

领域模型与执行协议放在 `packages/qa_agent/`；CLI 只负责编排、参数验证和序列化。真实命令只能由明确选择的执行后端运行，且其命令、工作目录、超时和退出结果全部记录为证据。适配器不拥有重试、权限、终止或模型选择权。

## 错误处理与安全

- 需求文本、Issue 内容、生成内容和测试输出均是不可信输入，不能当作运行指令。
- 补丁路径必须相对、位于允许的测试根目录、无 `..`、无绝对路径，且不得修改已有生产路径。
- 无法解析补丁、无法识别测试框架、超时、执行器不可用和缺少结果证据均是显式终止状态。
- 所有动作受 `ExecutionBudget`、文件大小、文件数量、工具调用、模型调用、执行次数和修复次数限制。
- v0.3 默认不接入网络、不保存凭据、不调用模型、不提交 Git，也不自动应用生成补丁。

## 验证策略

每个行为以 pytest 的 RED→GREEN 循环实现。v0.2 完成后运行定向单元/CLI/评测测试、完整 `pytest -q`、`qa-agent eval`、`qa-agent eval --version v0.2`、Markdown 链接检查和 `git diff --check`。v0.3 在同样的完整回归基础上新增生成、路径拒绝、编译/执行、超时、修复预算、生产文件保护和端到端离线工作流测试，并在实现阶段加入 `qa-agent eval --version v0.3`。

## 非目标

本次不实现 Mutation、Jira 默认集成、Neo4j、无人值守生产代码修复、自动应用补丁、自动提交/合并/发布、隐式网络访问、依赖下载或非确定性的默认模型调用。
