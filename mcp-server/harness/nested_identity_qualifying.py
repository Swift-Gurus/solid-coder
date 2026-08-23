"""Defines qualification of one nested dependency identity."""

from typing import Protocol


"""
solid-name: NestedIdentityQualifying
solid-category: abstraction
solid-spec: [SPEC-035, SPEC-037]
solid-description: Contract for prefixing a child-local identity while preserving references outside the nested workflow.
"""
class NestedIdentityQualifying(Protocol):
    def qualify(
        self,
        alias: str,
        identity: str,
        local_dependency_ids: set[str],
    ) -> str: ...
