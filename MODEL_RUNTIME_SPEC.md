# Model Runtime Specification

## 1. Purpose

`Model Runtime` is the abstraction layer between QA Agents and concrete AI providers.

Core principle:

```text
Task → Capability → Model
```

not:

```text
Agent → Hard-coded Model
```

## 2. Architecture

```text
QA Agent
   │
   ▼
Skill / Workflow
   │
   ▼
AI Reasoning Task
   │
   ▼
ModelRequest
   │
   ▼
Model Runtime
   │
   ├── Capability Check
   ├── Task Router
   ├── Model Policy
   ├── Fallback
   ├── Retry / Timeout
   ├── Structured Output Validation
   ├── Cost / Usage Tracking
   └── Observability
   │
   ▼
Provider Adapter
   │
   ├── OpenAI
   ├── Anthropic
   ├── Google
   ├── Azure OpenAI
   ├── AWS Bedrock
   └── OpenAI-compatible / Local
```

## 3. ModelRequest

Agents must not construct provider-specific requests.

```python
class ModelRequest(BaseModel):
    task_type: str
    system_instruction: str | None = None
    messages: list["Message"]
    output_schema: dict | None = None
    tools: list["ToolDefinition"] = []
    tier: str | None = None
    required_capabilities: set[str] = set()
    preferred_capabilities: set[str] = set()
    temperature: float | None = None
    max_output_tokens: int | None = None
    metadata: dict = {}
```

Example:

```yaml
task_type: semantic_test_review
tier: reasoning
required_capabilities:
  - structured_output
preferred_capabilities:
  - long_context
```

## 4. ModelResponse

```python
class ModelResponse(BaseModel):
    provider: str
    model: str
    content: str | None = None
    structured_output: dict | None = None
    tool_calls: list["ToolCall"] = []
    finish_reason: str | None = None
    usage: "ModelUsage"
    latency_ms: int | None = None
```

```python
class ModelUsage(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None
    cached_tokens: int | None = None
    estimated_cost: float | None = None
```

## 5. Provider Contract

```python
class ModelProvider(Protocol):
    @property
    def provider_name(self) -> str:
        ...

    def capabilities(self, model: str) -> "ModelCapabilities":
        ...

    def invoke(self, model: str, request: ModelRequest) -> ModelResponse:
        ...
```

Core code must never depend directly on provider SDK types.

## 6. Model Capabilities

```python
class ModelCapabilities(BaseModel):
    structured_output: bool = False
    tool_calling: bool = False
    vision: bool = False
    reasoning: bool = False
    code_generation: bool = False
    supports_system_prompt: bool = True
    supports_streaming: bool = True
    max_context_tokens: int | None = None
```

## 7. Model Tiers

Recommended logical tiers:

```text
FAST
BALANCED
REASONING
CODING
```

Example:

```yaml
model_tiers:
  fast:
    provider: openai
    model: ${QA_FAST_MODEL}

  balanced:
    provider: anthropic
    model: ${QA_BALANCED_MODEL}

  reasoning:
    provider: anthropic
    model: ${QA_REASONING_MODEL}

  coding:
    provider: openai
    model: ${QA_CODING_MODEL}
```

## 8. Task-based Routing

Prefer task-level routing:

```yaml
ai:
  tasks:
    semantic_test_review:
      tier: reasoning

    requirement_analysis:
      tier: reasoning

    test_generation:
      tier: coding

    report_summary:
      tier: fast
```

A single Agent can use multiple model tiers.

## 9. Capability Router

```text
ModelRequest
   ↓
Required Capabilities
   ↓
Candidate Models
   ↓
Capability Check
   ↓
Policy Check
   ↓
Model Selection
```

## 10. Capability Degradation

Supported modes:

### Strict

```text
MODEL_CAPABILITY_NOT_SUPPORTED
```

### Emulated

```text
Structured Output
→ JSON prompt
→ Parser
→ Pydantic Validation
```

### Fallback

Route to another compatible model.

Recommended default:

```text
Strict + Configurable Fallback
```

Silent degradation should be avoided.

## 11. Structured Output

Schema-first QA output:

```python
class SemanticTestReview(BaseModel):
    test_intent: str
    oracle_quality: Literal["strong", "medium", "weak"]
    requirement_verified: bool | None = None
    findings: list["SemanticFinding"]
    confidence: float
```

Runtime:

