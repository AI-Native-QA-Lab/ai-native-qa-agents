# AI Native QA Agents — Detailed Roadmap & Version Design

## Version Strategy

```text
v0.1  PR Quality Reviewer
v0.2  Requirement Intelligence
v0.3  AI Test Engineer
v0.4  Test Effectiveness & Mutation
v0.5  Failure Investigator
v0.6  CI / Pull Request Agent
v0.7  Release Guardian
v0.8  Production Quality Agent
v0.9  Quality Knowledge Graph
v1.0  AI Native QA System
```

The evolution follows:

```text
Observe
  ↓
Understand
  ↓
Generate
  ↓
Verify
  ↓
Investigate
  ↓
Integrate
  ↓
Decide
  ↓
Learn
  ↓
Remember
```

---

# v0.1 — PR Quality Reviewer

## Goal

Evidence-driven review of existing tests and changed code.

## Scope

- Local Git
- Python + pytest
- TypeScript + Playwright
- Git Diff
- Test Discovery
- Rule Engine
- Optional Semantic Review
- Evidence
- Findings
- Quality Gate
- Human / JSON / SARIF
- GitHub Action prototype

## Non-goals

- Test Generation
- Mutation
- Jira
- Multi-Agent
- Release Guardian
- Knowledge Graph

## Core Architecture

```text
CLI
 ↓
Repository Scanner
 ↓
Language / Framework Detection
 ↓
Git Diff Analyzer
 ↓
Test Discovery
 ↓
Rule Engine + Optional Semantic Reviewer
 ↓
Evidence Builder
 ↓
Finding Aggregator
 ↓
Gate
 ↓
Report
```

## Acceptance

- real repository analysis
- pytest + Playwright support
- 10–15 deterministic rules
- evidence-backed findings
- JSON + SARIF
- AI disabled mode
- 80+ eval cases
- GitHub Action smoke

## Estimated Schedule

8 weeks.

---

# v0.2 — Requirement Intelligence

## Goal

Move from:

```text
Code ↔ Test
```

to:

```text
Requirement ↔ Code ↔ Test
```

## Add

- Quality Analyst Agent
- Requirement Schema
- Acceptance Criteria Review
- Testability Analysis
- Risk Analysis
- Test Scope
- Markdown Requirement Adapter
- GitHub Issue Adapter
- lightweight traceability store

## Initial Storage

SQLite.

Do not introduce Neo4j yet.

## CLI

```bash
qa-agent analyze-requirement requirement.md
qa-agent map-coverage
qa-agent review-pr --requirement GH-123
```

## Acceptance

- Markdown and GitHub Issue supported
- Testability report
- Risk report
- Requirement ↔ Code ↔ Test mapping
- unsupported claims marked unverified

## Schedule

6–8 weeks.

---

# v0.3 — AI Test Engineer

## Goal

Generate tests only after the project has Reviewer + Evidence + Requirement context.

## Workflow

```text
Requirement
 ↓
Risk
 ↓
Existing Tests
 ↓
Test Design
 ↓
Candidate Test
 ↓
Generate
 ↓
Compile
 ↓
Execute
 ↓
Quality Review
 ↓
Accept / Reject
```

## Add

- Test Plan Schema
- TestGenerator Contract
- Change Proposal
- Human Approval
- Execution Gate
- Assertion Gate
- Reviewer Gate
- isolated execution

## Security

Use temporary worktree or Docker isolation.

## Acceptance

- Requirement → Test Plan
- Test Plan → pytest / Playwright test
- generated tests execute
- generated tests reviewed
- no auto-commit by default
- production code is never silently changed

## Schedule

8–10 weeks.

---

# v0.4 — Test Effectiveness & Mutation

## Goal

Solve:

```text
Test Exists ≠ Test Works
```

## Add

MutationBackend.

Adapters:

```text
Python → mutmut
Java → PIT
JavaScript/TypeScript → Stryker
```

## Effectiveness Signals

- Execution
- Assertion Quality
- Requirement Relevance
- Mutation

Example:

```yaml
score: 78
components:
  execution: 100
  assertion: 70
  requirement: 80
  mutation: 65
```

## Fake Test Detection

Use multi-signal evidence:

```text
static rule
semantic review
execution
mutation
requirement mapping
```

Do not rely on one opaque AI probability.

## Acceptance

- mutation adapters
- normalized mutation evidence
- effectiveness score
- fake-test multi-signal classification
- configurable threshold

## Schedule

6–8 weeks.

---

# v0.5 — Failure Investigator

## Goal

Classify and investigate test failures with evidence.

## Inputs

- Test result
- Logs
- Git Diff
- Test Source
- Production Source

## Hypothesis Model

Must include:

- supporting evidence
- contradicting evidence
- confidence
- next checks

## Result Adapters

- pytest
- JUnit XML
- Playwright JSON
- Jest
- Allure results

## Acceptance

- failure classification
- evidence-backed hypothesis
- unknown state supported
- no forced root cause

## Schedule

6–8 weeks.

---

# v0.6 — CI / Pull Request Agent

## Goal

Move from local developer tool to team workflow.

## Add

- GitHub Action
- Job Summary
- PR Summary
- SARIF
- Baseline
- Suppression
- Configurable Gate

## Baseline

```bash
qa-agent baseline create
```

Then only report new findings.

## Security

Fork PRs must not expose protected AI secrets.

## Acceptance

- GitHub Action
- summary
- SARIF
- baseline
- suppression
- fork safety
- configurable gate

