#!/usr/bin/env python3
"""Validate arch.json produced by /plan skill.

Runs two layers of checks:
  1. JSON schema validation against arch.schema.json (structural)
  2. Semantic cross-reference checks (relational integrity)

Usage:
    python3 validate-arch.py <arch.json> --schema <arch.schema.json>
    python3 validate-arch.py <arch.json>   # schema validation skipped

Exits 0 if all checks pass, 1 if errors found.
Warnings are printed but do not cause a non-zero exit.
"""

import sys
import json
import argparse

VALID_STACKS = {
    'swiftui', 'uikit', 'appkit',
    'combine', 'structured-concurrency', 'gcd',
    'tca', 'core-data', 'swift-data', 'grdb',
}


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {path}: {e}", file=sys.stderr)
        sys.exit(1)


def validate_schema(data, schema_path):
    """Validate against JSON schema. Returns list of error strings."""
    try:
        import jsonschema
    except ImportError:
        print("WARNING: jsonschema not installed — skipping schema validation", file=sys.stderr)
        return []

    schema = load_json(schema_path)
    errors = []
    validator = jsonschema.Draft7Validator(schema)
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        path = '.'.join(str(p) for p in error.path) or '(root)'
        errors.append(f"Schema [{path}]: {error.message}")
    return errors


def validate_semantic(data):
    """
    Checks relational integrity constraints the JSON schema cannot express.
    Returns (errors, warnings).
      errors   — will break downstream pipeline phases
      warnings — suspicious but not fatal
    """
    errors = []
    warnings = []

    components = data.get('components', [])
    wiring = data.get('wiring', [])

    # Build lookup sets
    all_interfaces = set()
    for c in components:
        for iface in c.get('interfaces', []):
            all_interfaces.add(iface)

    all_names = {c['name'] for c in components}

    # Every dependency must be exposed as an interface by some component
    for c in components:
        for dep in c.get('dependencies', []):
            if dep not in all_interfaces:
                errors.append(
                    f"'{c['name']}' depends on '{dep}' but no component exposes it as an interface"
                )

    # Every wiring.to must match an exposed interface
    for w in wiring:
        if w['to'] not in all_interfaces:
            errors.append(
                f"Wiring {w['from']} -> {w['to']}: '{w['to']}' is not exposed by any component"
            )

    # Every wiring.from must match a component name
    for w in wiring:
        if w['from'] not in all_names:
            errors.append(
                f"Wiring from '{w['from']}': no component with that name exists"
            )

    # Data models must have populated fields and empty interfaces/dependencies/produces
    for c in components:
        if c.get('category') == 'model':
            if not c.get('fields'):
                errors.append(f"'{c['name']}' is category 'model' but has empty fields[]")
            if c.get('interfaces'):
                errors.append(f"'{c['name']}' is category 'model' but has non-empty interfaces[]")
            if c.get('dependencies'):
                errors.append(f"'{c['name']}' is category 'model' but has non-empty dependencies[]")
            if c.get('produces'):
                errors.append(f"'{c['name']}' is category 'model' but has non-empty produces[]")

    # Warn on unknown stack values (vocabulary is fixed; unknown values won't activate rules)
    for c in components:
        for s in c.get('stack', []):
            if s not in VALID_STACKS:
                warnings.append(
                    f"'{c['name']}' uses unknown stack '{s}' — won't activate any principle rules"
                )

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description='Validate arch.json from /plan skill')
    parser.add_argument('arch_json', help='Path to arch.json')
    parser.add_argument('--schema', help='Path to arch.schema.json for structural validation')
    args = parser.parse_args()

    data = load_json(args.arch_json)

    all_errors = []

    if args.schema:
        all_errors.extend(validate_schema(data, args.schema))

    semantic_errors, warnings = validate_semantic(data)
    all_errors.extend(semantic_errors)

    for w in warnings:
        print(f"WARNING: {w}")

    if all_errors:
        print("ERRORS:")
        for e in all_errors:
            print(f"  - {e}")
        sys.exit(1)

    print("All validations passed")
    sys.exit(0)


if __name__ == '__main__':
    main()
