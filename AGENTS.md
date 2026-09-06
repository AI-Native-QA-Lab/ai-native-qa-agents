# AI Native QA Agents Contributor Guide

## Purpose

This repository specifies and will implement evidence-driven QA agents. Preserve the boundary between the **Agent Runtime** (control flow, authorization, evidence, verification, and termination) and the **Model Runtime** (capability selection, routing, providers, fallbacks, and governance).

## Working rules

- Read the applicable version pack under `docs/v*-engineering/` before changing its scope or implementation plan.
- Keep deterministic collection and rule evaluation ahead of model reasoning.
- Every finding and decision needs traceable evidence and an explicit confidence or insufficiency state.
- Enforce bounded loops: execution budgets, timeouts, permissions, and a termination reason are required.
- Treat generated patches as untrusted. Do not auto-commit, auto-merge, or execute outside the documented sandbox policy.
- Keep implementation source in `packages/`, adapters in `adapters/`, rules in `rules/`, evaluation assets in `evals/`, and examples in `examples/`.
- Avoid modifying unrelated version packs. Cross-version changes must update the roadmap and affected links.

## Documentation

- English is the canonical language for root-level project documentation; maintain the linked Chinese entry when its meaning changes.
- Do not translate identifiers, commands, configuration keys, model names, or file paths.
- Version packs may contain source-language material from the approved engineering pack. Do not rewrite their technical scope without an explicit decision record.

## Validation

- Check Markdown links and Mermaid syntax after documentation changes.
- When implementation exists, run the smallest relevant test suite first, then the repository-wide checks required by the affected release pack.
- Do not claim a feature is implemented when only its design documents exist.
