# v0.4 Test Effectiveness eval

`cases.json` is the fixed label manifest for the offline-first v0.4 vertical
slice. The runner uses the read-only reference repository and creates only
temporary context/report inputs. It covers deterministic mapping, score and
signal behavior, process completeness, budget/permission termination, strict
report validation, adversarial prompt-shaped data, and unavailable backends.

Run it with:

```bash
PYTHONPATH=packages python3 -m qa_agent.cli eval --version v0.4
```

The result is a JSON object with `cases` and `failures`; an empty failure list
is required for the local eval gate.
