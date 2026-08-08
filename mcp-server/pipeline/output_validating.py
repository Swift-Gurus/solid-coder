"""Defines validation of structured pipeline output."""

from typing import Protocol


"""
solid-name: OutputValidating
solid-category: abstraction
solid-description: Contract for validating structured output against a schema.
"""
class OutputValidating(Protocol):
    def validate_json(self, json_path: str, schema_path: str) -> dict: ...
