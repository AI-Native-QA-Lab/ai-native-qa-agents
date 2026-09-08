# v0.3 — AI 测试工程师

## 目标

在已验证的需求和证据上下文中，生成测试候选、隔离执行并作出可审计的接受或拒绝决定。

## 定位

本版本扩展证据驱动 QA 架构，但不弱化既有契约。

## 活跃 Agent

Test Engineer + Quality Reviewer + Quality Analyst

## 版本循环
`Test intent → generate → parse → compile → execute → review → analyze failure → repair → retry → accept/reject`

## 验证入口

`qa-agent engineer-test --requirement ... --repository ... --trace-db ... --generator-file ...` 只读取本地受限 JSON fixture，并在临时副本执行测试。运行 `qa-agent eval --version v0.3` 验证安全生成、失败候选和不安全路径拒绝。

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
