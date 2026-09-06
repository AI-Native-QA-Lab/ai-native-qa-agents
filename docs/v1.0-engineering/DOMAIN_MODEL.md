# v1.0 Domain Model — AI Native QA System

## Models
Stable QAAgent, AgentTask, AgentState, AgentResult, SkillManifest, ToolContract, PermissionPolicy, RuntimeEvent

## Cross-version invariants
- Version schemas.
- Findings and decisions reference evidence.
- AgentState is runtime state, not quality truth.
- Confidence is not verification.
- Durable knowledge must retain provenance.
