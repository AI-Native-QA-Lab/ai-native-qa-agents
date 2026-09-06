# Evidence Specification — v0.1

## 1. 目的

Evidence 是 AI Native QA Agents 的核心。

任何高价值 QA 判断都应该尽可能回答：

> 这个结论是基于什么事实得出的？

## 2. Evidence Schema

```yaml
id: EV-001
type: test_source
status: verified

source:
  provider: repository
  uri: tests/refund.spec.ts

subject:
  type: test
  id: refund-timeout

location:
  path: tests/refund.spec.ts
  line_start: 80
  line_end: 96

metadata:
  framework: playwright
  language: typescript

content_hash: sha256:...

created_at: 2026-09-04T00:00:00Z
```

## 3. Evidence Type

v0.1：

- repository_file
- git_diff
- code_entity
- test_source
- assertion
- mock
- test_metadata
- static_rule_match
- ai_semantic_review

后续版本预留：

- requirement
- test_execution
- coverage
- mutation
- bug
- log
- metric
- trace
- release

## 4. Evidence Status

```text
verified
partially_verified
unverified
contradicted
```

规则：

- 静态解析得到的 AST 事实通常为 `verified`
- LLM 独立语义判断默认不得高于 `partially_verified`
- 无工具证据支撑的推断为 `unverified`

## 5. Evidence Provenance

必须记录：

- provider
- source path / URI
- location
- hash
- timestamp
- extractor / detector

示例：

```yaml
provenance:
  extractor: pytest-adapter
  version: 0.1.0
```

## 6. Finding 与 Evidence

```yaml
finding:
  id: F-001
  rule_id: TQ010
  title: Status-only API assertion
  evidence:
    - EV-012
    - EV-013
```

禁止：

```yaml
finding:
  title: This test is fake
  evidence: []
```

除非：

```yaml
verification_status: unverified
```

## 7. Evidence Integrity

推荐：

```text
SHA-256
```

用于：

- 防止分析后文件变化导致引用失效
- Cache Key
- Eval reproducibility

## 8. Evidence Bundle

一次 review 产生：

```json
{
  "review_id": "REV-123",
  "evidence": [],
  "findings": [],
  "decision": {}
}
```

JSON 输出必须包含 Evidence。

## 9. Evidence Completeness

可以计算：

```text
evidence_completeness =
findings_with_evidence / total_findings
```

v0.1 默认要求：

```text
>= 0.95
```

AI-only finding 如果没有结构证据，必须清晰标记。

## 10. 后续兼容性

Evidence ID 和 Type 一旦公开发布，应保持向后兼容。

Schema 建议携带：

```yaml
schema_version: "1"
```

---

## Evidence in the Agent Loop

Evidence is produced from observations:

```text
Action → Tool Result → Observation → Evidence
```

Every evidence record should optionally carry loop provenance:

```yaml
loop:
  iteration: 3
  action_id: ACT-007
  observation_id: OBS-008
```

This enables audit and replay of how a finding was reached.
