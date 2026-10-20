"""Identifies structural enclosing scopes independently of review policy."""

from enum import Enum


"""
solid-name: SourceScopeKind
solid-category: model
solid-spec: [SPEC-066]
solid-description: Distinguishes enclosing type, callable, and closure scopes in a parsed declaration inventory.
"""
class SourceScopeKind(str, Enum):
    FILE = "file"
    TYPE = "type"
    CALLABLE = "callable"
    CLOSURE = "closure"
