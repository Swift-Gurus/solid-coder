#!/usr/bin/env python3
"""Validate review-input.json against output.schema.json.

Usage:
    python3 validate-output.py <review-input.json> <schema.json>

Exits 0 on success, 1 on validation failure with a clear error message.
"""
import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("Error: jsonschema not installed. Run: pip install jsonschema", file=sys.stderr)
    sys.exit(1)



# --- Public API ---


def validate_json(json_path: str, schema_path: str) -> dict:
    """Validate a JSON file against a JSON schema.

    Returns {valid: bool, error: str|None, path: str|None}.
    """
    jp = Path(json_path)
    sp = Path(schema_path)

    if not jp.exists():
        return {"valid": False, "error": f"{jp} not found", "path": None}
    if not sp.exists():
        return {"valid": False, "error": f"{sp} not found", "path": None}

    try:
        with open(jp) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return {"valid": False, "error": f"{jp} is not valid JSON: {e}", "path": None}

    with open(sp) as f:
        schema = json.load(f)

    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        error_path = " → ".join(str(p) for p in e.absolute_path) if e.absolute_path else "(root)"
        return {"valid": False, "error": e.message, "path": error_path}

    return {"valid": True, "error": None, "path": None}


# --- CLI entry point ---


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <json-file> <schema-file>", file=sys.stderr)
        sys.exit(1)

    result = validate_json(sys.argv[1], sys.argv[2])
    if not result["valid"]:
        loc = f" at {result['path']}" if result["path"] else ""
        print(f"Schema validation failed{loc}:\n  {result['error']}", file=sys.stderr)
        sys.exit(1)

    print("OK")


if __name__ == "__main__":
    main()
