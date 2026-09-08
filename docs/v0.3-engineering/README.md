# v0.3 — AI 测试工程师

## 目标

在已验证的需求和证据上下文中，生成测试候选、隔离执行并作出可审计的接受或拒绝决定。

## 定位

本版本扩展证据驱动 QA 架构，但不弱化既有契约。

## 活跃 Agent

Test Engineer + Quality Reviewer + Quality Analyst

## 版本循环
`Test intent → generate → parse → compile → execute → review → analyze failure → repair → retry → accept/reject`

## 执行契约（0.3.1）

- **默认**：本地临时目录副本 + `python -m pytest`；原仓库只读、不落盘生成补丁。
- **可选**：`--execution-backend docker` 使用 `containers/pytest` 镜像做无网络/只读挂载加固隔离。
- Playwright 在二进制不可用时返回结构化 `INSUFFICIENT_EVIDENCE`，不下载依赖。
- 补丁仅限测试路径；禁止自动应用、自动提交、自动合并。

## 验证入口

`qa-agent engineer-test --requirement ... --repository ... --trace-db ... --generator-file ... [--framework pytest|playwright] [--execution-backend local|docker]`
只读取本地受限 JSON fixture。运行 `qa-agent eval --version v0.3` 验证安全生成、失败候选和不安全路径拒绝。

## 非目标

Mutation、自治生产代码修复、无人值守写入。

## Definition of Done
- Real artifacts can drive the workflow end to end.
- High-impact findings/decisions reference Evidence IDs.
- Agent loop is bounded and traceable.
- Model reasoning is schema-validated and subordinate to Agent Runtime.
- New adapters have contract tests.
- Eval set contains positive, negative, ambiguous and adversarial cases.
- Security boundaries are enforced outside prompts.
