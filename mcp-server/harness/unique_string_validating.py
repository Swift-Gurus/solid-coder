"""Defines reusable validation of string identity uniqueness."""

from typing import Protocol


"""
solid-name: UniqueStringValidating
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-039]
solid-description: Contract for rejecting repeated string identities with a caller-provided identity name.
"""
class UniqueStringValidating(Protocol):

    def validate(self, values: list[str], identity_name: str) -> None:
        ...
