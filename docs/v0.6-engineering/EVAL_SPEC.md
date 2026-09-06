# v0.6 Evaluation — CI / Pull Request Agent

## Focus
decision accuracy, new-vs-existing findings, annotation location, spam rate, fork behavior, cost

## Layers
1. Parser/rule/adapter
2. Skill/task
3. Agent loop
4. End-to-end workflow

## Metrics
Precision, recall, FPR, evidence alignment, decision accuracy, tool selection accuracy, unnecessary tool calls, re-plan accuracy, termination accuracy, iterations, model calls, cost and latency.

Do not rely only on LLM-as-judge.