## Schedule

6 weeks.

---

# v0.7 — Release Guardian

## Goal

Aggregate quality evidence into release recommendation.

## Inputs

- Requirement Coverage
- Change Risk
- Tests
- Coverage
- Mutation
- Bugs
- Performance
- Security

## Recommendations

```text
GO
GO_WITH_RISK
NO_GO
INSUFFICIENT_EVIDENCE
```

The last state is mandatory.

## Human Control

Agent recommends; humans decide.

## Acceptance

- Release Policy Engine
- Evidence Aggregation
- Evidence Completeness
- Release Recommendation
- Human Approval
- Release Report

## Schedule

6–8 weeks.

---

# v0.8 — Production Quality Agent

## Goal

Connect software delivery with production quality.

## Add

ObservabilityBackend:

```text
query_logs
query_metrics
query_traces
get_incident
```

Initial adapters:

- OpenTelemetry
- Generic JSON Logs

Later:

- Grafana
- Datadog

## Feedback Loop

```text
Incident
 ↓
Failure Pattern
 ↓
Related Code
 ↓
Related Requirement
 ↓
Missing Test
 ↓
Regression Test Proposal
```

## Acceptance

- production incident ingestion
- logs / trace evidence
- code/test mapping
- test-gap detection
- regression proposal
- human confirmation

## Schedule

8 weeks.

---

# v0.9 — Quality Knowledge Graph

## Goal

Persist relationships among:

```text
Requirement
Code
Test
Execution
Mutation
Finding
Bug
Incident
Release
```

## Nodes

- Requirement
- AcceptanceCriterion
- SourceFile
- CodeEntity
- Test
- Execution
- Mutation
- Bug
- Incident
- Release

## Edges

- IMPLEMENTS
- VERIFIED_BY
- EXECUTED_IN
- FAILED_IN
- DETECTED
- CAUSED_BY
- RELATED_TO
- INTRODUCED_BY
- FIXED_BY

## Storage

Start with graph abstraction.

Optional Neo4j adapter.

## Acceptance

Answer questions like:

- Which incidents have no regression tests?
- Which requirements have weak test effectiveness?
- Which modules repeatedly produce high-risk defects?
- Which tests survive mutation over time?

## Schedule

8–10 weeks.

---

# v1.0 — AI Native QA System

## Goal

Stabilize the core abstractions, not merely add more features.

## Stable Contracts

- QAAgent
- Skill
- Tool
- Backend
- Adapter
- Evidence
- Finding
- Gate
- Eval
- Permission

## Orchestration

```text
Task
 ↓
Context
 ↓
Select Agent / Skill / Tool
 ↓
Collect Evidence
 ↓
Verify
 ↓
Apply Gates
 ↓
Human-facing Decision
```

## Permission Model

```text
READ
ANALYZE
EXECUTE
WRITE
RELEASE
```

Default:

```text
READ + ANALYZE → automatic
EXECUTE → configurable
WRITE + RELEASE → approval
```

---

# Language Roadmap

```text
v0.1 Python + TypeScript
v0.3 JavaScript
v0.4 Java
v0.6 Go
later C# / Rust
```

---

# Framework Roadmap

Initial:

```text
pytest
Playwright
```

Then:

```text
Jest
Vitest
JUnit
Cypress
Selenium
REST Assured
```

Performance frameworks later:

```text
k6
JMeter
Gatling
```

Potentially as a dedicated Performance Quality Agent.

---

# AI Cost Strategy

Always prefer:

```text
Diff first
Rules first
AST first
Relevant context only
Cache
LLM only when needed
```

Never send the entire repository by default.

---

# Project KPIs

Measure:

- False Positive Rate
- Finding Acceptance Rate
- Generated Test Acceptance Rate
- Mutation Score
- Requirement Coverage Accuracy
- Failure Diagnosis Accuracy
- Cost per Review
- Review Duration

Success is not:

```text
Generated 100 tests
```

Success is:

```text
Found important gaps
Prevented fake tests
Reduced review effort
Improved test effectiveness
Produced explainable decisions
```


---

## Model Runtime Evolution

```text
v0.1
Provider Contract
+ OpenAI / Anthropic
+ Structured Output
+ AI On/Off
+ Usage Tracking

v0.2-v0.3
Capabilities
+ Model Tier
+ Task-based Routing
+ OpenAI-compatible Local Model
+ Basic Fallback

v0.4+
Model Benchmark
+ Cost / Quality Comparison
+ Quality Fallback

v0.7+
Enterprise Governance
+ Provider Allow/Deny
+ Data Residency
+ Internal-only Routing
```

---

## Agent Loop Evolution

Agent Loop evolves with the QA capability rather than being implemented as a generic autonomous runtime on day one.

```text
v0.1  Minimal Controlled Review Loop
      AgentState + Observation + Budget + Termination + Verify

v0.2  Stateful Re-plan
      Open Questions + Context Expansion + Requirement Gathering

v0.3  Repair Loop
      Generate → Compile → Execute → Analyze → Repair → Retry

v0.5  Hypothesis Loop
      Hypothesis → Evidence → Challenge → Refine → Verify

v0.7  Policy-aware Decision Loop
      Evidence Completeness → Release Policy → Human Approval

v1.0  Stable Generic Agent Runtime
```

The runtime must always allow `INSUFFICIENT_EVIDENCE` and `BUDGET_EXHAUSTED` as legitimate outcomes.
