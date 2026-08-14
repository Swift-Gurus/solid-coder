"""Defines minimal example-value resolution for JSON schemas."""

from typing import Protocol


"""
solid-name: SchemaMinimalValueResolving
solid-category: abstraction
solid-description: Contract for deriving a minimal representative value from one JSON Schema value declaration.
"""
class SchemaMinimalValueResolving(Protocol):
    def resolve(self, schema: dict): ...