```text
Model
  ↓
Structured Output
  ↓
Schema Validation
  ↓
Valid?
 ├── yes → continue
 └── no → repair once → fallback / fail
```

## 12. Prompt Architecture

Maintain one canonical prompt per task.

```text
prompts/
  semantic_test_review/
    canonical.md
    openai.override.md
    anthropic.override.md
```

Recommended:

```text
80% canonical behavior
20% provider-specific optimization
```

## 13. Tool Calling

Canonical tool:

```yaml
name: read_test
input_schema:
  type: object
  properties:
    path:
      type: string
```

Canonical return:

```python
class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict
```

Provider adapters translate to native formats. The model never owns GitHub, Jira or CI credentials.

## 14. Local / Enterprise Models

Support an `OpenAICompatibleProvider` where practical.

```yaml
providers:
  internal:
    type: openai-compatible
    base_url: ${QA_MODEL_BASE_URL}
    api_key_env: QA_INTERNAL_MODEL_KEY
```

Useful for internal gateways, vLLM, Ollama-compatible gateways and enterprise proxies.

## 15. Fallback

Separate:

- Technical Fallback: timeout, rate limit, provider outage, transport failure
- Quality Fallback: invalid structured output, unsupported capability, repeated validation failure

Fallback metadata must be observable.

## 16. Model Policy / Governance

```yaml
ai:
  policy:
    allow_providers:
      - azure_openai
      - internal

    deny_external_models: true
    source_code_external_upload: false
    pii_redaction: true
```

The router must enforce policy before provider invocation.

## 17. Model Evaluation

Provider integration requires:

```text
Provider Contract Test
Capability Test
QA Golden Dataset Eval
```

Potential command:

```bash
qa-agent eval models
```

Metrics:

```text
Precision
Recall
False Positive Rate
Evidence Alignment
Schema Success Rate
Cost
Latency
```

This can evolve into a `QA Agent Model Benchmark`.

## 18. Cost Control

Track:

```text
input tokens
output tokens
cached tokens
estimated cost
latency
```

Later routing policies may include:

```text
quality-first
cost-first
latency-first
balanced
```

## 19. Observability

Example invocation record:

```yaml
task_type: semantic_test_review
provider: anthropic
model: xxx
tier: reasoning
latency_ms: 1820
input_tokens: 4310
output_tokens: 620
fallback_used: false
schema_valid: true
```

Do not log prompts containing secrets.

## 20. Security

Integrate with ContextBuilder and security policy:

- secret redaction
- repository content treated as untrusted
- model upload policy
- token budget
- file allow/deny
- no credential exposure
- provider data handling controls

## 21. Directory Structure

```text
packages/
  qa_model_runtime/
    request.py
    response.py
    capabilities.py
    runtime.py
    router.py
    policy.py
    registry.py
    usage.py
    errors.py

adapters/
  models/
    openai/
    anthropic/
    google/
    azure_openai/
    bedrock/
    openai_compatible/

prompts/
  semantic_test_review/
  requirement_analysis/
  failure_investigation/
  test_generation/

evals/
  models/
```

## 22. Version Evolution

### v0.1

Implement:

```text
ModelProvider Contract
ModelRequest / ModelResponse
Structured Output Validation
AI On / Off
OpenAI Adapter
Anthropic Adapter
Basic Usage Tracking
```

### v0.2–v0.3

Add:

```text
Model Capabilities
Model Tier
Task-based Routing
OpenAI-compatible Provider
Basic Fallback
```

### v0.4+

Add:

```text
Model Benchmark
Cost / Quality Comparison
Routing Policies
Quality Fallback
```

### v0.7+

Add:

```text
Enterprise Model Governance
Provider Allow/Deny Policy
Data Residency Policy
Internal-only Routing
```

## 23. Design Rule

```text
Agents express WHAT capability they need.

Model Runtime decides HOW and WHERE that capability is fulfilled.
```

QA Agent must never become coupled to GPT, Claude, Gemini or any provider-specific API.

---

## Agent Runtime Boundary

`Model Runtime` is subordinate to `Agent Runtime`.

```text
Agent Runtime
   ↓
AI Reasoning Task
   ↓
Model Runtime
   ↓
Provider
```

Model Runtime must not:

- decide whether the QA goal is complete
- own loop termination
- bypass tool permissions
- mutate AgentState directly
- turn provider tool calls into unrestricted execution

It returns normalized reasoning results to the Agent Runtime, which evaluates them alongside deterministic observations and evidence.
