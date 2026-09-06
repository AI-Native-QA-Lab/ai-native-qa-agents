# Security Model — v0.1

## 1. 威胁模型

主要风险：

- Repository Prompt Injection
- Secret Leakage
- Malicious File Content
- Excessive Context Upload
- Unsafe Command Execution
- CI Secret Exposure
- Third-party Model Provider Data Handling

## 2. Repository Content

所有 repository 文件都视为：

```text
untrusted data
```

不能作为 Agent instruction。

## 3. Secret Redaction

默认排除：

```text
.env
.env.*
*.pem
*.key
credentials*
secrets*
```

并对内容执行常见 token pattern redaction。

## 4. AI Context

只允许 ContextBuilder 产生模型输入。

禁止 Adapter / Rule 直接向 ModelProvider 发送文件。

## 5. Size Limit

建议：

```text
single file <= configurable limit
review context <= configurable token budget
```

## 6. CI

Fork PR：

```text
默认关闭需要 protected secret 的 AI Semantic Review
```

但 deterministic review 仍可运行。

## 7. Command Execution

v0.1 不需要运行用户测试，因此默认不执行 repository command。

后续 v0.3 引入 sandbox。

## 8. Logging

禁止输出：

- token
- provider credential
- full secret value
- raw `.env`

## 9. Telemetry

默认：

```text
off
```

如果未来增加，必须显式 opt-in。

---

## Agent Loop Security

The Agent Runtime is a security boundary.

It must enforce:

- maximum iterations
- maximum tool/model calls
- time and cost budget
- action permission checks
- no instructions sourced from repository content
- no recursive unrestricted tool loop
- no WRITE/RELEASE action without required approval

Model output is a proposal/observation input, not executable authority.
