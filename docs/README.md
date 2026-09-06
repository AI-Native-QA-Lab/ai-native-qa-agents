# Engineering Documentation

[English project overview](../README.md) · [中文项目入口](../README.zh-CN.md)

Every release has an independent engineering pack. The packs define the planned scope; they do not by themselves indicate that the release has been implemented.

| Version | Agent-loop milestone | Engineering pack |
| --- | --- | --- |
| v0.1 | Minimal controlled review | [Open](v0.1-engineering/README.md) |
| v0.2 | Stateful re-plan | [Open](v0.2-engineering/README.md) |
| v0.3 | Generate, execute, repair, retry | [Open](v0.3-engineering/README.md) |
| v0.4 | Mutation and effectiveness | [Open](v0.4-engineering/README.md) |
| v0.5 | Hypothesis and challenge | [Open](v0.5-engineering/README.md) |
| v0.6 | PR and baseline aggregation | [Open](v0.6-engineering/README.md) |
| v0.7 | Policy-aware release decision | [Open](v0.7-engineering/README.md) |
| v0.8 | Production feedback | [Open](v0.8-engineering/README.md) |
| v0.9 | Verified knowledge persistence | [Open](v0.9-engineering/README.md) |
| v1.0 | Stable generic runtime | [Open](v1.0-engineering/README.md) |

Each pack provides `README`, `ARCHITECTURE`, `IMPLEMENTATION_PLAN`, `DOMAIN_MODEL`, `AGENT_LOOP`, `ADAPTER_SPEC`, `EVIDENCE_AND_GATES`, `MODEL_RUNTIME`, `EVAL_SPEC`, `SECURITY`, and `ISSUE_BACKLOG`.

Cross-version contracts live at the repository root: [Agent Runtime](../AGENT_RUNTIME_SPEC.md), [Model Runtime](../MODEL_RUNTIME_SPEC.md), and [version roadmap](../ROADMAP_AND_VERSION_DESIGN.md).
