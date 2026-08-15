"""Defines workflow condition serialization."""

from __future__ import annotations

from typing import Protocol

from harness.condition_declaration import ConditionDeclaration


"""
solid-name: ConditionSerializing
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for serializing a typed condition for durable output.
"""
class ConditionSerializing(Protocol):
    def serialize(
        self,
        condition: ConditionDeclaration,
    ) -> dict[str, object]: ...
