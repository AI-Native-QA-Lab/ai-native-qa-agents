# Agent Runtime Specification

## 1. Purpose

`Agent Runtime` is the execution layer that turns a QA task into a controlled, evidence-driven agent loop.

The project must distinguish:

```text
Agent Runtime → HOW the QA agent works
Model Runtime → WHICH model fulfills an AI reasoning task
```

The core loop is:

```text
Understand
   ↓
Plan
   ↓
Act
   ↓
Observe
   ↓
Evaluate
   ↓
Need More Evidence?
 ├── Yes → Re-plan
 └── No
       ↓
     Verify
       ↓
   Quality Gate
       ↓
     Decide
       ↓
      Stop
```

The loop is controlled by deterministic runtime policy. It is not an unlimited LLM/tool-call loop.

## 2. Core Invariant

```text
Reasoning proposes.
Runtime authorizes.
Tools execute.
Observations become evidence.
Verification supports decisions.
```

## 3. Agent State

```python
class AgentState(BaseModel):
    task_id: str
    goal: str
    status: str
    iteration: int = 0

    plan: list["PlannedAction"] = []
    completed_actions: list["ActionRecord"] = []
    pending_actions: list["PlannedAction"] = []

    observations: list["Observation"] = []
    evidence_ids: list[str] = []
    finding_ids: list[str] = []

    open_questions: list[str] = []
    confidence: float | None = None

    budget: "ExecutionBudget"
    termination_reason: str | None = None
```

State must be serializable so the system can later support replay, debugging, evals, audit and resume.

## 4. Observation

Tool results are not injected directly into prompts as unstructured text.

```text
Tool Result
   ↓
Observation
   ↓
Evidence Builder
   ↓
Evidence
```

Example:

```python
class Observation(BaseModel):
    id: str
    action_id: str
    source: str
    summary: str
    structured_data: dict = {}
    evidence_ids: list[str] = []
```

## 5. Evaluate vs Verify

`Evaluate` asks:

> What does the current observation tell us?

`Verify` asks:

> Is the collected evidence sufficient to support the claim or decision?

These are separate stages.

## 6. Runtime Components

```text
qa_agent_runtime/
├── loop.py
├── state.py
├── planner.py
├── executor.py
├── observer.py
├── evaluator.py
├── verifier.py
├── termination.py
├── budget.py
├── trace.py
└── policies/
```

Responsibilities:

- Planner — proposes next actions.
- Executor — authorizes and invokes tools/workflows.
- Observer — normalizes results.
- Evaluator — updates understanding and open questions.
- Verifier — validates claims against evidence.
- Termination Policy — decides whether the loop may continue.
- Budget — limits iterations, tools, model calls, cost and time.
- Trace — records loop history.

## 7. Execution Budget

Every loop must have explicit bounds.

```yaml
budget:
  max_iterations: 8
  max_tool_calls: 30
  max_model_calls: 5
  max_cost_usd: 0.50
  timeout_seconds: 300
```

The exact defaults are configurable.

Budget exhaustion is a valid termination state and must not be hidden.

## 8. Termination Policy

Supported stop reasons include:

```text
EVIDENCE_SUFFICIENT
GOAL_COMPLETED
NO_VALID_NEXT_ACTION
GATE_REACHED
UNSUPPORTED_TASK
HUMAN_APPROVAL_REQUIRED
BUDGET_EXHAUSTED
TIMEOUT
INSUFFICIENT_EVIDENCE
ERROR
```

An agent is allowed to stop with `INSUFFICIENT_EVIDENCE`.

## 9. Minimal v0.1 Loop

v0.1 must not introduce an autonomous general planner.

Use a deterministic review loop:

```text
Inspect Repository
   ↓
Inspect Diff
   ↓
Discover Related Tests
   ↓
Run Rules
   ↓
Need Semantic Review?
 ├── No
 └── Yes → Model Runtime
   ↓
Collect Evidence
   ↓
Verify Findings
   ↓
Apply Gate
   ↓
Stop
```

Re-planning is constrained to predefined review actions.

## 10. Quality Reviewer Loop

Example:

