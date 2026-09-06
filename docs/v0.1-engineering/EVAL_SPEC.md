# Eval Specification — v0.1

## 1. Eval 层级

### Rule Eval
验证单条 deterministic rule。

### Adapter Eval
验证测试发现与解析是否正确。

### Semantic Eval
验证 AI Review 是否产生高价值 Finding。

### Workflow Eval
验证一次完整 review 的输出。

## 2. Dataset 结构

```text
evals/
└── test_quality/
    ├── python/
    │   ├── good/
    │   ├── weak/
    │   ├── fake/
    │   └── ambiguous/
    └── playwright/
        ├── good/
        ├── weak/
        ├── fake/
        └── ambiguous/
```

## 3. Case Schema

```yaml
id: PY-TQ001-001
language: python
framework: pytest

input:
  file: fixture.py

expected:
  findings:
    - rule_id: TQ001
      severity: high

forbidden:
  findings:
    - rule_id: TQ010
```

## 4. Metrics

Rule：

```text
precision
recall
false_positive_rate
```

Semantic：

```text
finding_precision
finding_usefulness
hallucination_rate
evidence_alignment
```

Workflow：

```text
decision_accuracy
evidence_completeness
cost
latency
```

## 5. Human Label

Semantic Eval 最少需要：

```text
2 人 review 一部分 golden cases
```

如果存在 disagreement：

```text
mark ambiguous
```

不要强行生成唯一答案。

## 6. Regression Gate

CI 中：

```text
Rule Precision 不允许下降超过阈值
```

AI Eval：

建议：

```text
先报告趋势，不阻塞所有 PR
```

直到 Dataset 足够稳定。

## 7. Adversarial Cases

必须包含：

- 注释中出现 assert
- dead code assertion
- test name 伪装
- source code prompt injection
- huge irrelevant context
- dynamically generated tests
- framework alias

---

## Agent Loop Eval

Workflow evals must inspect loop traces in addition to final findings.

Metrics:

```text
goal_completion
tool_selection_accuracy
unnecessary_tool_calls
evidence_sufficiency
termination_accuracy
iterations
model_calls
cost
latency
```

Required cases include:

- should stop after deterministic evidence
- should escalate to semantic review
- should not call model when AI is disabled
- should stop on budget exhaustion
- should return insufficient evidence rather than fabricate a finding
