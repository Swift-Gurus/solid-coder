"""Defines qualification of an included workflow identifier."""

from typing import Protocol


"""
solid-name: IncludedWorkflowIdentifierQualifying
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for qualifying a child workflow identifier for one runtime instance.
"""
class IncludedWorkflowIdentifierQualifying(Protocol):
    def qualify(
        self,
        identifier: str,
        alias: str,
        instance_prefix: str,
    ) -> str: ...
