# AI Native QA Agents — Project Blueprint

## 1. Repository

```text
ai-native-qa-agents
```

Suggested organization:

```text
AI-Native-QA-Lab/ai-native-qa-agents
```

Description:

> Reference blueprint for building AI-native software quality agents. Includes requirement analysis, test engineering, test quality review, failure investigation and release quality intelligence.

中文：

> 一个面向软件交付全生命周期、以证据驱动的软件质量 Agent 开源参考架构。

---

## 2. Why This Project Exists

Traditional QA tools focus on:

```text
Test Case
Test Script
Test Execution
Test Report
```

Many AI testing tools focus on:

```text
Prompt
  ↓
LLM
  ↓
Generate Tests
```

But real software quality work is:

```text
Requirement
    ↓
Understand
    ↓
Question
    ↓
Risk Analysis
    ↓
Testability
    ↓
Test Strategy
    ↓
Test Design
    ↓
Test Implementation
    ↓
Test Execution
    ↓
Failure Investigation
    ↓
Quality Evaluation
    ↓
Release Decision
    ↓
Production Feedback
```

The project therefore defines the core object as:

```text
Software Quality Agent
```

rather than:

```text
Test Generator
```

---

## 3. Definition of an AI Native QA Agent

An AI Native QA Agent is an agent that uses real engineering context, QA knowledge, tool execution and verifiable evidence to autonomously or semi-autonomously perform software quality tasks.

Core capabilities:

- Context Aware
- Skill Driven
- Tool Enabled
- Evidence Based
- Quality Gated
- Evaluated

---

## 4. Core Architecture

```text
                     QA Orchestrator
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
 Quality Analyst     Test Engineer    Quality Reviewer
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                  Failure Investigator
                           ▼
                    Release Guardian
                           ▼
               Production Quality Agent
```

Underlying system:

```text
Agents
  ├── Skills
  ├── Tools
  ├── Backends
  ├── Adapters
  ├── Evidence
  ├── Quality Gates
  ├── Memory
  ├── Evals
  └── Runtime
```

---

## 5. Core Principles

### Evidence over Opinion

Every important QA claim should map to evidence.

```text
Claim
  ↓
Evidence
  ↓
Verification
  ↓
Decision
```

### Verification over Generation

```text
Generate
   ↓
Execute
   ↓
Verify
   ↓
Challenge
```

Generated tests are not considered complete until verified.

### Context over Prompt

Agent reasoning should use:

- Requirement
- Git Diff
- Source
- Tests
- CI
- Bugs
- Logs
- Metrics

rather than an oversized prompt.

### Human Control over Blind Autonomy

Default permissions:

```text
READ      → automatic
ANALYZE   → automatic
EXECUTE   → configurable
WRITE     → human approval
RELEASE   → human approval
```

---

## 6. Agent Definitions

### Quality Analyst

Purpose:

> Testing before testing.

Capabilities:

- Requirement Analysis
- Acceptance Criteria Review
- Testability Analysis
- Risk Analysis
- Change Impact Analysis
- Test Scope Analysis
- Test Strategy
- Test Planning

### Test Engineer

Capabilities:

- Test Design
- Unit Test Generation
- API Test Generation
- E2E Test Generation
- Contract Test Generation
- Test Data Generation
- Test Execution

### Quality Reviewer

Purpose:

> Test the tests.

Capabilities:

- Fake Test Detection
- Weak Assertion Detection
- Over Mocking
- Always-pass Detection
- Missing Business Oracle
- Test Effectiveness Review
- AI-generated Test Verification

### Failure Investigator

Capabilities:

- Failure Classification
- Evidence Gathering
- Root-cause Hypothesis
- Supporting / Contradicting Evidence
- Next Investigation Steps

### Release Guardian

Capabilities:

- Release Risk
- Evidence Completeness
- Requirement Coverage
- Test Effectiveness
- Known Defect Risk
- GO / GO_WITH_RISK / NO_GO / INSUFFICIENT_EVIDENCE

### Production Quality Agent

Capabilities:

- Incident Analysis
- Regression Gap Detection
- Production-to-Test Feedback
- Quality Knowledge Accumulation

---

## 7. Backend Architecture

Abstract backends:

```text
RequirementBackend
RepositoryBackend
TestBackend
ExecutionBackend
CoverageBackend
MutationBackend
DefectBackend
ObservabilityBackend
ReleaseBackend
```

Example adapters:

```text
GitHub / GitLab / Local Git
Jira / GitHub Issues / Markdown
pytest / JUnit / Jest
Playwright / Cypress / Selenium
PIT / mutmut / Stryker
Grafana / Datadog / OpenTelemetry
```

The Agent Core must not directly bind to vendor systems.

---

## 8. Evidence Model

Example:

