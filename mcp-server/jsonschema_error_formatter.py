"""
solid-description: Formats schema validation errors as human-readable messages.
solid-category: utility
"""

from typing import Any, List


def format_schema_errors(schema: dict, data: Any, limit: int = 10) -> List[str]:
    """Validate data against schema, returning up to `limit` formatted "path: message" lines."""
    import jsonschema

    validator = jsonschema.Draft7Validator(schema)
    raw = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    return [
        f"  - {'.'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
        for e in raw[:limit]
    ]
