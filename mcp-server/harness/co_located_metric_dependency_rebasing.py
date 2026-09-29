"""Defines scoped dependency rebasing for expanded co-located metrics."""

from typing import Protocol

from harness.co_located_metric_identity import CoLocatedMetricIdentity
from harness.include_alias_group import IncludeAliasGroup
from harness.step_declaration import StepDeclaration


"""
solid-name: CoLocatedMetricDependencyRebasing
solid-category: abstraction
solid-spec: [SPEC-058]
solid-description: Contract for rebasing sibling dependencies onto qualified compact metric identities.
"""
class CoLocatedMetricDependencyRebasing(Protocol):
    def rebase(
        self,
        steps: list[StepDeclaration],
        identities: list[CoLocatedMetricIdentity],
        alias_groups: list[IncludeAliasGroup],
    ) -> list[StepDeclaration]: ...
