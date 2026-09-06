# Adapter Specification — v0.1

## 1. 目标

Adapter 隔离语言、测试框架和 AI Provider 差异。

Agent / Core 只依赖统一 Contract。

## 2. Adapter 类型

v0.1：

- LanguageAdapter
- TestFrameworkAdapter
- ModelProvider

后续：

- RequirementBackend
- MutationBackend
- ObservabilityBackend
- DefectBackend

## 3. LanguageAdapter

```python
class LanguageAdapter(Protocol):

    name: str

    def detect(self, repo: RepositoryContext) -> DetectionResult:
        ...

    def parse_file(self, path: Path) -> ParsedFile:
        ...

    def find_functions(self, parsed: ParsedFile) -> list[CodeEntity]:
        ...

    def find_calls(self, parsed: ParsedFile) -> list[CallReference]:
        ...

    def find_imports(self, parsed: ParsedFile) -> list[ImportReference]:
        ...
```

v0.1：

```text
PythonLanguageAdapter
TypeScriptLanguageAdapter
```

## 4. TestFrameworkAdapter

```python
class TestFrameworkAdapter(Protocol):

    name: str

    def detect(self, repo: RepositoryContext) -> DetectionResult:
        ...

    def discover_tests(self, repo: RepositoryContext) -> list[TestEntity]:
        ...

    def parse_test(self, path: Path) -> ParsedTestFile:
        ...

    def extract_assertions(self, test: TestEntity) -> list[Assertion]:
        ...

    def extract_mocks(self, test: TestEntity) -> list[MockUsage]:
        ...

    def extract_metadata(self, test: TestEntity) -> TestMetadata:
        ...
```

v0.1：

```text
PytestAdapter
PlaywrightAdapter
```

## 5. Framework Detection

pytest:

- pyproject.toml
- pytest.ini
- requirements*.txt
- test_*.py
- *_test.py

Playwright:

- package.json
- @playwright/test
- playwright.config.*
- *.spec.ts
- *.test.ts

输出：

```yaml
framework: playwright
confidence: 0.98
evidence:
  - package.json
  - playwright.config.ts
```

## 6. Adapter Capability

```yaml
capabilities:
  test_discovery: true
  assertion_extraction: true
  mock_extraction: true
  execution: false
```

后续版本可以增加 execution。

## 7. ModelProvider

```python
class ModelProvider(Protocol):

    name: str

    def capabilities(self) -> ModelCapabilities:
        ...

    def structured_review(
        self,
        request: SemanticReviewRequest
    ) -> SemanticReviewResult:
        ...
```

ModelProvider 不直接接收整个 Repository。

输入只能来自 ContextBuilder。

## 8. Provider Capability

```yaml
tools: false
structured_output: true
max_context_tokens: 200000
```

v0.1 官方支持建议：

- Anthropic
- OpenAI

但 Core 必须允许完全关闭 AI。

## 9. Adapter Registry

建议：

```python
registry.register_language(...)
registry.register_framework(...)
registry.register_model_provider(...)
```

v0.1 可使用代码注册，不需要复杂 Plugin Discovery。

## 10. Adapter Error

统一：

```text
AdapterUnavailable
AdapterDetectionFailed
AdapterParseFailed
UnsupportedProject
```

## 11. Contract Testing

每个 Adapter 必须通过：

```text
adapter contract tests
```

避免 pytest / Playwright 行为不一致。

## 12. 第三方扩展

未来社区 Adapter 应能够独立 package，例如：

```text
qa-agent-adapter-junit
qa-agent-adapter-cypress
```

但 v0.1 先不实现动态插件安装。

---

## Adapter Boundary in the Agent Loop

Adapters are execution dependencies of the Agent Runtime. They must return structured results; they do not control planning, re-planning or termination.

```text
Agent Runtime → Adapter → Structured Result → Observation
```

ModelProvider remains behind Model Runtime and must not mutate AgentState.
