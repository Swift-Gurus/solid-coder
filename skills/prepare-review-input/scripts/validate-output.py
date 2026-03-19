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


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <json-file> <schema-file>", file=sys.stderr)
        sys.exit(1)

    json_path = Path(sys.argv[1])
    schema_path = Path(sys.argv[2])

    if not json_path.exists():
        print(f"Error: {json_path} not found", file=sys.stderr)
        sys.exit(1)
    if not schema_path.exists():
        print(f"Error: {schema_path} not found", file=sys.stderr)
        sys.exit(1)

    try:
        with open(json_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: {json_path} is not valid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    with open(schema_path) as f:
        schema = json.load(f)

    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        # Build a readable path to the failing field
        path = " → ".join(str(p) for p in e.absolute_path) if e.absolute_path else "(root)"
        print(f"Schema validation failed at {path}:\n  {e.message}", file=sys.stderr)
        sys.exit(1)

    print("OK")


if __name__ == "__main__":
    main()
