# v0.1 Domain Model

Core models: `ReviewRequest`, `ReviewResult`, `Evidence`, `Finding`, `TestEntity`, `CodeChange`, `QualityDecision`, `GateResult`, `AgentState`, `Observation`, `LoopTrace`, `ExecutionBudget`.

Runtime state is transient. Evidence and Findings are durable review artifacts. Findings reference Evidence IDs. Model confidence never substitutes for verification status.
