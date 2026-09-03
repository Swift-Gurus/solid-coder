"""Defines validation of combined workflow-presentation groups."""

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup
from harness.step_declaration import StepDeclaration


"""
solid-name: CombinedPresentationGroupValidating
solid-category: abstraction
solid-spec: [SPEC-043]
solid-description: Contract for validating workflow groups that opt into combined model presentation.
"""
class CombinedPresentationGroupValidating(Protocol):
    def validate(
        self,
        steps: list[StepDeclaration],
        groups: list[IncludeAliasGroup],
    ) -> None: ...
