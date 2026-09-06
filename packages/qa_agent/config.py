"""Small stdlib configuration loader for JSON and the v0.1 YAML subset."""

from dataclasses import dataclass, field
import json
from pathlib import Path


@dataclass(frozen=True)
class AgentConfig:
    fail_on: tuple[str, ...] = ("critical",)
    rule_severity: dict[str, str] = field(default_factory=dict)
    suppressed_rules: dict[str, tuple[str, ...]] = field(default_factory=dict)
    max_actions: int = 6
    max_files: int = 500
    max_file_bytes: int = 1_000_000
    max_tool_calls: int = 32
    max_model_calls: int = 0
    timeout_seconds: int = 60


def _parse_scalar(value: str):
    value = value.strip()
    if not value: return {}
    if value in {"true", "false"}: return value == "true"
    try: return int(value)
    except ValueError: pass
    return value.strip("'\"")


def _yaml_subset(text: str) -> dict:
    result, section, subsection, list_key, current_item = {}, None, None, None, None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip(): continue
        indent = len(line) - len(line.lstrip())
        content = line.strip()
        if indent == 0 and content.endswith(":"):
            section = content[:-1]; subsection = list_key = current_item = None; result[section] = [] if section == "ignore" else {}
        elif section == "ignore":
            if indent == 2 and content.startswith("-"):
                current_item = {}; result[section].append(current_item)
                if ":" in content[1:]:
                    key, value = content[1:].split(":", 1); current_item[key.strip()] = _parse_scalar(value)
            elif current_item is not None and indent == 4 and content.endswith(":"):
                key = content[:-1]; current_item[key] = [] if key == "paths" else {}
                list_key = key if key == "paths" else None
            elif current_item is not None and indent == 6 and content.startswith("-") and list_key:
                current_item[list_key].append(_parse_scalar(content[1:]))
        elif indent == 0 and ":" in content:
            key, value = content.split(":", 1); result[key.strip()] = _parse_scalar(value)
        elif section and indent == 2 and content.endswith(":"):
            key = content[:-1]; subsection = key; list_key = key if key == "fail_on" else None; result[section][key] = [] if list_key else {}
        elif section and indent == 2 and ":" in content:
            key, value = content.split(":", 1); subsection = key.strip(); list_key = None; result[section][subsection] = _parse_scalar(value)
        elif section and indent == 4 and content.startswith("-"):
            if list_key: result[section][list_key].append(_parse_scalar(content[1:]))
        elif section and subsection and indent == 4 and ":" in content:
            key, value = content.split(":", 1); result[section][subsection][key.strip()] = _parse_scalar(value)
    return result


def load_config(path: Path | None = None) -> AgentConfig:
    if path is None:
        path = next((candidate for candidate in (Path(".qa-agent.yaml"), Path(".qa-agent.yml"), Path(".qa-agent.json")) if candidate.exists()), None)
    if path is None or not path.exists(): return AgentConfig()
    data = json.loads(path.read_text()) if path.suffix == ".json" else _yaml_subset(path.read_text())
    gates = data.get("gates", {})
    rules = data.get("rules", {})
    ignored = data.get("ignore", [])
    suppressed = {item.get("rule", ""): tuple(item.get("paths", ())) for item in ignored if item.get("rule")}
    return AgentConfig(tuple(gates.get("fail_on", ("critical",))), {key: value.get("severity", value) if isinstance(value, dict) else value for key, value in rules.items()}, suppressed, **{key: data[key] for key in ("max_actions", "max_files", "max_file_bytes", "max_tool_calls", "max_model_calls", "timeout_seconds") if key in data})