```yaml
id: EV-001
type: test_execution
status: verified

source:
  provider: github-actions
  run_id: 19283

subject:
  type: requirement
  id: REQ-123

result:
  status: passed
```

Evidence types evolve over time:

```text
requirement
acceptance_criteria
code
git_diff
test
test_execution
coverage
mutation
bug
incident
log
metric
trace
release
```

---

## 9. Quality Gates

Core gates:

- Evidence Gate
- Execution Gate
- Assertion Gate
- Requirement Gate
- Mutation Gate
- Release Gate

Example:

```text
No Evidence
→ Cannot claim VERIFIED
```

```text
Generated Test Never Executed
→ GENERATED_NOT_VERIFIED
```

```text
Critical Requirement Uncovered
→ HIGH_RELEASE_RISK
```

---

## 10. AI Integration Strategy

Do not use:

```text
Everything → LLM
```

Use:

### Deterministic Layer

- AST
- Static Rules
- Git Diff
- Test Discovery
- Coverage
- Mutation
- Execution Result Parsing

### AI Reasoning Layer

- Requirement Understanding
- Semantic Assertion Review
- Business Oracle Analysis
- Risk Reasoning
- Failure Hypothesis
- Test Recommendation

### Agent Layer

- Planning
- Skill Selection
- Tool Selection
- Evidence Gathering
- Verification
- Decision Composition

---

## 11. Multi-language Design

Language-independent core:

```text
Requirement
Risk
Evidence
Finding
Gate
Decision
```

Language adapters:

```text
python
typescript
javascript
java
go
csharp
rust
```

Initial support:

```text
Python
TypeScript
```

---

## 12. Framework Adaptation

Unified adapter contract:

```text
detect()
discover_tests()
parse_test()
extract_assertions()
extract_mocks()
run_test()
parse_result()
get_coverage()
```

Initial frameworks:

```text
pytest
Playwright
```

Later:

```text
Jest
Vitest
JUnit
Cypress
Selenium
REST Assured
Postman
k6
JMeter
Gatling
```

---

## 13. Chinese / English

Core logic is locale-neutral.

Configuration:

```yaml
locale:
  input: auto
  output: zh-CN
```

or:

```yaml
locale:
  output: en-US
```

Rules use message keys:

```yaml
message_key: rule.no_assertion
```

Translations:

```text
locales/en-US.yaml
locales/zh-CN.yaml
```

Do not maintain separate Chinese and English agent logic.

---

## 14. AI Provider Adaptation

Unified interface:

```text
ModelProvider
```

Potential providers:

- Anthropic
- OpenAI
- Google
- Azure OpenAI
- AWS Bedrock
- Local Models

Core must not directly depend on one provider.

---

## 15. Role-based Usage

### QA Engineer

- Requirement analysis
- Test design
- Test review
- Failure investigation

### SDET / Automation QA

- Test quality
- Mutation
- Generated test verification
- Flaky pattern analysis

### Developer

- PR review
- Missing test identification
- Weak test detection

### QA Lead

- Risk
- Coverage
- Quality gate
- Release confidence

### PM / BA

- Testability
- Acceptance Criteria review

### DevOps

- CI integration
- Release gate
- Evidence collection

### Engineering Manager

- Quality trend
- Risk concentration
- Release intelligence

---

## 16. Relationship with awesome-qa-skills

```text
awesome-qa-skills
=
QA Knowledge / Skill Registry
```

```text
ai-native-qa-agents
=
Agent Runtime / Tools / Evidence / Gates / Orchestration
```

Relationship:

```text
QA Knowledge
    ↓
Skills
    ↓
Agents
    ↓
Tools + Backends
    ↓
Evidence
    ↓
Quality Decision
```

---

## 17. Long-term Vision

```text
Requirement
    ↓
Quality Analyst
    ↓
Risk Intelligence
    ↓
Test Engineer
    ↓
Quality Reviewer
    ↓
Execution
    ↓
Failure Investigator
    ↓
Release Guardian
    ↓
Production Quality
    ↓
Quality Knowledge
    ↓
Next Change
```

Final positioning:

> Quality is not a testing phase. Quality becomes an intelligent, continuous and evidence-driven part of software delivery.

---

## Agent Runtime & Agent Loop

The core architecture contains two separate runtimes:

```text
QA Task
  ↓
Agent Runtime
  ├── Understand
  ├── Plan
  ├── Act
  ├── Observe
  ├── Evaluate
  ├── Re-plan
  ├── Verify
  ├── Gate
  └── Decide / Stop
        │
        └── AI reasoning → Model Runtime → Provider
```

The loop is evidence-driven and bounded by `ExecutionBudget` and `TerminationPolicy`.

Core runtime models:

- AgentState
- Observation
- LoopTrace
- ExecutionBudget
- TerminationReason

The v0.1 reviewer uses a constrained deterministic loop. More autonomous re-planning is introduced only when concrete QA workflows require it.
