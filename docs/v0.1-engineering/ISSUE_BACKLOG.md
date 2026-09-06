# v0.1 Issue Backlog

## Epic A — Core

### #1 Define Evidence schema
Acceptance:
- Pydantic model
- schema_version
- JSON serialization
- unit tests

### #2 Define Finding schema
Acceptance:
- severity
- confidence
- verification_status
- evidence references

### #3 Define ReviewResult and GateResult
Acceptance:
- stable JSON representation
- result versioning

### #4 Build CLI skeleton
Commands:
- review
- detect
- rules list
- config show

### #5 Implement config loader
Acceptance:
- `.qa-agent.yaml`
- defaults
- validation

## Epic B — Repository

### #6 Git repository detection
### #7 Base branch and diff reader
### #8 Changed file classifier
### #9 Python language detection
### #10 TypeScript language detection

## Epic C — Test Adapters

### #11 Pytest discovery
### #12 Pytest assertion extraction
### #13 Pytest skip/mock metadata
### #14 Playwright discovery
### #15 Playwright expect extraction
### #16 Playwright action / timeout metadata
### #17 Adapter contract test suite

## Epic D — Rule Engine

### #18 Rule interface and registry
### #19 TQ001-TQ005
### #20 TQ006-TQ010
### #21 TQ011-TQ015
### #22 Rule configuration
### #23 Rule suppression
### #24 Rule fixture suite

## Epic E — Change Relevance

### #25 Code entity extraction
### #26 Import reference mapping
### #27 Symbol matching
### #28 Related-test heuristic
### #29 Missing-related-test finding

## Epic F — AI Review

### #30 ModelProvider protocol
### #31 Anthropic provider
### #32 OpenAI provider
### #33 ContextBuilder
### #34 Semantic test review prompt
### #35 Structured semantic result
### #36 AI disabled mode
### #37 AI finding evidence policy

## Epic G — Gate & Reports

### #38 Quality Gate engine
### #39 Human report
### #40 JSON report
### #41 SARIF report
### #42 Exit code policy

## Epic H — Eval

### #43 Eval runner
### #44 Python golden cases
### #45 Playwright golden cases
### #46 Adversarial cases
### #47 Metrics report
### #48 CI regression check

## Epic I — Security

### #49 Secret file exclusion
### #50 Secret redaction
### #51 Prompt injection handling
### #52 Context token limits
### #53 Fork PR AI safety

## Epic J — GitHub

### #54 GitHub Action wrapper
### #55 Job summary
### #56 SARIF upload example
### #57 Optional PR summary comment
### #58 Example repository

## Epic K — Release

### #59 Architecture documentation
### #60 Rule documentation
### #61 Adapter author guide
### #62 Configuration guide
### #63 v0.1 smoke test
### #64 v0.1.0 release checklist

Status: implemented locally; remote tag/publish remains a release operation.

---

## Epic L — Agent Runtime

### #65 Define AgentState
Acceptance:
- serializable state
- iteration
- plan/actions
- observations/evidence
- budget
- termination reason

### #66 Define Observation schema
### #67 Define LoopTrace schema
### #68 Implement ExecutionBudget
### #69 Implement TerminationPolicy
### #70 Implement deterministic ReviewPlanner
### #71 Implement ActionExecutor
### #72 Implement Observer / Evidence conversion
### #73 Implement Evaluator
### #74 Implement EvidenceVerifier
### #75 Add loop budget tests
### #76 Add termination eval cases
### #77 Expose loop metadata in JSON report
### #78 Add loop trace debug output
