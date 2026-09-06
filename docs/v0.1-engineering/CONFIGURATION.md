# v0.1 Configuration

The CLI reads `.qa-agent.yaml`, `.qa-agent.yml`, or `.qa-agent.json` from the repository root. An explicit `--config` path takes precedence.

```yaml
gates:
  fail_on:
    - critical
rules:
  TQ012:
    severity: low
ignore:
  - rule: TQ012
    paths:
      - legacy/**
max_actions: 6
max_files: 500
max_file_bytes: 1000000
max_tool_calls: 32
max_model_calls: 0
timeout_seconds: 60
```

The deterministic reviewer never executes repository commands. `max_model_calls: 0` keeps semantic review disabled; an explicitly injected provider and a positive model budget are required to enable it.
