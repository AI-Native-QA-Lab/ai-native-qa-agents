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

| 版本 | 受控能力 |
| --- | --- |
| v0.1 | 最小受控审查循环 |
| v0.2 | 状态化重规划与上下文扩展 |
| v0.3 | 测试生成、执行、修复与重试 |
| v0.4–v1.0 | 见 [路线图](ROADMAP_AND_VERSION_DESIGN.md) |

当前包装版本为 **0.3.1**，可执行基线覆盖 v0.1 审查、v0.2 需求智能与 v0.3 测试工程。后续版本包在实现前仍以设计为主。

## 快速开始

```bash
python -m pip install .
qa-agent detect .
qa-agent review .
qa-agent review . --format sarif > qa-agent.sarif
qa-agent config show
```

### v0.2 需求智能

```bash
qa-agent analyze-requirement path/to/req.md --trace-db ./trace.db
qa-agent map-coverage --requirement REQ-ID --repository . --trace-db ./trace.db
qa-agent review-pr . --requirement REQ-ID --trace-db ./trace.db
qa-agent eval --version v0.2
```

状态型命令必须显式传入 `--trace-db`；缺少关键证据时终止为 `INSUFFICIENT_EVIDENCE`。

### v0.3 测试工程

```bash
qa-agent engineer-test \
  --requirement REQ-ID \
  --repository . \
  --trace-db ./trace.db \
  --generator-file ./candidate.json
qa-agent eval --version v0.3
```

默认在本地临时工作副本中应用仅测试路径补丁并执行 pytest，不写入原仓库。可选加固隔离：`--execution-backend docker`。不会自动应用补丁或提交。

## 关键文档

- [项目蓝图](PROJECT_BLUEPRINT.md)
- [Agent Runtime 规范](AGENT_RUNTIME_SPEC.md)
- [Model Runtime 规范](MODEL_RUNTIME_SPEC.md)
- [总实施路线图](MASTER_IMPLEMENTATION_ROADMAP.md)
- [完整工程计划](FULL_ENGINEERING_PLAN.md)
- [项目协作规则](AGENTS.md)
- [更新日志](CHANGELOG_CN.md)

## 状态

本仓库已提供至 v0.3.1 的可执行基线，尚非生产发布。

## 许可证

本项目采用 [PolyForm Noncommercial License 1.0.0](LICENSE)。允许的用途和条件以许可证全文为准。
