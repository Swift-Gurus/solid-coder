"""Defines child include-group transformation during nested resolution."""

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup
from harness.include_source import IncludeSource


"""
solid-name: NestedIncludeChildGroupTransforming
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035, SPEC-045]
solid-description: Contract for transforming nested child-group ownership and execution policy.
"""
class NestedIncludeChildGroupTransforming(Protocol):
    def transform(
        self,
        group: IncludeAliasGroup,
        source: IncludeSource,
        transparent_aliases: set[str],
    ) -> IncludeAliasGroup: ...
