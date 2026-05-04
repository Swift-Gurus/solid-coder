#!/usr/bin/env python3
"""PreToolUse hook — validate pipeline JSON outputs against their schemas
BEFORE Write commits them.

Fires on Write of known pipeline JSON outputs (arch.json, validation.json,
implementation-plan.json, review-input.json, *.output.json, *.plan.json,
principle review-output.json / fix.json). Reads the proposed content from
tool_input, validates against the registered schema, and emits a
permissionDecision=deny to block the write when the JSON does not conform.

Failures unrelated to schema mismatch (missing schema, missing library,
malformed hook input) fail open — never block on infrastructure problems.
"""

import json
import os
import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", Path(__file__).resolve().parents[1]))

FILENAME_TO_SCHEMA = {
    "arch.json":                 "skills/plan/arch.schema.json",
    "validation.json":           "skills/validate-plan/validation.schema.json",
    "review-input.json":         "skills/prepare-review-input/output.schema.json",
    "implementation-plan.json":  "skills/synthesize-implementation/implementation-plan.schema.json",
}


def find_schema(file_path: Path):
    name = file_path.name

    if name in FILENAME_TO_SCHEMA:
        p = PLUGIN_ROOT / FILENAME_TO_SCHEMA[name]
        return p if p.exists() else None

    if name.endswith(".output.json"):
        p = PLUGIN_ROOT / "skills/validate-findings/file-output.schema.json"
        return p if p.exists() else None

    if name.endswith(".plan.json"):
        p = PLUGIN_ROOT / "skills/synthesize-fixes/plan.schema.json"
        return p if p.exists() else None

    # Principle outputs: /rules/{PRINCIPLE}/review-output.json or /rules/{PRINCIPLE}/fix.json
    m = re.search(r"[/\\]rules[/\\]([^/\\]+)[/\\](review-output|fix)\.json$", str(file_path))
    if m:
        principle, kind_raw = m.group(1), m.group(2)
        kind = "review" if kind_raw == "review-output" else "fix"
        for candidate in PLUGIN_ROOT.rglob("output.schema.json"):
            parts = candidate.parts
            if len(parts) >= 3 and parts[-2] == kind and parts[-3] == principle:
                return candidate

    return None


def collect_errors(content: str, schema_path: Path):
    """Return one of:
      - None  → infrastructure problem (skip validation, fail open)
      - [str] → list of error lines (empty list = valid)
    """
    try:
        import jsonschema
    except ImportError:
        return None

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        return [f"  - <root>: invalid JSON — {e.msg} (line {e.lineno}, col {e.colno})"]

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    validator = jsonschema.Draft7Validator(schema)
    raw = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    if not raw:
        return []
    return [
        f"  - {'.'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
        for e in raw[:10]
    ]


def _allow():
    sys.exit(0)


def _block(reason: str):
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    sys.stdout.write(json.dumps(payload))
    sys.stdout.flush()
    sys.exit(0)


def main():
    try:
        raw = sys.stdin.read()
        event = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        _allow()

    if event.get("tool_name") != "Write":
        _allow()

    tool_input = event.get("tool_input") or {}
    file_path_str = tool_input.get("file_path") or ""
    content = tool_input.get("content") or ""

    if not file_path_str or not file_path_str.endswith(".json"):
        _allow()

    file_path = Path(file_path_str)
    schema_path = find_schema(file_path)
    if schema_path is None:
        _allow()

    errors = collect_errors(content, schema_path)
    if errors is None or len(errors) == 0:
        _allow()

    lines = [
        f"Schema validation failed for {file_path.name} ({schema_path.name}) — {len(errors)} error(s):"
    ]
    lines.extend(errors)
    lines.append("")
    lines.append("Fix the JSON to match the schema before retrying the write.")
    _block("\n".join(lines))


if __name__ == "__main__":
    main()
