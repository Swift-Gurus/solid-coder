"""Rebases sibling dependencies onto expanded co-located metric identities."""

from harness.co_located_metric_dependency_rebasing import (
    CoLocatedMetricDependencyRebasing,
)
from harness.co_located_metric_dependency_resolving import (
    CoLocatedMetricDependencyResolving,
)
from harness.co_located_metric_identity import CoLocatedMetricIdentity
from harness.include_alias_group import IncludeAliasGroup
from harness.include_group_membership_resolving import (
    IncludeGroupMembershipResolving,
)
from harness.step_declaration import StepDeclaration
from harness.step_dependencies_replacing import StepDependenciesReplacing


"""
solid-name: CoLocatedMetricDependencyRebaser
solid-category: service
solid-spec: [SPEC-058]
solid-description: Coordinates workflow scope lookup and typed dependency replacement after compact metric expansion.
"""
class CoLocatedMetricDependencyRebaser(CoLocatedMetricDependencyRebasing):
    def __init__(
        self,
        membership_resolver: IncludeGroupMembershipResolving,
        dependency_resolver: CoLocatedMetricDependencyResolving,
        dependency_replacer: StepDependenciesReplacing,
    ) -> None:
        self._membership_resolver = membership_resolver
        self._dependency_resolver = dependency_resolver
        self._dependency_replacer = dependency_replacer

    def rebase(
        self,
        steps: list[StepDeclaration],
        identities: list[CoLocatedMetricIdentity],
        alias_groups: list[IncludeAliasGroup],
    ) -> list[StepDeclaration]:
        rebased: list[StepDeclaration] = []
        for step in steps:
            memberships = self._membership_resolver.resolve(
                step.id or "",
                alias_groups,
            )
            dependencies = [
                self._dependency_resolver.resolve(
                    dependency,
                    memberships,
                    identities,
                )
                for dependency in (step.depends_on or [])
            ]
            rebased.append(
                step
                if dependencies == (step.depends_on or [])
                else self._dependency_replacer.replace_dependencies(
                    step,
                    dependencies,
                )
            )
        return rebased
