"""Defines conversion of serializable values into YAML text."""

from __future__ import annotations

from typing import Protocol


"""
solid-name: YamlDumping
solid-category: abstraction
solid-spec: [SPEC-031]
solid-description: Contract for converting serializable values into YAML text.
"""
class YamlDumping(Protocol):
    def dump(self, value: object) -> str: ...
