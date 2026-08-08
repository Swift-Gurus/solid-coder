"""Defines detection of circular workflow include traversals."""

from __future__ import annotations

from typing import Protocol


"""
solid-name: IncludeCycleGuarding
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for rejecting a repeated workflow source in an active include traversal.
"""
class IncludeCycleGuarding(Protocol):

    def check(
        self,
        identity: str | None,
        label: str | None,
        ancestor_identities: list[str],
        ancestor_labels: list[str],
    ) -> None:
        ...
