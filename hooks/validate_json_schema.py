#!/usr/bin/env python3
"""PostToolUse hook — validate written JSON files against their schemas.

Fires after Write or Edit. If the file is a known pipeline JSON output,
validates it against its registered schema and prints errors so the agent
can fix the file immediately.

Silent on success (exit 0, no output). On validation failure: prints errors
to stdout and exits 1 so the agent sees them.
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


def collect_errors(file_path: Path, schema_path: Path):
    try:
        import jsonschema
    except ImportError:
        return None  # graceful degradation — schema validation skipped

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]
    except OSError as e:
        return [f"Cannot read file: {e}"]

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None  # unreadable schema — skip

    validator = jsonschema.Draft7Validator(schema)
    raw = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    if not raw:
        return []
    return [
        f"  - {'.'.join(str(p) for p in e.absolute_path) or '(root)'}: {e.message}"
        for e in raw[:10]
    ]


def main():
    try:
        raw = sys.stdin.read()
        event = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_name = event.get("tool_name")
    print(f"[schema-hook] invoked tool_name={tool_name!r} keys={list(event.keys())}", file=sys.stderr)

    if tool_name not in ("Write", "Edit"):
        sys.exit(0)

    file_path_str = event.get("tool_input", {}).get("file_path", "")
    print(f"[schema-hook] file_path={file_path_str!r}", file=sys.stderr)
    if not file_path_str or not file_path_str.endswith(".json"):
        sys.exit(0)

    file_path = Path(file_path_str)
    if not file_path.exists():
        sys.exit(0)

    schema_path = find_schema(file_path)
    if schema_path is None:
        sys.exit(0)

    errors = collect_errors(file_path, schema_path)
    if errors is None or len(errors) == 0:
        sys.exit(0)

    lines = [f"Schema validation failed for {file_path.name} ({schema_path.name}):"]
    lines.extend(errors)
    lines.append("Fix the JSON and re-write the file.")
    message = "\n".join(lines)

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "userFacingError": message,
        }
    }))
    sys.exit(1)


if __name__ == "__main__":
    main()
