"""Defines readiness checks for a dynamic workflow include group."""

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup
from harness.models import RunState


"""
solid-name: IncludeGroupReadinessChecking
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for checking whether an included workflow may materialize.
"""
class IncludeGroupReadinessChecking(Protocol):
    def is_ready(
        self,
        group: IncludeAliasGroup,
        run_state: RunState,
    ) -> bool: ...
