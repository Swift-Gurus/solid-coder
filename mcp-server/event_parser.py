"""
solid-description: Validates and coerces raw data into typed structures.
solid-category: service
solid-tags: [hook, llm]
"""

from typing import Optional

from pydantic import TypeAdapter, ValidationError


class PydanticEventParser:
    """Boundary adapter: uses pydantic TypeAdapter to coerce raw output into typed events."""

    def parse_events(self, raw: object) -> list:
        try:
            return TypeAdapter(list).validate_python(raw)
        except ValidationError:
            return [raw]

    def parse_event_dict(self, event: object) -> Optional[dict]:
        try:
            return TypeAdapter(dict).validate_python(event)
        except ValidationError:
            return None
