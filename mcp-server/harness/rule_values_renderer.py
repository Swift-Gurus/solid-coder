"""Renders typed rule-selection values for audit output."""

from pydantic import TypeAdapter


"""
solid-name: RuleValuesRenderer
solid-category: adapter
solid-spec: [SPEC-039]
solid-description: Produces stable audit text for rule-selection values.
"""
class RuleValuesRenderer:

    def __init__(self, adapter: TypeAdapter) -> None:
        self._adapter = adapter

    def render(self, values: list[object]) -> list[str]:
        return self._adapter.validate_python(values)
