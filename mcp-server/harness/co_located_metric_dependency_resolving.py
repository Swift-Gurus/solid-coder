"""Defines scoped compact-metric dependency identity resolution."""

from typing import Protocol

from harness.co_located_metric_identity import CoLocatedMetricIdentity


"""
solid-name: CoLocatedMetricDependencyResolving
solid-category: abstraction
solid-spec: [SPEC-058]
solid-description: Contract for selecting a compact metric runtime identity within one workflow scope.
"""
class CoLocatedMetricDependencyResolving(Protocol):
    def resolve(
        self,
        dependency: str,
        memberships: set[str],
        identities: list[CoLocatedMetricIdentity],
    ) -> str: ...