```text
Goal: review changed tests

Iteration 1
PLAN      inspect diff and project type
ACT       git diff + detector
OBSERVE   changed Python code + pytest test
EVALUATE  need changed symbols

Iteration 2
PLAN      parse changed symbols and related tests
ACT       AST + relevance mapping
OBSERVE   refund() changed; one related test
EVALUATE  inspect assertions

Iteration 3
PLAN      run deterministic test-quality rules
ACT       rule engine
OBSERVE   status-only assertion
EVALUATE  possible weak business oracle

Iteration 4
PLAN      semantic oracle review
ACT       Model Runtime
OBSERVE   refund state not verified
EVALUATE  evidence sufficient

VERIFY
GATE
DECIDE
STOP
```

## 11. Agent-specific Loop Policies

All agents share the runtime primitives but not necessarily the same loop.

### Quality Analyst

```text
Requirement
→ Identify ambiguity
→ Gather context
→ Evaluate testability
→ Re-plan if context missing
→ Risk analysis
→ Verify
→ Decision
```

### Test Engineer

```text
Test Intent
→ Generate
→ Parse
→ Compile
→ Execute
→ Review
→ Failure?
   ├── Yes → Analyze → Repair → Retry
   └── No  → Verify → Accept
```

This becomes the `Repair Loop` in v0.3.

### Failure Investigator

```text
Failure
→ Hypothesis
→ Collect evidence
→ Challenge hypothesis
→ Reject / Refine
→ Collect more evidence
→ Verify
→ Conclusion or UNKNOWN
```

This becomes the `Hypothesis Loop` in v0.5.

### Release Guardian

Prefer a constrained aggregation loop:

```text
Collect evidence
→ Check completeness
→ Request missing evidence when allowed
→ Apply policy
→ Recommendation
```

## 12. Agent Runtime and Model Runtime

```text
Agent Runtime
   │
   ├── deterministic planning
   ├── state
   ├── tools
   ├── evidence
   ├── verification
   ├── gates
   └── termination
   │
   └── AI reasoning request
            ↓
       Model Runtime
            ↓
   capability / routing / policy
            ↓
      provider adapter
```

Model Runtime must not own the agent loop.

## 13. Permissions

Every action is checked before execution:

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
WRITE + RELEASE → human approval
```

## 14. Loop Trace

Every run should record:

```yaml
iteration: 3
state: evaluating
planned_action: review_assertion
tool: static_rule_engine
observations:
  - OBS-008
evidence:
  - EV-012
findings:
  - F-003
next_action: semantic_oracle_review
```

Loop traces support:

- debugging
- replay
- audit
- evals
- cost analysis
- agent behavior comparison

## 15. Eval Requirements

Agent evals must evaluate loop behavior, not only final prose.

Metrics include:

```text
Goal Completion
Tool Selection Accuracy
Unnecessary Tool Calls
Evidence Sufficiency
Re-plan Accuracy
Termination Accuracy
Loop Length
Model Calls
Cost
Latency
Final Decision Accuracy
```

Adversarial evals must include loops that should stop rather than continue.

## 16. Security

The loop controller must prevent:

- arbitrary tool execution proposed by repository text
- recursive uncontrolled model/tool calls
- bypassing permission gates
- hidden budget expansion
- direct credential access
- silent write/release actions

Repository content is data, not runtime instruction.

## 17. Version Evolution

### v0.1 — Minimal Controlled Loop

```text
AgentState
Observation
LoopTrace
ExecutionBudget
Deterministic Planner
Evidence-aware Verifier
Termination Policy
```

### v0.2 — Stateful Re-plan

```text
Open Questions
Context Expansion
Constrained Re-plan
Requirement Context Gathering
```

### v0.3 — Repair Loop

```text
Generate
Compile
Execute
Analyze
Repair
Retry
Review
```

### v0.5 — Hypothesis Loop

```text
Hypothesis
Evidence
Challenge
Refine
Verify
```

### v0.7 — Policy-aware Decision Loop

```text
Evidence Completeness
Release Policy
Human Approval
```

### v1.0 — Stable Generic Agent Runtime

```python
class QAAgent(Protocol):
    def understand(...): ...
    def plan(...): ...
    def act(...): ...
    def observe(...): ...
    def evaluate(...): ...
    def verify(...): ...
    def decide(...): ...
```

The generic interface is stabilized only after concrete loops have proven the abstraction.

## 18. Design Rule

The project must remain:

```text
Controlled Agent Loop
+
Deterministic Engineering Tools
+
Optional Model Reasoning
+
Evidence
+
Verification
+
Explicit Termination
```

not:

```text
LLM → Tool → LLM → Tool → ... forever
```
