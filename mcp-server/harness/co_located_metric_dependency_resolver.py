"""Resolves authored compact-metric dependencies within one workflow scope."""

from harness.co_located_metric_dependency_resolving import (
    CoLocatedMetricDependencyResolving,
)
from harness.co_located_metric_identity import CoLocatedMetricIdentity

"""
solid-name: CoLocatedMetricDependencyResolver
solid-category: service
solid-spec: [SPEC-058]
solid-description: Selects the qualified compact metric identity owned by a step's root or included-workflow scope.
"""


class CoLocatedMetricDependencyResolver(CoLocatedMetricDependencyResolving):
    def resolve(
        self,
        dependency: str,
        memberships: set[str],
        identities: list[CoLocatedMetricIdentity],
    ) -> str:
        identity = next(
            (
                candidate
                for candidate in identities
                if candidate.authored_id == dependency
                and (
                    candidate.owning_alias in memberships
                    if candidate.owning_alias is not None
                    else not memberships
                )
            ),
            None,
        )
        return identity.runtime_id if identity is not None else dependency
