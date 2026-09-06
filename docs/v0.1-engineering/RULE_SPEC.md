# Test Quality Rule Specification — v0.1

## 1. 目标

Rule Engine 用于处理确定性或半确定性的测试质量问题。

原则：

> 能用 AST / 静态规则准确判断的问题，不交给 LLM。

## 2. Rule Schema

```yaml
id: TQ001
version: 1
name: no-assertion
category: test-validity
default_severity: high

languages:
  - python
  - javascript
  - typescript

frameworks:
  - pytest
  - playwright

detector:
  kind: static

message_key: rule.no_assertion

enabled_by_default: true
```

## 3. Rule Interface

```python
class Rule:
    id: str

    def supports(self, context: RuleContext) -> bool:
        ...

    def evaluate(self, context: RuleContext) -> list[Finding]:
        ...
```

## 4. RuleContext

包含：

```text
TestEntity
AST
Assertions
Mocks
Code Location
Framework Metadata
Git Diff Context
```

禁止 Rule 直接访问网络或 AI。

## 5. 第一批规则

### TQ001 no-assertion

测试没有显式或框架隐式验证。

Severity:

```text
high
```

### TQ002 skipped-test

测试被 skip / xfail / disabled。

默认：

```text
medium
```

若 changed code 只有被 skip 测试覆盖，可升级。

### TQ003 empty-test

测试体为空或仅包含 pass / placeholder。

```text
high
```

### TQ004 todo-test

测试只保留 TODO / NotImplemented / pending。

```text
medium
```

### TQ005 always-pass-assertion

例如：

```python
assert True
```

或：

```typescript
expect(true).toBe(true)
```

```text
critical
```

### TQ006 swallowed-exception

测试捕获异常但不 rethrow、不 fail、不 assert。

```text
high
```

### TQ007 excessive-mocking

Mock 数量显著高于行为验证数量。

v0.1 只作为 heuristic：

```text
medium
```

### TQ008 unreachable-assertion

断言位于 return / raise 后不可达路径。

```text
high
```

### TQ009 duplicated-assertion

多个完全相同断言，未增加验证价值。

```text
low
```

### TQ010 status-only-api-assertion

测试只验证 HTTP status，不验证业务响应或状态变化。

```text
medium
```

LLM 可做二次语义增强。

### TQ011 screenshot-only-e2e-test

E2E 只有截图动作，无实际业务断言。

```text
medium
```

### TQ012 sleep-based-test

固定 sleep 代替条件等待。

```text
medium
```

### TQ013 hardcoded-success-path

测试数据和结果过度硬编码，且没有行为验证。

```text
low
```

### TQ014 no-observable-outcome

执行操作后，没有验证 UI / API / DB / state 等可观察结果。

```text
high
```

### TQ015 broad-exception-catch

捕获 `Exception` / `BaseException` / JavaScript 宽泛错误后掩盖失败。

```text
high
```

## 6. Severity Override

用户可配置：

```yaml
rules:
  TQ012:
    severity: low
```

## 7. Rule Suppression

```yaml
ignore:
  - rule: TQ012
    paths:
      - legacy/**
```

v0.1 不建议支持复杂 inline annotation。

## 8. Rule Testing

每条规则必须：

```text
positive fixtures
negative fixtures
edge fixtures
```

最低要求：

```text
5 positive + 5 negative
```

## 9. Rule Eval

规则本身目标：

```text
Precision >= 95%
```

若无法达到，应：

- 降级为 heuristic
- 降低 Severity
- 转移到 Semantic Reviewer

## 10. Rule Versioning

Rule ID 永久稳定。

行为重大变化：

```yaml
version: 2
```

不要改 Rule ID。

---

## Rules in the Agent Loop

Deterministic rules are actions inside the controlled review loop.

Rule results become observations and then evidence. A rule must never independently terminate the Agent Runtime or invoke a model.

```text
RuleRunner
  ↓
Rule Match
  ↓
Observation
  ↓
Evidence
  ↓
Evaluator / Verifier
```

Semantic escalation is decided by runtime policy, not by individual rules.
