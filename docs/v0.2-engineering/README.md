# v0.2 — 需求智能

## 目标

将需求、代码与测试纳入可追溯的证据链。该版本的实现以本地 Markdown、离线 GitHub Issue JSON 和显式 SQLite trace store 为基础；缺少关键证据时必须终止为 `INSUFFICIENT_EVIDENCE`。

## 定位

本版本扩展证据驱动 QA 架构，但不弱化既有契约。

## 活跃 Agent

Quality Analyst + Quality Reviewer

## 版本循环
`Requirement → ambiguity/missing info → gather context → testability/risk → re-plan if needed → verify → decision`

## 验证入口

`qa-agent analyze-requirement`、`map-coverage` 和 `review-pr` 均要求显式 `--trace-db`。运行 `qa-agent eval --version v0.2` 验证离线正反例、歧义、冲突、恶意文本和预算终止。

## 非目标

Jira 默认集成、测试生成、Mutation、通用多 Agent 运行时、Neo4j。

## Definition of Done
- Real artifacts can drive the workflow end to end.
- High-impact findings/decisions reference Evidence IDs.
- Agent loop is bounded and traceable.
- Model reasoning is schema-validated and subordinate to Agent Runtime.
- New adapters have contract tests.
- Eval set contains positive, negative, ambiguous and adversarial cases.
- Security boundaries are enforced outside prompts.
