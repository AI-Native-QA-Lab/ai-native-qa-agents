# AI Native QA Agents

[English](README.md) · [工程文档](docs/README.md)

这是一个面向软件交付全生命周期的、公开的、以证据驱动的 AI 原生质量 Agent 参考架构。

项目将 Agent 定义为受控运行时，而不是无限制的模型调用循环：确定性检查负责收集和标准化证据；模型只处理边界明确的推理任务；验证和质量门禁决定结果能否支持最终决策。

## 核心原则

- 证据优先于观点。
- 验证优先于生成。
- 先做确定性分析，再引入模型推理。
- 所有执行都有明确的预算、权限、溯源和停止条件。
- 不绑定语言、测试框架或模型提供商。

## 版本演进

v0.1 从受控测试质量审查循环开始；v0.2–v0.9 逐步加入状态化重规划、修复重试、变异有效性、假设验证、PR 聚合、策略决策、生产反馈与知识沉淀；v1.0 收敛为稳定的通用 Agent Runtime。完整定义见 [路线图](ROADMAP_AND_VERSION_DESIGN.md)。

当前仓库处于“文档先行”的工程蓝图阶段，尚未声明生产实现已完成。每个版本包都包含架构、实施计划、领域模型、Agent Loop、Adapter、Evidence 与 Gate、Model Runtime、Eval、安全边界和 Issue Backlog。

从 [v0.1 工程包](docs/v0.1-engineering/README.md) 开始；它聚焦 Python/pytest 和 TypeScript/Playwright 仓库的证据驱动测试质量审查。

## v0.1 快速开始

```bash
python -m pip install .
qa-agent detect .
qa-agent review .
qa-agent review . --format sarif > qa-agent.sarif
qa-agent config show
```

当前实现采用受限的确定性循环：`detect → inspect diff → discover tests → run rules → verify and gate`。它提供全部 15 条 v0.1 静态质量规则、YAML/JSON 配置、Evidence、loop trace 和预算元数据；默认只有 critical 会让 Gate 失败。模型语义审查默认关闭，只有显式注入 Provider 且模型预算大于 0 时才启用。

## 关键文档

- [项目蓝图](PROJECT_BLUEPRINT.md)
- [Agent Runtime 规范](AGENT_RUNTIME_SPEC.md)
- [Model Runtime 规范](MODEL_RUNTIME_SPEC.md)
- [总实施路线图](MASTER_IMPLEMENTATION_ROADMAP.md)
- [完整工程计划](FULL_ENGINEERING_PLAN.md)
- [项目协作规则](AGENTS.md)

## 许可证

本项目采用 [PolyForm Noncommercial License 1.0.0](LICENSE)。允许的用途和条件以许可证全文为准。
